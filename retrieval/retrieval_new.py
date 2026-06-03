import os
import io
import ast
import fitz
import json
import torch
import base64
import requests
import numpy as np
import pandas as pd
from PIL import Image
from dotenv import load_dotenv

from qdrant_client import QdrantClient, models
from qdrant_client.models import QueryRequest, Prefetch, Fusion, SparseVector

from colpali_engine.models import ColQwen2, ColQwen2Processor

from fastembed import SparseTextEmbedding

from supabase import create_client, Client

from langchain_openai import ChatOpenAI
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.messages import HumanMessage, SystemMessage

from scripts.config import settings

splade_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")

rate_limiter = InMemoryRateLimiter(
    requests_per_second=7,
    check_every_n_seconds=0.1,
    max_bucket_size=10
)

llm = ChatOpenAI(model=settings.openai_model, temperature=0, rate_limiter=rate_limiter, api_key=settings.openai_api_key.get_secret_value())

client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key.get_secret_value()
)

supabase = create_client(
    settings.supabase_url,
    settings.supabase_key.get_secret_value()
)

JINA_API_KEY = settings.jina_api_key.get_secret_value()

model_name = "vidore/colqwen2-v1.0"
model = ColQwen2.from_pretrained(
    model_name,
    dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
).eval()

processor = ColQwen2Processor.from_pretrained(
    model_name, 
    trust_remote_code=True
)

def get_coarse_embedding(embeddings_tensor):
    pooled = embeddings_tensor.mean(dim=1) # mean pooling 
    normalised = pooled / pooled.norm(dim=-1, keepdim=True) # L2 normalization 
    return normalised.squeeze().to(torch.float32).cpu()

def embed_query(query, model, processor):
    inputs = processor.process_queries(queries=[query])
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        embeddings = model(**inputs)
        embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True) # L2 normalization

        coarse_vector = get_coarse_embedding(embeddings).flatten().tolist()
        embeddings = embeddings.squeeze(0).to(torch.float32).cpu().tolist()
    return coarse_vector, embeddings

def get_query_embeddings(query):
    coarse_vector, page_embeddings = embed_query(query, model, processor)
    splade_vector = next(splade_model.query_embed(query))
    return coarse_vector, splade_vector, page_embeddings

def search(coarse_vector, splade_vector, page_embeddings):

    qdrant_vector = SparseVector(
        indices=splade_vector.indices.tolist(),
        values=splade_vector.values.tolist()
    )

    response = client.query_points(
        collection_name="multimodal-rag",

        prefetch=[
            models.Prefetch(
                query=coarse_vector,
                using="coarse_embedding",
                limit=50
            ),
            models.Prefetch(
                query=qdrant_vector,
                using="splade_vector",
                limit=50
            ),
        ],
        query=page_embeddings,
        using="page_embeddings",
        limit=20
    )
    
    retrieved = {}
    for point in response.points:
        page_id = point.payload.get("page_id")
        score = point.score
        retrieved[page_id] = score
    return retrieved

def retrieve_content(initial_search):
    target_page_ids = [key for key in initial_search.keys()]
    response = (
        supabase.table("pages")
        .select("page_id, pdfs(name, path), markdown, num")
        .in_("page_id", target_page_ids)
        .execute()
    )
    if response.data:
        results = []
        for record in response.data:
            pdf_info = record.get("pdfs") or {}

            page_id = record.get("page_id")
            markdown = record.get("markdown")
            pdf_name = pdf_info.get("name")
            page_num = record.get("num")
            pdf_path = pdf_info.get("path")
            image_score = initial_search.get(page_id)

            results.append({
                "page_id": page_id,
                "markdown": markdown,
                "pdf_name": pdf_name,
                "page_num": page_num,
                "pdf_path": pdf_path,
                "image_score": image_score
                
            })
    return results

def text_rerank(query, content):
    url = "https://api.jina.ai/v1/rerank"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}"
    }

    markdowns = [item["markdown"] for item in content]


    data = {
        "model": "jina-reranker-v3",
        "query": query,
        "documents": markdowns,
        "top_n": len(markdowns)
    }

    results = []

    response = requests.post(url, headers=headers, json=data).json()

    for item in response.get("results", []):
        idx = item["index"]
        score = item["relevance_score"]

        matched = content[idx]
        matched["text_score"] = score

        results.append(matched)
    
    return results 

    
def apply_rrf(results, k=60):

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

def retrieve_and_generate(query):
    coarse_vector, splade_vector, page_embeddings = get_query_embeddings(query)
    initial_search = search(coarse_vector, splade_vector, page_embeddings) 
    print(initial_search.keys())
    image_ranking = retrieve_content(initial_search)
    text_ranking = text_rerank(query, image_ranking)
    results = apply_rrf(text_ranking)
    results = results[:5]
    return results 

results = retrieve_and_generate("What was the Neonatal Mortality Rate for the South-East Asia Region in 1990?")
for item in results:
    print(item["pdf_name"], item["page_num"])
