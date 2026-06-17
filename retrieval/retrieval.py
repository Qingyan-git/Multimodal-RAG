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

from scripts.supabase import retrieve_markdowns, retrieve_source_from_pageid, retrieve_source_from_pdf_name, retrieve_string_from_pageid
from scripts.qdrant import similarity_search
from scripts.models import QueryRequest, QueryResponse, DocumentSource
from scripts.models import (
    openai_model,
    qwen3vl_model,
    colqwen_model,
    sparse_embedder,
    jina
)

from scripts.config import settings


def apply_rrf(results, k=60):
    """
    Results data structure : {page_id:{'text_score':text_score,'image_score':image_score}}
    """
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

    colqwen_rank_map = {item[0]: rank for rank, item in enumerate(colqwen_sorted)}
    jina_rank_map = {item[0]: rank for rank, item in enumerate(jina_sorted)}

    # Dynamic selection (image) using maximum scalar bounds
    image_scores = [item['image_score'] for item in results.values()]
    max_image_score = max(image_scores) if image_scores else 0
    image_cutoff = max_image_score * 0.8
    image_docs = [page_id for page_id, scores in results.items() if scores.get('image_score', 0) >= image_cutoff]

    # Dynamic selection (text) using absolute threshold filters
    TEXT_ABSOLUTE_THRESHOLD = 0.30
    text_docs = [page_id for page_id, scores in results.items() if scores.get('text_score', 0) >= TEXT_ABSOLUTE_THRESHOLD]

    rrf_scores = {}
    for page_id in image_docs:
        rank = colqwen_rank_map[page_id]
        rrf_scores[page_id] = 1.0 / (k + (rank + 1))
        
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


async def get_sources(page_ids):
    async def _process_source(page_id):
        pdf_name, page_no, page_image = await retrieve_source_from_pageid(page_id)
        if page_image == None:
            print(f'\nNO PAGE IMAGE DETECTED FROM {pdf_name} {page_no}\n')
            image_base64 = ""
        else:
            image_base64 = base64.b64encode(page_image).decode('utf-8')

        source = (pdf_name, page_no, image_base64) 
        return source

    tasks = [_process_source(page_id) for page_id in page_ids]
    sources = await asyncio.gather(*tasks)
    return sources


async def extract_and_truncate_sources(llm_output):
    parts = re.split(r"\n*---\s*SOURCES\s*---\n*", llm_output, maxsplit=1)
    clean_answer = parts[0] if len(parts) > 1 else llm_output
    source_block = parts[1] if len(parts) > 1 else ""

    source_pattern = r"<used_source>PDF NAME:\s*(.*?)\s*\|\s*PAGE NUMBER:\s*(\d+)\s*</used_source>"
    matches = re.findall(source_pattern, source_block)

    async def _process_match(pdf_name, page_no):

        page_image = await retrieve_source_from_pdf_name(pdf_name,page_no)

        if page_image == None:
            print(f'\nNO PAGE IMAGE DETECTED FROM {pdf_name} {page_no}\n')
            image_base64 = ""
        else:
            image_base64 = base64.b64encode(page_image).decode('utf-8')

        return {
            "pdf_name": pdf_name,
            "page_num": int(page_no),
            "image_base64": image_base64
        }

        return source

    tasks = [_process_match(pdf_name, page_no) for pdf_name, page_no in matches]
    used_sources = await asyncio.gather(*tasks)
        
    return clean_answer, used_sources


async def answer_user_question(question):

    print(f'\nquestion : {question}\n')

    pre = datetime.now()
    splade = await sparse_embedder.embed(question)
    multi = await colqwen_model.get_query_embedding(question)
    post = datetime.now()
    print(f'Time taken to embed question vector: {(post-pre).total_seconds()}\n')

    pre = datetime.now()
    image_scores = await similarity_search(splade, multi)
    post = datetime.now()
    print(f'Time taken to do similarity search: {(post-pre).total_seconds()}\n')
    page_ids = list(image_scores.keys())
    print(f'\nsimilarity search page_ids : {page_ids}\n')

    pre = datetime.now()
    markdowns = await retrieve_markdowns(page_ids)
    post = datetime.now()
    print(f'Time taken to retrieve markdowns: {(post-pre).total_seconds()}\n')

    pre = datetime.now()
    text_scores = jina.text_rerank(question, markdowns)
    post = datetime.now()
    print(f'Time taken to do text reranking: {(post-pre).total_seconds()}\n')

    pre = datetime.now()
    combined_scores = {}
    for page_id in page_ids:
        combined_scores[page_id] = {
            'image_score': image_scores.get(page_id, 0),
            'text_score': text_scores.get(page_id, 0)
        }
    rrf_results = apply_rrf(combined_scores)
    post = datetime.now()
    print(f'Time taken to do rrf: {(post-pre).total_seconds()}\n')
    answer_page_ids = list(rrf_results.keys())
    print(f'\nanswer_page_ids : {answer_page_ids}\n')

    pre = datetime.now()
    sources = await get_sources(answer_page_ids)
    post = datetime.now()
    print(f'Time taken to get sources: {(post-pre).total_seconds()}\n')

    pre = datetime.now()
    answer = await openai_model.answer_question(question, sources)
    post = datetime.now()
    print(f'Time taken to answer question on openai: {(post-pre).total_seconds()}\n')

    pre = datetime.now()
    cleaned_answer, used_sources = await extract_and_truncate_sources(answer)
    post = datetime.now()
    print(f'Time taken to extract out used sources: {(post-pre).total_seconds()}\n')


    '''
    check here if object nonetype iterable error
    '''
    return cleaned_answer, used_sources


async def answer_csv(path):

    '''
    need to change the return of answer_user_question from cleaned_answer, used_sources to cleaned_answer, answer_page_ids
    '''

    df = pd.read_csv(path)
    questions = df.iloc[:, 0].tolist()
    results = []
    for question in questions:
        cleaned_answer,answer_page_ids = await answer_user_question(question)
        sources_string = ""
        for page_id in answer_page_ids:
            pdf_name, page_no = await retrieve_string_from_pageid(page_id)
            sources_string += f"-- Source : Page {page_no} from file {pdf_name} --\n"
        result = {
            'Question' : question,
            'Answer' : cleaned_answer,
            'Sources' : sources_string
        }
        results.append(result)

    result_df = pd.DataFrame(results)
    save_path = Path(settings.results_path) / f'{path.stem}_results.csv'
    result_df.to_csv(save_path,index=False)


async def answer_testset(path):
    try:
        if path.is_dir():
            for file in path.iterdir():
                if file.suffix == '.csv':
                    print(f'\nProcessing {file.name}\n')
                    await answer_csv(file)
                    print(f'\nDone\n')

        elif path.is_file() and path.suffix == '.csv':
            print(f'\nProcessing {path.name}\n')
            await answer_csv(path)
            print(f'\nDone\n')

    except Exception as e:
        print(f'An error occurred: \n{e}\n\n')
        raise



if __name__ == "__main__":

    asyncio.run(answer_testset(Path(r'C:\Users\UserAdmin\Documents\Multimodal-RAG\testset\test_set - Guide to Data Protection.csv')))


