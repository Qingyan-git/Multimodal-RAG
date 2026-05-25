import asyncio
from pathlib import Path
from PIL import Image
import os
import sys
import re
import pandas as pd
from dotenv import load_dotenv

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from scripts.supabase_setup import retrieve_pdf_path
from scripts.qdrant_setup import similarity_search
from scripts.models import OpenAIModel, ColQwenModel, SparseEmbedder




async def get_source_images(splade,coarse,embeddings,converter):

    answer_sources = similarity_search(splade,coarse,embeddings)
    page_sources = []
    for source in answer_sources:

        filename = source['filename']
        pages = source['pages']

        filepath = await retrieve_pdf_path(filename)
        document = converter.convert(filepath)

        for page_no in pages:
            page = document.pages[page_no]
            pil_image = page.image.pil_image
            item = {
                'image' : pil_image,
                'source' : f'Document {filename}, page {page_no}'
            }
            page_sources.append(item)

    return page_sources


async def answer_testset(filepath,converter,openai,colqwen,sparse):

    df = pd.read_csv(filepath)
    questions = df.iloc[:, 0]
    results = []
    for question in questions:

        splade_vector = await sparse.embed(question)
        coarse_vector, embeddings = await colqwen.embed_query(question)

        sources = await get_source_images(splade_vector,coarse_vector,embeddings,converter)

        answer = await openai.answer_question(question,sources)

        results.append({'Question' : question ,'Answer': answer})

    results_df = pd.DataFrame(results)

    answer_path = os.getenv('answer_path')
    results_df.to_csv(answer_path,index=False,encoding='utf-8-sig')


async def run_testset():

    try:

        testset_path = Path(os.getenv('testset_path'))

        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_page_images = True  # Critical for vision model downstream usage
        
        docling_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        openai_model = OpenAIModel()
        colqwen_model = ColQwenModel()
        sparse_embedder = SparseEmbedder()

        if testset_path.is_dir():
            for file in testset_path.iterdir():
                if file.suffix == '.csv':

                    print(f'Processing {file.name}\n\n')

                    await answer_testset(file,docling_converter,openai_model,colqwen_model,sparse_embedder)

                    print(f'Done\n\n')


    except Exception as e:
        print(f'Unable to answer testsets, error \n{e}\n\n')
        raise

