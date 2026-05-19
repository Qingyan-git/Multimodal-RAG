import io
import asyncio
from PIL import Image
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import PictureItem


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


async def get_document_markdown(filepath,converter):

    document = converter.convert(filepath).document
    markdown_text = []

    for page_no in document.pages.keys():

        page_markdown = []

        for item, level in document.iterate_items(traverse_pictures=True, page_no=page_no):

            if isinstance(item,PictureItem):
                page_width = page_item.size.width
                page_height = page_item.size.height
                is_useable_image(item)
                pil_image = item.image.pil_image

            else:
                temp_doc = DoclingDocument(name='temp')
                temp_doc.add_node_items([item])
                item_markdown = temp_doc.export_to_markdown().strip()
                page_markdown.append(item_markdown)


def parse_all_documents(folderpath):

    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True  # CRUCIAL: Tells Docling to pull out images
    pipeline_options.images_scale = 2.0             # Upscale to ~144 DPI for better LLM legibility

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    if folder_path.is_dir():
        for file in folder_path.iterdir():
            if file.suffix == '.pdf':

                get_document_markdown(file,converter)
