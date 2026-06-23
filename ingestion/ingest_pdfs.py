import asyncio
from pathlib import Path
from PIL import Image
import os
import sys
import re
import gc
import torch
import io 
import pymupdf
from dotenv import load_dotenv

from docling_core.types.doc import PictureItem
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer

from scripts.supabase import insert_pdf, insert_page
from scripts.qdrant import format_point, upload_points, get_qdrant_client, create_collection
from scripts.models import (
    openai_model,
    colqwen_model,
    document_converter,
    sparse_embedder
)

from scripts.config import settings



async def get_page_markdown(document, page_no, openai_model):
    serializer = MarkdownDocSerializer(doc=document)
    items = []
    image_tasks = []

    for item, level in document.iterate_items(traverse_pictures=True, page_no=page_no):
        if isinstance(item, PictureItem):

            page = document.pages[page_no]
            page_area  = page.size.width * page.size.height
            item_bbox = item.prov[0].bbox
            item_area = item_bbox.width * item_bbox.height
            if item_area / page_area > 0.2:
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

    return final_markdown


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
        pil_image = page.image.pil_image

        buffer = io.BytesIO()
        rgb_image = pil_image.convert("RGB")
        rgb_image.save(buffer, format="JPEG", quality=95)
        page_image = buffer.getvalue()

        page_id = await insert_page(filepath.name, markdown, page_no, page_image)

        multi = await colqwen_model.get_image_embedding(pil_image)
        
        embedding = {
            'page_id': page_id,
            'sparse': sparse,
            'multi': multi
        }

        vector = format_point(embedding)

        return markdown, vector


async def parse_pdf(filepath, filesize):
    filename = filepath.name
    await insert_pdf(filename, filepath, filesize)

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
                    print(f'\nProcessing {file.name}\n')
                    await parse_pdf(file)
                    print(f'\nDone\n')

        elif path.is_file() and path.suffix == '.pdf':
            print(f'\nProcessing {path.name}\n')
            await parse_pdf(path)
            print(f'\nDone\n')

    except Exception as e:
        print(f'An error occurred: \n{e}\n\n')
        raise


if __name__ == "__main__":

    asyncio.run(ingest_pdf(Path(r'C:\Users\UserAdmin\Documents\Multimodal-RAG\pdfs')))