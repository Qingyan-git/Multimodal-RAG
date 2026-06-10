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

from docling_core.types.doc import PictureItem
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer

from test.test_supabase import insert_pdf, insert_page, get_connection
from test.test_qdrant import format_point, upload_points, get_qdrant_client
from test.test_models import (
    openai_model,
    colqwen_model,
    document_converter,
    sparse_embedder
)

from scripts.config import settings




def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
    return text


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

    # 2. Aspect Ratio Check
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


async def get_page_markdown(document, page_no, openai_model):
    serializer = MarkdownDocSerializer(doc=document)
    items = []
    image_tasks = []

    for item, level in document.iterate_items(traverse_pictures=True, page_no=page_no):
        if isinstance(item, PictureItem):
            page_item = document.pages[page_no]
            page_width = page_item.size.width
            page_height = page_item.size.height
            useable = is_useable_image(item, page_width, page_height)
            if useable:
                pil_image = item.get_image(doc=document)
                task = openai_model.get_image_description(pil_image)
                image_tasks.append(task)
                parsed_item = {'type': 'image_placeholder', 'index': len(image_tasks)-1}
            else:
                item_markdown = item.caption_text(doc=document)
                parsed_item = {'type': 'content', 'markdown': item_markdown}
        else:
            item_markdown = serializer.serialize(item=item).text
            parsed_item = {'type': 'content', 'markdown': item_markdown}

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


async def process_page_single(filepath, page_no, semaphore):
    async with semaphore:
        conversion_result = await asyncio.to_thread(
            document_converter.convert, 
            filepath, 
            page_range=(page_no, page_no)
        )
        document = conversion_result.document

        markdown = await get_page_markdown(document, page_no, openai_model)
        sparse = await sparse_embedder.embed(markdown)

        page = document.pages[page_no]
        page_image = page.image.pil_image

        multi = await colqwen_model.get_image_embedding(page_image)
        page_id = await insert_page(filepath.name, markdown, page_no)

        embedding = {
            'page_id': page_id,
            'sparse': sparse,
            'multi': multi
        }

        vector = format_point(embedding)

        if hasattr(document, "unload"):
            try:
                document.unload()
            except Exception:
                pass

        return markdown, vector


async def parse_pdf(filepath):
    filename = filepath.name
    await insert_pdf(filename, filepath)

    semaphore = asyncio.Semaphore(1)

    with pymupdf.open(filepath) as doc:
        pages = len(doc)
    
    tasks = [process_page_single(filepath, page_no, semaphore) for page_no in range(1, pages+1)]
    results = await asyncio.gather(*tasks)
    
    document_markdown, document_vectors = zip(*results)

    await upload_points(list(document_vectors))


async def ingest_pdf(path):
    try:
        if path.is_dir():
            for file in path.iterdir():
                if file.suffix == '.pdf':
                    print(f'\n Processing {file.name}\n')
                    await parse_pdf(file)
                    print(f'\nDone\n')

        elif path.is_file() and path.suffix == '.pdf':
            print(f'\n Processing {path.name}\n')
            await parse_pdf(path)
            print(f'\nDone\n')

    except Exception as e:
        print(f'An error occurred: \n{e}\n\n')
        raise


if __name__ == "__main__":

    asyncio.run(ingest_pdf(Path(r'C:\Users\UserAdmin\Documents\Multimodal-RAG\pdfs')))