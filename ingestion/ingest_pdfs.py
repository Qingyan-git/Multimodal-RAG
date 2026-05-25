import asyncio
from pathlib import Path
from PIL import Image
import os
import sys
import re
from dotenv import load_dotenv

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
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
                item = {'type' : 'image_placeholder', 'index' : len(image_tasks)-1}
            else:
                item_markdown = item.caption_text(doc=document)
                item = {'type' : 'content', 'markdown' : item_markdown}
        else:
            item_markdown = serializer.serialize(item=item).text
            item = {'type' : 'content', 'markdown' : item_markdown}

        items.append(item)


    image_descriptions = await asyncio.gather(*image_tasks)

    page_markdown = []
    for item in items:
        if item['type'] == 'image_placeholder':
            page_markdown.append(image_descriptions[item['index']])
        else:
            page_markdown.append(item['markdown'])

    final_markdown = f'\n\nPage {page_no} from document {document.name}\n\n' + "".join(page_markdown)
    cleaned_text = clean_text(final_markdown)

    return cleaned_text


async def parse_pdf(filepath,document,openai_model,colqwen_model,sparse_embedder):

    filename = filepath.name
    await insert_pdf(filename,filepath)

    async def _process_page(page_no):

        markdown = await get_page_markdown(document,page_no,openai_model)

        sparse = await sparse_embedder.embed(markdown)
        await insert_page(filename,markdown,page_no)
        
        page = document.pages[page_no]
        pil_image = page.image.pil_image
        coarse, multi = await colqwen_model.get_image_embedding(pil_image)

        embedding = {
            'filename' : filename,
            'page_no' : page_no,
            'sparse' : sparse,
            'coarse' : coarse,
            'multi' : multi
        }

        vector = format_point(embedding)

        return markdown, vector

    tasks = [_process_page(page_no) for page_no in document.pages.keys()]
    results = await asyncio.gather(*tasks)
    document_markdown, document_vectors = zip(*results)
    save_name = filepath.stem + '.md'
    save_to_file(save_name, list(document_markdown))
    await upload_points(list(document_vectors))


async def ingest_all_pdfs():

    try:

        folderpath = Path(os.getenv('pdfs_path'))

        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_picture_images = True
        pipeline_options.generate_page_images = True
        pipeline_options.images_scale = 2.0
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.do_code_enrichment = True
        pipeline_options.do_formula_enrichment = True
        docling_converter = DocumentConverter(
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

                    print(f'Processing {file.name}\n\n')

                    document = docling_converter.convert(file).document
                    await parse_pdf(file,document,openai_model,colqwen_model,sparse_embedder)

                    print(f'Done\n\n')

    except Exception as e:
        print(f'An error occured : \n{e}\n\n')
        raise



if __name__ == "__main__":

    asyncio.run(ingest_all_pdfs())