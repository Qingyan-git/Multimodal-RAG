
import os
import io
import base64
import asyncio
import torch
import requests

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.rate_limiters import InMemoryRateLimiter

from transformers.utils.import_utils import is_flash_attn_2_available
from colpali_engine.models import ColQwen2, ColQwen2Processor

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from fastembed import SparseTextEmbedding

from scripts.config import settings


rate_limiter = InMemoryRateLimiter(
    requests_per_second=10,
    max_bucket_size=10,
    check_every_n_seconds=0.1
)

class OpenAIModel:

    def __init__(self):

        model = settings.openai_model
        api_key = settings.openai_api_key.get_secret_value()

        self.model = ChatOpenAI(
            model=model,
            api_key=api_key,
            rate_limiter=rate_limiter,
            temperature=0,
            max_tokens=4096,
            timeout=60,
            max_retries=2,
            reasoning_effort='minimal'
        )


    async def get_image_description(self,pil_image):

        buffered = io.BytesIO()
        pil_image = pil_image.convert("RGB")
        pil_image.save(buffered, format="JPEG", quality=95)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{img_str}"

        messages = [
            SystemMessage(content="""You are an expert Document Layout and Visual Data Extraction engine. 
            Your single task is to convert the provided image into a dense, highly accurate textual representation optimized for vector-database indexing and semantic retrieval.

            Observe these strict extraction guardrails:
            1. DOCUMENT LAYOUT & STRATEGY: If the image is a flowchart, architecture diagram, or process map, explicitly list the nodes, relationships, directional flows, and logical dependencies ("X connects to Y via Z").
            2. DATA ISOLATION: If the image is a chart, graph, or matrix, extract every visible data point, axis label, metric scale, legend key, and observed statistical trend.
            3. SEMANTIC WEIGHT: Use rich, explicit domain-specific keywords. Do not summarize abstractly if you can describe concretely. Avoid vague descriptions like "a beautiful chart". Instead use "Bar chart illustrating 2026 projected fiscal growth metrics".
            4. OUTPUT FORMAT: Start directly with the factual analysis. Do not include introductory phrases like "Sure, here is the description" or conversational sign-offs. Write in clean, structural paragraph blocks or technical markdown lists."""
            ),
            HumanMessage(
                content=[
                    {
                        "type": "text", 
                        "text": "Analyze this extracted image layout element and output its semantic text equivalent for database serialization."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url}
                    }
                ]
            )
        ]

        response = await self.model.ainvoke(messages)
        content = response.content

        return content


    async def answer_question(self,question,sources):

        message = []
        
        for source in sources:

            pdf_name = source.pdf_name
            page_no = source.page_num
            image_base64 = source.image_base64

            message.append({
                "type": "text",
                "text": f"\n<DocumentSource file='{pdf_name}' page='{page_no}'>\n"
            })

            # Add the actual image
            message.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}",
                    "detail": "high"
                }
            })
            
            message.append({
                "type": "text",
                "text": f"\n</DocumentSource>\n"
            })

        # 2. Add the final user question
        message.append({
            "type": "text",
            "text": f"\nUser Query: {question}"
        })

        messages = [
            SystemMessage(content="""You are a specialized Document Analysis Assistant. You are provided with document images wrapped inside `<DocumentSource file="..." page="...">` XML boundaries.

            YOUR CORE TASKS:
            1. Formulate a comprehensive answer based solely on the text, charts, or visual evidence in the provided images.
            2. Provide explicit inline citations using the file and page properties whenever you state a fact extracted from an image (e.g., [filename.pdf, Page 1]).
            3. Underneath your complete answer, output a machine-readable list capturing ONLY the source documents you actively cited.

            STRICT OUTPUT FORMAT MATCHING:
            Your output must strictly separate the prose response from the source metadata using the exact tag block shown below:

            [Your detailed conversational and analysis response goes here, utilizing regular inline citations.]

            ---
            <used_source>PDF NAME: [Exact PDF Name] | PAGE NUMBER: [Exact Page Number]</used_source>

            CRITICAL INSTRUCTIONS FOR THE SOURCE MANIFEST:
            - DIRECT CORRELATION REQUIREMENT: A `<used_source>` line must ONLY be generated for a document if you explicitly cited that exact file and page number inline within your response text. If a source was provided but you did not use its facts to formulate the answer, DO NOT include it in the manifest.
            - ABSOLUTE ZERO RULE: If you determine that the images do not contain enough information to answer the query, state: "I cannot find the answer based on the provided document sources." When this happens, you MUST NOT output any `<used_source>` tags or the `---` markdown line. The manifest must be completely empty.
            - The `<used_source>` tags must sit at the absolute end of your output, with one tag per line for each document used.
            - You must use the exact format: <used_source>PDF NAME: filename.pdf | PAGE NUMBER: X</used_source>
            - Notice the pipe character `|` separating the name and the page number. This is mandatory.
            - Do not add any conversational transitions, markdown bullet points, or extra spaces outside or inside the `<used_source>` tags.
            """),
            HumanMessage(content=message)
        ]

        response = await self.model.ainvoke(messages)
        content = response.content

        return content



class ColQwenModel:

    def __init__(self):
        name = settings.colqwen_model

        self.model = ColQwen2.from_pretrained(
            name,
            torch_dtype=torch.bfloat16,
            device_map='auto',
            attn_implementation="flash_attention_2" if is_flash_attn_2_available() else "sdpa",
            trust_remote_code=True
        ).eval()
        self.processor = ColQwen2Processor.from_pretrained(name,trust_remote_code=True)


    def _get_coarse_embedding(self, embeddings_tensor):
        pooled = embeddings_tensor.mean(dim=1)
        normalised = pooled / pooled.norm(dim=-1, keepdim=True)
        return normalised.to(torch.float32).cpu()


    def _calculate_embedding(self, image):
        inputs = self.processor.process_images(images=[image])
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        with torch.no_grad():
            embeddings = self.model(**inputs)
            embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
            coarse_vector = self._get_coarse_embedding(embeddings).flatten().tolist()
            embeddings_multivector = embeddings.squeeze(0).to(torch.float32).cpu()

            return coarse_vector, embeddings_multivector

    
    async def get_image_embedding(self, image):
        loop = asyncio.get_running_loop()
        
        # This offloads the heavy tensor math to a background worker thread,
        # yielding execution back to the loop so your Supabase/OpenAI tasks can run simultaneously
        coarse_vector, embeddings_multivector = await loop.run_in_executor(
            None,                  # Uses default ThreadPoolExecutor
            self._calculate_embedding, 
            image
        )

        return coarse_vector, embeddings_multivector


    def _embed_query(self,query):
        inputs = self.processor.process_queries(queries=[query])
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        with torch.no_grad():
            embeddings = self.model(**inputs)
            embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True) # L2 normalization

            coarse_vector = self._get_coarse_embedding(embeddings).flatten().tolist()
            embeddings = embeddings.squeeze(0).to(torch.float32).cpu().tolist()
        return coarse_vector, embeddings

    
    async def embed_query(self,query):
        loop = asyncio.get_running_loop()

        coarse_vector, embeddings = await loop.run_in_executor(
            None,
            self._embed_query,
            query
        )

        return coarse_vector, embeddings



class SparseEmbedder:

    def __init__(self, model_name=settings.sparse_embedding_model, use_threads=8):

        self.model = SparseTextEmbedding(model_name=model_name, parallel=use_threads)

    
    def _calculate_embedding(self, item):
        embedding = list(self.model.embed(item))[0]
        return {
            "indices": embedding.indices.tolist(),
            "values": embedding.values.tolist()
        }


    async def embed(self, item):
        loop = asyncio.get_running_loop()

        embedding = await loop.run_in_executor(
            None,
            self._calculate_embedding,
            item
        )

        return embedding



class Jina:

    def __init__(self):
        self.url = settings.jina_url
        self.api_key = settings.jina_api_key.get_secret_value()
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def text_rerank(self, query, content):

        '''
        Content data structure is like : {page_id:markdown,page_id:markdown}
        '''

        page_ids = list(content.keys())
        markdowns = list(content.values())
        
        data = {
            "model": "jina-reranker-v3",
            "query": query,
            "documents": markdowns,
            "top_n": len(markdowns)
        }

        response = requests.post(self.url, headers=self.headers, json=data).json()

        results = {}
        for item in response.get("results", []):
            idx = item["index"]
            score = item["relevance_score"]
            page_id = page_ids[idx]
            results[page_id] = score

        return results

