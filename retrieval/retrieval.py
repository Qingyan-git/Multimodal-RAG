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
import pymupdf

from scripts.supabase import retrieve_markdowns, retrieve_source_from_pageid, retrieve_info_from_pageid, retrieve_string_from_pageid
from scripts.qdrant import similarity_search
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
        pdf_name, page_no, source_url = await retrieve_source_from_pageid(page_id)
        source = (page_id, pdf_name, page_no, source_url) 
        return source

    tasks = [_process_source(page_id) for page_id in page_ids]
    sources = await asyncio.gather(*tasks)
    return sources


async def extract_used_sources(llm_output, original_sources):

    parts = re.split(r"\n*---\s*SOURCES\s*---\n*", llm_output, maxsplit=1)
    clean_answer = parts[0].strip() if len(parts) > 1 else llm_output
    source_block = parts[1] if len(parts) > 1 else None

    if source_block == None:
        return clean_answer, [{
            'pdf_name' : source[1],
            'page_num' : source[2],
            "signed_url": source[3]
        } for source in original_sources]

    else:
        source_pattern = r"<used_source>ID:\s*([^<]+)\s*</used_source>"
        matched_ids = re.findall(source_pattern, source_block)

        used_sources = []
        source_map = {str(src[0]).strip(): src for src in original_sources}
        for page_id in matched_ids:
            clean_id = page_id.strip()
            if clean_id in source_map:
                source_data = source_map[clean_id]
                used_sources.append({
                    "pdf_name": source_data[1],
                    "page_num": int(source_data[2]),
                    "signed_url": source_data[3]
                })
            else:
                print(f"Warning: LLM cited ID '{clean_id}', but it wasn't in original_sources.")

        return clean_answer, used_sources


async def answer_user_question(question):

    time_taken = ''

    print(f'\nquestion : {question}\n')

    total_pre = datetime.now()

    pre = datetime.now()
    splade = await sparse_embedder.embed(question)
    multi = await colqwen_model.get_query_embedding(question)
    post = datetime.now()
    time_taken += f'Time taken to embed question vector: {(post-pre).total_seconds()}\n'

    pre = datetime.now()
    image_scores = await similarity_search(splade, multi)
    post = datetime.now()
    time_taken += f'Time taken to do similarity search: {(post-pre).total_seconds()}\n'
    page_ids = list(image_scores.keys())
    print(f'\nsimilarity search page_ids : {page_ids}\n')

    pre = datetime.now()
    markdowns = await retrieve_markdowns(page_ids)
    post = datetime.now()
    time_taken += f'Time taken to retrieve markdowns: {(post-pre).total_seconds()}\n'

    pre = datetime.now()
    text_scores = jina.text_rerank(question, markdowns)
    post = datetime.now()
    time_taken += f'Time taken to do text reranking: {(post-pre).total_seconds()}\n'

    pre = datetime.now()
    combined_scores = {}
    for page_id in page_ids:
        combined_scores[page_id] = {
            'image_score': image_scores.get(page_id, 0),
            'text_score': text_scores.get(page_id, 0)
        }
    rrf_results = apply_rrf(combined_scores)
    post = datetime.now()
    time_taken += f'Time taken to do rrf: {(post-pre).total_seconds()}\n'
    answer_page_ids = list(rrf_results.keys())
    print(f'\nanswer_page_ids : {answer_page_ids}\n')

    pre = datetime.now()
    sources = await get_sources(answer_page_ids)
    post = datetime.now()
    time_taken += f'Time taken to get sources: {(post-pre).total_seconds()}\n'

    pre = datetime.now()
    answer = await openai_model.answer_question(question, sources)
    post = datetime.now()
    time_taken += f'Time taken to answer question on openai: {(post-pre).total_seconds()}\n'

    pre = datetime.now()
    cleaned_answer, used_sources = await extract_used_sources(answer,sources)
    post = datetime.now()
    time_taken += f'Time taken to extract out used sources: {(post-pre).total_seconds()}\n'

    total_post = datetime.now()
    total_time = (total_post - total_pre).total_seconds()
    time_taken += f'Total time taken to answer question : {total_time}\n'

    print(f'\nTime taken : {time_taken}\n')

    '''
    check here if object nonetype iterable error
    '''
    return cleaned_answer, used_sources


async def answer_csv(path):

    '''
    need to change the return of answer_user_question from cleaned_answer, used_sources to cleaned_answer, answer_page_ids, time_taken
    '''

    df = pd.read_csv(path)
    questions = df.iloc[:, 0].tolist()
    results = []
    for question in questions:
        cleaned_answer,answer_page_ids,time_taken = await answer_user_question(question)
        sources_string = ""
        for page_id in answer_page_ids:
            pdf_name, page_no = await retrieve_string_from_pageid(page_id)
            sources_string += f"-- Source : Page {page_no} from file {pdf_name} --\n"
        result = {
            'Question' : question,
            'Answer' : cleaned_answer,
            'Sources' : sources_string,
            'Time taken' : time_taken
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

    asyncio.run(answer_testset(Path(r'C:\Users\Chu Qingyan\Documents\WFH\Multimodal-RAG\testset')))


