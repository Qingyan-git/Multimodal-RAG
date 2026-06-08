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

    sources = []

    for page_id in page_ids:

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
        sources.append(source)

    return sources


async def extract_and_truncate_sources(llm_output):
    """
    Splits the conversational answer from the metadata manifest block,
    then parses every <used_source> line using structured regex boundaries.
    
    Returns:
        tuple: (clean_conversational_answer_str, list_of_parsed_source_dicts)
    """

    parts = re.split(r"\n*---\s*SOURCES\s*---\n*", llm_output, maxsplit=1)
    
    clean_answer = parts[0].strip()
    source_block = parts[1] if len(parts) > 1 else ""

    source_pattern = r"<used_source>PDF NAME:\s*(.*?)\s*\|\s*PAGE NUMBER:\s*(\d+)\s*</used_source>"
    matches = re.findall(source_pattern, source_block)

    used_sources = []
    for pdf_name, page_no in matches:

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

        source = DocumentSource(pdf_name=pdf_name,page_num=int(page_no),image_base64=image_base64)
        used_sources.append(source)
        
    return used_sources


async def answer_user_question(question):

    #question = input('Enter the question : ')

    splade = await sparse_embedder.embed(question)
    coarse, multi = await colqwen_model.embed_query(question)

    image_scores = await similarity_search(splade,coarse,multi)
    # print(f'\nimage_scores : {image_scores}\n')

    page_ids = [key for key in image_scores.keys()]
    # print(f'\npage_ids : {page_ids}\n')

    markdowns = await retrieve_markdowns(page_ids)
    # print(f'\nmarkdowns : {markdowns}\n')

    text_scores = jina.text_rerank(question,markdowns)
    # print(f'\ntext_scores : {text_scores}\n')

    combined_scores = {}
    for page_id in page_ids:
        combined_scores[page_id] = {
            'image_score' : image_scores.get(page_id, 0),
            'text_score' : text_scores.get(page_id, 0)}
    # print(f'\ncombined_scores : {combined_scores}\n')

    rrf_results = apply_rrf(combined_scores)
    # print(f'\nrrf_results : {rrf_results}\n')

    answer_page_ids = [key for key in rrf_results.keys()]
    # print(f'\nanswer_page_ids : {answer_page_ids}\n')

    sources = await get_sources(answer_page_ids)

    answer = await openai_model.answer_question(question,sources)
    # print(f'\nanswer : {answer}\n')

    used_sources = await extract_and_truncate_sources(answer)

    query_response = QueryResponse(answer=answer,sources=used_sources)

    return query_response


async def answer_testset():

    semaphore = asyncio.Semaphore(3)

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

    asyncio.run(answer_user_question('What does the government define a Third Party under these regulations?'))
