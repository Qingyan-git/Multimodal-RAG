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

from scripts.supabase_setup import retrieve_pdf_path, retrieve_files
from scripts.qdrant_setup import similarity_search
from scripts.models import OpenAIModel, ColQwenModel, SparseEmbedder, Jina



def apply_rrf(results, k=60):

    """
    Need to adapt this code to use the other data structure of {page_id:{'text_score':text_score,'image_score':image_score}}
    """

    colqwen_sorted = sorted(
        results, 
        key=lambda x: x.get("image_score", 0), 
        reverse=True
    )
    
    jina_sorted = sorted(
        results, 
        key=lambda x: x.get("text_score", 0), 
        reverse=True
    )

    colqwen_rank_map = {doc["page_id"]: rank for rank, doc in enumerate(colqwen_sorted)}
    jina_rank_map = {doc["page_id"]: rank for rank, doc in enumerate(jina_sorted)}

    # dynamic selection (image)
    image_scores = [item["image_score"] for item in results]
    max_image_score = max(image_scores)
    image_cutoff= max_image_score * 0.8

    image_docs = [doc for doc in results if doc["image_score"] >= image_cutoff]

    # dynamic selection (text)
    TEXT_ABSOLUTE_THRESHOLD = 0.30

    text_docs = [doc for doc in results if doc["text_score"] >= TEXT_ABSOLUTE_THRESHOLD]

    
    rrf_scores = {}

    for doc in image_docs:
        page_id = doc["page_id"]
        rank = colqwen_rank_map[page_id]
        rrf_scores[page_id] = 1.0 / (k + (rank + 1))
        
    for doc in text_docs:
        page_id = doc["page_id"]
        rank = jina_rank_map[page_id]
        if page_id in rrf_scores:
            rrf_scores[page_id] += 1.0 / (k + (rank + 1))
        else:
            rrf_scores[page_id] = 1.0 / (k + (rank + 1))
            
    final_hybrid_results = []

    for doc in results:
        page_id = doc["page_id"]
        if page_id in rrf_scores:
            doc["rrf_score"] = rrf_scores[page_id]
            final_hybrid_results.append(doc)
        
    final_hybrid_results.sort(key=lambda x: x["rrf_score"], reverse=True)
    
    return final_hybrid_results


async def get_sources(splade,coarse,embeddings,doc_cache,cache_lock):
    similar_pages = await similarity_search(splade,coarse,embeddings)
    pages_with_markdown = await retrieve_markdowns(similar_pages)
    pages_with_scores = Jina().text_rerank(pages_with_markdown)
    for page_id in pages_with_scores:
        pages_with_scores[page_id].pop("markdown", None)

    #Now pages_with_scores looks like this : {page_id : {'image_score' : image_score, 'text_score' : text_score}}


async def get_source_images(splade,coarse,embeddings,converter,doc_cache,cache_lock):

    page_ids = await similarity_search(splade,coarse,embeddings)
    answer_sources = await retrieve_files(page_ids)
    page_sources = []
    for source in answer_sources:

        filename = source['name']
        page_no = source['page_no']

        filepath = await retrieve_pdf_path(filename)
        async with cache_lock:
            if filename not in doc_cache:
                # Running heavy blocking CPU code like converter.convert inside async 
                # can freeze the loop. The lock ensures only one task does it at a time.
                doc_cache[filename] = converter.convert(filepath)
        document = doc_cache[filename]
        page = document.pages[page_no-1]
        
        pil_image = page.image
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

    semaphore = asyncio.Semaphore(5)
    doc_cache = {}
    cache_lock = asyncio.Lock()

    async def answer_question(question):
        async with semaphore:

            splade_vector = await sparse.embed(question)
            coarse_vector, embeddings = await colqwen.embed_query(question)
            sources = await get_source_images(splade_vector,coarse_vector,embeddings,converter,doc_cache,cache_lock)
            answer = await openai.answer_question(question,sources)

            return {'Question' : question ,'Answer': answer, 'Sources' : sources}

    tasks = [answer_question(question) for question in questions]
    results = await asyncio.gather(*tasks)
    results_df = pd.DataFrame(results)

    answer_path = os.getenv('answer_path')
    filename = filepath.stem + '_answers'
    save_name = answer_path + filename
    results_df.to_csv(save_name,index=False,encoding='utf-8-sig')


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



if __name__ == "__main__":

    asyncio.run(run_testset())