import asyncio
from pathlib import Path
from PIL import Image
import os
import sys
import re
import gc
import torch
import pymupdf
from dotenv import load_dotenv

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import PictureItem, DoclingDocument
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer

from scripts.supabase_setup import insert_pdf, insert_page, get_connection
from scripts.qdrant_setup import format_point, upload_points, get_qdrant_client
from scripts.models import OpenAIModel, ColQwenModel, SparseEmbedder


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
    return text


def save_to_file(filename,content,filepath=os.getenv('markdown_path'),method='w'):

    save_path = Path(filepath) / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with save_path.open(method, encoding='utf-8') as f:
        f.write('\n')
        if isinstance(content, list):
            for item in content:
                f.write(f"{item}\n\n")
        else:
            f.write(content)
        f.write('\n')


def is_useable_image(img, page_w, page_h, min_dim=100, area_threshold=0.20):

    if not img.prov:
        return False
        
    prov = img.prov[0]
    bbox = prov.bbox
    
    # 1. Basic Dimension Check
    if bbox.height == 0 or bbox.width == 0:
        return False
    
    if bbox.height < min_dim or bbox.width < min_dim:
        return False

    # 2. Aspect Ratio Check (Your 0.2 to 5.0 range)
    ratio = bbox.height / bbox.width 
    if ratio > 5 or ratio < 0.2:
        return False
        
    # 3. Normalized Area Check
    image_area = bbox.width * bbox.height
    page_area = page_w * page_h
    normalized_area = image_area / page_area
    
    if normalized_area < area_threshold:
        return False
        
    return True


async def get_page_markdown(document,page_no,openai_model):

    serializer = MarkdownDocSerializer(doc=document)
    items = []
    image_tasks = []

    for item, level in document.iterate_items(traverse_pictures=True, page_no=page_no):
        if isinstance(item,PictureItem):
            page_item = document.pages[page_no]
            page_width = page_item.size.width
            page_height = page_item.size.height
            useable = is_useable_image(item,page_width,page_height)
            if useable :
                pil_image = item.get_image(doc=document)
                task = openai_model.get_image_description(pil_image)
                image_tasks.append(task)
                item_markdown = f'<-- PLACEHOLDER FOR IMAGE FOUND -->'
                parsed_item = {'type' : 'image_placeholder', 'index' : len(image_tasks)-1}
            else:
                item_markdown = item.caption_text(doc=document)
                parsed_item = {'type' : 'content', 'markdown' : item_markdown}
        else:
            item_markdown = serializer.serialize(item=item).text
            parsed_item = {'type' : 'content', 'markdown' : item_markdown}

        items.append(parsed_item)

    image_descriptions = await asyncio.gather(*image_tasks)

    page_markdown = []
    for item in items:
        if item['type'] == 'image_placeholder':
            page_markdown.append(f'\nIMAGE FOUND, DESCRIPTION : ' + image_descriptions[item['index']] + '\n')
        else:
            page_markdown.append(item['markdown'])

    final_markdown = f'\n\nPage {page_no} from document {document.name}\n\n' + ''.join(page_markdown)
    cleaned_text = clean_text(final_markdown)

    return cleaned_text


async def process_page_single(filepath,converter,page_no,openai_model,colqwen_model,sparse_embedder,semaphore):

    async with semaphore:

        conversion_result = await asyncio.to_thread(
            converter.convert, 
            filepath, 
            page_range=(page_no, page_no)
        )
        document = conversion_result.document

        markdown = await get_page_markdown(document,page_no,openai_model)
        sparse = await sparse_embedder.embed(markdown)
        page = document.pages[page_no]

        page_image = page.image.pil_image

        coarse, multi = await colqwen_model.get_image_embedding(page_image)
        page_id = await insert_page(filepath.name,markdown,page_no)

        embedding = {
            'page_id' : page_id,
            'sparse' : sparse,
            'coarse' : coarse,
            'multi' : multi
        }

        vector = format_point(embedding)

        # Explicitly call unload() on the document backends if the method exists
        if hasattr(document, "unload"):
            try:
                document.unload()
            except Exception:
                pass

        return markdown, vector


async def parse_pdf(filepath,converter,openai_model,colqwen_model,sparse_embedder):

    filename = filepath.name
    await insert_pdf(filename,filepath)

    semaphore = asyncio.Semaphore(1)

    document_markdown = []
    document_vectors = []
    with pymupdf.open(filepath) as doc:
        pages = len(doc)
    
    tasks = [process_page_single(filepath,converter,page_no,openai_model,colqwen_model,sparse_embedder,semaphore) for page_no in range(1,pages+1)]
    results = await asyncio.gather(*tasks)
    document_markdown, document_vectors = zip(*results)
    save_name = filepath.stem + '.md'
    save_to_file(save_name, list(document_markdown))
    await upload_points(list(document_vectors))


async def ingest_all_pdfs(folderpath):

    try:

        #folderpath = Path(os.getenv('pdfs_path'))

        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_picture_images = True
        pipeline_options.generate_page_images = True
        pipeline_options.images_scale = 2.0
        # pipeline_options.do_ocr = True
        # pipeline_options.do_table_structure = True
        # pipeline_options.do_code_enrichment = True
        # pipeline_options.do_formula_enrichment = True
        # accelerator_options = AcceleratorOptions(
        #     num_threads=8, 
        #     device="cuda" if torch.cuda.is_available() else "cpu"
        # )
        # pipeline_options.accelerator_options = accelerator_options
        document_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        openai_model = OpenAIModel()
        colqwen_model = ColQwenModel()
        sparse_embedder = SparseEmbedder()

        if folderpath.is_dir():
            for file in folderpath.iterdir():
                if file.suffix == '.pdf':

                    print(f'\n Processing {file.name}\n')
                    await parse_pdf(file,document_converter,openai_model,colqwen_model,sparse_embedder)
                    print(f'\nDone\n')

        elif folderpath.is_file() and folderpath.suffix=='.pdf':
            print(f'\n Processing {file.name}\n')
            await parse_pdf(file,document_converter,openai_model,colqwen_model,sparse_embedder)
            print(f'\nDone\n')

    except Exception as e:
        print(f'An error occured : \n{e}\n\n')
        raise



if __name__ == "__main__":

    asyncio.run(ingest_all_pdfs())