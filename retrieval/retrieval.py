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
from scripts.supabase_setup import retrieve_markdowns, retrieve_source_from_pageid, retrieve_source_from_pdf_name
from scripts.qdrant_setup import similarity_search
from scripts.models import QueryRequest, QueryResponse, DocumentSource
from scripts.models import (
    openai_model,
    qwen3vl_model,
    colqwen_model,
    sparse_embedder,
    jina
)


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
        image_base64 = base64.b64encode(page_image).decode('utf-8')

        return {
            "pdf_name": pdf_name,
            "page_num": int(page_no),
            "image_base64": image_base64
        }

        return source

    tasks = [_process_match(pdf_name, int(page_no)) for pdf_name, page_no in matches]
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
    print(f'Time taken to answer question on qwen3vl: {(post-pre).total_seconds()}\n')

    pre = datetime.now()
    cleaned_answer, used_sources = await extract_and_truncate_sources(answer)
    post = datetime.now()
    print(f'Time taken to extract out used sources: {(post-pre).total_seconds()}\n')

    return cleaned_answer, used_sources


if __name__ == "__main__":

    question = 'Which specific cause provided a HALE gain through morbidity reduction for the 70+ age group between 2000 and 2019?'
    # 'What was the specific HALE loss attributed to diabetes mellitus morbidity in the 30–69 age group globally between 2000 and 2019?'
    # 'Which cause is the leading driver of HALE gain for the African Region in the 30–69 age group (2000–2019)?',
    # 'Which WHO region is the only one to show a HALE loss due to Collective violence and legal intervention in the 2000–2019 data?',
    # 'Which condition caused the largest morbidity-related HALE loss globally during the 2019–2021 period?',
    # 'How many years of HALE were lost in the Region of the Americas due to COVID-19 mortality in the 70+ age group specifically?'
    # 'What is the leading cause of HALE disadvantage for females compared to males globally?',
    # 'What is the HALE advantage for females in the Western Pacific Region regarding stroke mortality?',
    # 'What was the global HALE advantage for females over males regarding COVID-19 mortality in 2021?',
    # 'Which region saw the smallest female HALE advantage (0.01 years) in COVID-19 mortality for the 70+ age group in 2021?',
    # 'What is the HALE gap between High-income and Low-income countries caused by Lower respiratory infections in the 0–1 age group?',
    # 'What is the negative HALE contribution of Drug use disorders for High-income countries when compared to Lower-middle-income countries?',
    # 'What is the HALE lead for High-income countries over Lower-middle-income countries due specifically to COVID-19 mortality?',
    # 'Which cause contributes a -0.16 year HALE disadvantage to High-income countries when compared to Low-income countries in the 2021 comparison?',
    # 'What was the estimated Maternal Mortality Ratio for the African Region in the year 2023?',
    # 'What was the Neonatal Mortality Rate for the South-East Asia Region in 1990?',
    # 'Which World Bank income group shows the most significant projected reduction in premature NCD mortality by 2030?',
    # 'What was the global suicide death rate per 100,000 population for males in 2021?',
    # 'Which region had the highest crude death rate (33.9) for interpersonal violence among males in 2021?',
    # 'What percentage of the global population requiring NTD interventions resides in the South-East Asia Region according to the 2023 distribution data?'

    response = asyncio.run(answer_user_question(question))

    answer_text = response[0]
    used_sources = response[1]
    print(f'\nQuestion : {question}\n')
    print(f'\nAnswer : {answer_text}\n')

    if used_sources:
            source_strings = [f"{src['pdf_name']} (Page {src['page_num']})" for src in used_sources]
            print(f'\nUsed Sources : {", ".join(source_strings)}\n')
    else:
        print('\nUsed Sources : None\n')



