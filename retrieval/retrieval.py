import asyncio
from pathlib import Path
from PIL import Image
import io
import base64
import os
import sys
import re
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

# from ingestion.ingest_pdfs import save_to_file
from scripts.supabase_setup import retrieve_pdf_info, retrieve_markdowns, get_path_from_pdf_name
from scripts.qdrant_setup import similarity_search
from scripts.models import QueryRequest, QueryResponse, DocumentSource
from scripts.models import (
    openai_model,
    colqwen_model,
    document_converter,
    sparse_embedder,
    jina
)


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

    rrf_results = {}
    for page_id in results.keys():
        if page_id in rrf_scores:
            rrf_results[page_id] = rrf_scores[page_id]
        
    sorted_items = sorted(rrf_results.items(), key=lambda item: item[1], reverse=True)[:5]
    
    return dict(sorted_items)


def encode_pil_to_base64(pil_image):
    buffered = io.BytesIO()
    pil_image.save(buffered, format='jpeg',quality=95)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


async def get_sources(page_ids):

    async def _process_source(page_id):

        page_no, pdf_name, pdf_path = await retrieve_pdf_info(page_id)

        conversion_result = await asyncio.to_thread(
            document_converter.convert, 
            pdf_path, 
            page_range=(page_no, page_no)
        )
        document = conversion_result.document

        page = document.pages[page_no]
        page_image = page.image.pil_image
        image_base64 = encode_pil_to_base64(page_image)

        source = DocumentSource(pdf_name=pdf_name,page_num=page_no,image_base64=image_base64)

        return source

    tasks = [_process_source(page_id) for page_id in page_ids]
    sources = await asyncio.gather(*tasks)

    return sources


async def extract_and_truncate_sources(llm_output):

    parts = re.split(r"\n*---\s*SOURCES\s*---\n*", llm_output, maxsplit=1)
    source_block = parts[1] if len(parts) > 1 else ""

    source_pattern = r"<used_source>PDF NAME:\s*(.*?)\s*\|\s*PAGE NUMBER:\s*(\d+)\s*</used_source>"
    matches = re.findall(source_pattern, source_block)

    async def _process_match(pdf_name,page_no):

        page_no = int(page_no)
        pdf_path = await get_path_from_pdf_name(pdf_name)

        conversion_result = await asyncio.to_thread(
            document_converter.convert, 
            pdf_path, 
            page_range=(page_no, page_no)
        )

        document = conversion_result.document
        page = document.pages[page_no]
        page_image = page.image.pil_image
        image_base64 = encode_pil_to_base64(page_image)

        source = DocumentSource(pdf_name=pdf_name,page_num=page_no,image_base64=image_base64)

        return source

    tasks = [_process_match(pdf_name,page_no) for pdf_name,page_no in matches]
    used_sources = await asyncio.gather(*tasks)
        
    return used_sources


async def answer_user_question(question):

    # question = input('Enter the question : ')

    pre = datetime.now()
    splade = await sparse_embedder.embed(question)
    coarse, multi = await colqwen_model.embed_query(question)
    post = datetime.now()
    taken = post-pre
    print(f'Time taken to embed question vector : {taken.total_seconds()}\n')

    pre = datetime.now()
    image_scores = await similarity_search(splade,coarse,multi)
    post = datetime.now()
    taken = post-pre
    print(f'Time taken to do similarity search : {taken.total_seconds()}\n')

    page_ids = [key for key in image_scores.keys()]

    pre = datetime.now()
    markdowns = await retrieve_markdowns(page_ids)
    post = datetime.now()
    taken = post-pre
    print(f'Time taken to retrieve markdowns : {taken.total_seconds()}\n')

    pre = datetime.now()
    text_scores = jina.text_rerank(question,markdowns)
    post = datetime.now()
    taken = post-pre
    print(f'Time taken to do text reranking : {taken.total_seconds()}\n')

    combined_scores = {}
    for page_id in page_ids:
        combined_scores[page_id] = {
            'image_score' : image_scores.get(page_id, 0),
            'text_score' : text_scores.get(page_id, 0)}

    pre = datetime.now()
    rrf_results = apply_rrf(combined_scores)
    post = datetime.now()
    taken = post-pre
    print(f'Time taken to do rrf : {taken.total_seconds()}\n')

    answer_page_ids = [key for key in rrf_results.keys()]

    pre = datetime.now()
    sources = await get_sources(answer_page_ids)
    post = datetime.now()
    taken = post-pre
    print(f'Time taken to get sources : {taken.total_seconds()}\n')


    pre = datetime.now()
    answer = await openai_model.answer_question(question,sources)
    post = datetime.now()
    taken = post-pre
    print(f'Time taken to answer question on openai : {taken.total_seconds()}\n')

    pre = datetime.now()
    used_sources = await extract_and_truncate_sources(answer)
    post = datetime.now()
    taken = post-pre
    print(f'Time taken to extract out used sources : {taken.total_seconds()}\n')

    query_response = QueryResponse(answer=answer,sources=used_sources)

    print(f'answer : \n{answer}\n')

    return query_response


async def answer_testset():

    semaphore = asyncio.Semaphore(5)

    async def _answer_test(question):
        async with semaphore:
            response = await answer_user_question(question)
            answer = response.answer
            sources = response.sources
            return {
                'Question': question,
                'Answer': answer,
                'Sources': [f"{x.pdf_name} + {x.page_num}" for x in sources]
            }
    file = r"C:\Users\UserAdmin\Documents\Multimodal-RAG\testset\test_set - WHO World health statistics 2025 .csv"
    df = pd.read_csv(file)
    questions = df.iloc[:, 0]

    tasks = [_answer_test(question) for question in questions]
    results = await asyncio.gather(*tasks)
    results_df = pd.DataFrame(results)

    output_path = Path(r'C:\Users\UserAdmin\Documents\Multimodal-RAG\testing-results\answers') / f"{Path(file).stem}_results.csv"
    results_df.to_csv(output_path, index=False)



if __name__ == "__main__":

    asyncio.run(answer_user_question('What was the global suicide death rate per 100,000 population for males in 2021?'))
