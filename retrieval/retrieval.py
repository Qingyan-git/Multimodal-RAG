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

from ingestion.ingest_pdfs import save_to_file
from scripts.supabase_setup import retrieve_pdf_path_from_page_id, retrieve_markdowns
from scripts.qdrant_setup import similarity_search, format_point
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

    rrf_results = {}
    for page_id in results.keys():
        if page_id in rrf_scores:
            rrf_results[page_id] = rrf_scores[page_id]
        
    sorted_items = sorted(rrf_results.items(), key=lambda item: item[1], reverse=True)[:5]
    
    return dict(sorted_items)


async def get_sources(question,splade,coarse,query):

    image_ranking = await similarity_search(splade,coarse,query)
    '''
    Structure : {page_id : image_score, page_id : image_score}
    '''
    print(f'\nimage_ranking : {image_ranking}\n')

    target_page_ids = [key for key in image_ranking.keys()]
    print(f'\ntarget_page_ids : {target_page_ids}\n')

    target_page_markdowns = await retrieve_markdowns(target_page_ids)
    '''
    Structure : {page_id : markdown, page_id : markdown}
    '''
    print(f'target_page_markdowns : {target_page_markdowns}')

    text_ranking = Jina().text_rerank(question,target_page_markdowns)
    '''
    Structure : {page_id : text_score, page_id : text_score}
    '''
    print(f'\ntext_ranking : {text_ranking}\n')

    combined_ranking = {}
    for page_id in target_page_ids:
        combined_ranking[page_id] = {'image_score' : image_ranking[page_id], 'text_score' : text_ranking[page_id]}
    '''
    Structure : {page_id : {'text_score' : text_score, 'image_score' : image_score}}
    '''
    print(f'\ncombined_ranking : {combined_ranking}\n')
    






# async def get_text_scores(question,pages):
#     page_ids = list(pages.keys())
#     text_markdowns = await retrieve_markdowns(page_ids)
#     text_scores = Jina().text_rerank(question,text_markdowns)

#     return text_scores


# async def get_sources(question,splade,coarse,embeddings,pipeline_options):

#     image_scores = await similarity_search(splade,coarse,embeddings)
#     '''image_scores structure : {page_id: score}'''
#     text_scores = await get_text_scores(question,image_scores)
    
#     print(f'\nquestion : {question}\n')
#     print(f'\nimage_scores : {image_scores}\n')
#     print(f'\ntext_scores : {text_scores}\n')

#     combined_scores = {
#         page_id: {'image_score': image_scores[page_id], 'text_score': text_scores[page_id]}
#         for page_id in text_scores
#     }

#     print(f'combined_scores : {combined_scores}')

#     top_5_rrf = apply_rrf(combined_scores)
    
#     print(f'top_5_rrf : {top_5_rrf}')

#     page_sources = []

#     for page_id in top_5_rrf.keys():

#         converter = DocumentConverter(
#             format_options={
#                 InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
#             }
#         )

#         page_no, filepath = await retrieve_pdf_path_from_page_id(page_id)

#         conversion_result = await asyncio.to_thread(converter.convert, filepath, page_range=(page_no,page_no))
#         document = conversion_result.document
#         page = document.pages[page_no]

#         pil_image = page.image.pil_image
#         item = {
#             'image' : pil_image,
#             'source' : f'Document {Path(filepath).name}, page {page_no}'
#         }
#         page_sources.append(item)

#         if hasattr(document, "unload"):
#             try:
#                 document.unload()
#             except Exception:
#                 pass

#     print(f'\npage_sources : {page_sources}\n')

#     return page_sources


async def answer_testset(filepath,pipeline_options,openai,colqwen,sparse):

    df = pd.read_csv(filepath)
    questions = df.iloc[:, 0]
    results = []

    semaphore = asyncio.Semaphore(1)

    async def answer_question(question):
        async with semaphore:

            splade_vector = await sparse.embed(question)
            coarse_vector, embeddings = await colqwen.embed_query(question)
            
            sources = await get_sources(question,splade_vector,coarse_vector,embeddings)
            '''
            here problem
            '''

            answer = await openai.answer_question(question,sources)

            return {'Question' : question ,'Answer': answer, 'Sources' : sources}

    tasks = [answer_question(question) for question in questions]
    results = await asyncio.gather(*tasks)
    results_df = pd.DataFrame(results)

    answer_path = Path(os.getenv('answer_path'))
    filename = filepath.stem + '_answers.csv'
    save_name = answer_path / filename
    print(f'save_name : {save_name}')
    results_df.to_csv(save_name,index=False,encoding='utf-8-sig')


async def run_testset():

    try:

        testset_path = Path(os.getenv('testset_path'))

        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_page_images = True

        openai_model = OpenAIModel()
        colqwen_model = ColQwenModel()
        sparse_embedder = SparseEmbedder()

        if testset_path.is_dir():
            for file in testset_path.iterdir():
                if file.suffix == '.csv':

                    print(f'Processing {file.name}\n\n')

                    await answer_testset(file,pipeline_options,openai_model,colqwen_model,sparse_embedder)

                    print(f'Done\n\n')


    except Exception as e:
        print(f'Unable to answer testsets, error \n{e}\n\n')
        raise



if __name__ == "__main__":

    asyncio.run(run_testset())