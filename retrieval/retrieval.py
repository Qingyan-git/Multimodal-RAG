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

from scripts.supabase_setup import retrieve_pdf_path_from_page_ids, retrieve_markdowns
from scripts.qdrant_setup import similarity_search
from scripts.models import OpenAIModel, ColQwenModel, SparseEmbedder, Jina



def apply_rrf(results, k=60):

    """
    Results data structure : {page_id:{'text_score':text_score,'image_score':image_score}}
    """

    #ranking the scores after each type of similarity search
    colqwen_sorted = sorted(
        results.items(), 
        key=lambda item: item[1].get("image_score", 0), 
        reverse=True
    )
    
    jina_sorted = sorted(
        results.items(), 
        key=lambda item: item[1].get("text_score", 0), 
        reverse=True
    )

    colqwen_rank_map = {item[0] : rank for rank, item in enumerate(colqwen_sorted)}
    jina_rank_map = {item[0] : rank for rank, item in enumerate(jina_sorted)}

    # dynamic selection (image)
    image_scores = [item['image_score'] for item in results.values()]
    max_image_score = max(image_scores)
    image_cutoff = max_image_score * 0.8
    image_docs = [page_id for page_id,scores in results.items() if scores.get('image_score',0) >= image_cutoff]

    # dynamic selection (text)
    TEXT_ABSOLUTE_THRESHOLD = 0.30
    text_docs = [page_id for page_id,scores in results.items() if scores.get('text_score',0) >= TEXT_ABSOLUTE_THRESHOLD]

    rrf_scores = {}
    for page_id in image_docs:
        rank = colqwen_rank_map[page_id]
        rrf_scores[page_id] = 1.0 / (k + (rank+1))
    for page_id in text_docs:
        rank = jina_rank_map[page_id]
        if page_id in rrf_scores:
            rrf_scores[page_id] += 1.0 / (k + (rank + 1))
        else:
            rrf_scores[page_id] = 1.0 / (k + (rank + 1))

    for page_id, scores in results.items():
        if page_id in rrf_scores:
            results[page_id]['rrf_score'] = rrf_scores[page_id]

    filtered_items = [item for item in results.items() if 'rrf_score' in item[1]]
    sorted_items = sorted(filtered_items, key=lambda item: item[1].get('rrf_score', 0), reverse=True)
    
    return [page_id for page_id, scores in sorted_items][:5]


async def get_text_scores(question,pages):
    text_markdowns = await retrieve_markdowns(pages)
    text_scores = Jina().text_rerank(question,text_markdowns)

    return text_scores


async def get_sources(question,splade,coarse,embeddings,converter):

    image_scores = await similarity_search(splade,coarse,embeddings)
    text_scores = await get_text_scores(question,image_scores)
    
    print(f'\nimage_scores : {image_scores}\n')
    print(f'\text_scores : {text_scores}\n')

    combined_scores = {
        page_id: {'image_score': image_scores[page_id], 'text_score': text_scores[page_id]}
        for page_id in text_scores
    }

    print(f'combined_scores : {combined_scores}')

    page_sources = []
    top_5_rrf = apply_rrf(combined_scores)

    for page_id in top_5_rrf:
        page_no, filepath = await retrieve_pdf_path_from_page_ids(page_id)

        document = converter.convert(filepath)
        page = document.pages[page_no]
        
        pil_image = page.image
        item = {
            'image' : pil_image,
            'source' : f'Document {Path(filepath).name}, page {page_no}'
        }
        page_sources.append(item)

        if hasattr(document, "unload"):
            try:
                document.unload()
            except Exception:
                pass

    return page_sources
    


# async def get_source_images(splade,coarse,embeddings,converter,doc_cache,cache_lock):

#     page_ids = await similarity_search(splade,coarse,embeddings)
#     answer_sources = await retrieve_files(page_ids)
#     page_sources = []
#     for source in answer_sources:

#         filename = source['name']
#         page_no = source['page_no']

#         filepath = await retrieve_pdf_path(filename)
#         async with cache_lock:
#             if filename not in doc_cache:
#                 # Running heavy blocking CPU code like converter.convert inside async 
#                 # can freeze the loop. The lock ensures only one task does it at a time.
#                 doc_cache[filename] = converter.convert(filepath)
#         document = doc_cache[filename]
#         page = document.pages[page_no-1]
        
#         pil_image = page.image
#         item = {
#             'image' : pil_image,
#             'source' : f'Document {filename}, page {page_no}'
#         }
#         page_sources.append(item)

#     return page_sources


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
            sources = await get_sources(question,splade_vector,coarse_vector,embeddings,converter)
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
        pipeline_options.generate_page_images = True
        
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