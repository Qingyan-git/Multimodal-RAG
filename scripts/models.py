
import os
import io
import base64
import asyncio
import torch

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.rate_limiters import InMemoryRateLimiter

from transformers.utils.import_utils import is_flash_attn_2_available
from colpali_engine.models import ColQwen2, ColQwen2Processor

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from fastembed import SparseTextEmbedding


rate_limiter = InMemoryRateLimiter(
    requests_per_second=10,
    max_bucket_size=10,
    check_every_n_seconds=0.1
)

class OpenAIModel:

    def __init__(self):

        model = os.getenv('openai_model')
        api_key = os.getenv('openai_api_key')

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


    async def answer_question(self,user_query,sources):

        # 1. Construct the Image blocks for the Human Message
        image_content = []
        
        for source in sources:

            image = source['image']
            document = source['source']

            # Format the image
            buffer = io.BytesIO()
            rgb_image = image.convert("RGB")
            rgb_image.save(buffer, format="JPEG", quality=95)
            img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # TEXT ANCHOR: Tells the vision model exactly what page follows this boundary
            image_content.append({
                "type": "text",
                "text": f"\n--- Start of image from {document} ---\n"
            })

            # Add the actual image
            image_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_str}",
                    "detail": "high" # Ensures the LLM looks at the high-res version for small text
                }
            })

        # 2. Add the final user question
        image_content.append({
            "type": "text",
            "text": f"\nUser Query: {user_query}"
        })

        messages = [
            SystemMessage(content="""
            You are a specialized Document Analysis Assistant. You will be provided with images of document chunks paired with source text boundaries.

            YOUR TASKS:
            1. Analyze the provided images (including text, tables, and charts) to answer the user's query.
            2. For every fact you state, you MUST explicitly cite the original source using the tag provided directly above that image (e.g., [Source: filename.pdf, Page X]).
            3. If the answer is found in a chart or table, describe the visual evidence.
            4. If the images do not contain enough information, state that you cannot find the answer.

            FORMATTING:
            - Use clear, professional language.
            - Always use the strict citation format matching the text anchor: [Source: <extracted_source_text>].
            """),
            HumanMessage(content=image_content)
        ]

        response = await self.model.ainvoke(messages)
        content = response.content

        return content



class ColQwenModel:

    def __init__(self):
        name = os.getenv('colqwen_model')

        self.model = ColQwen2.from_pretrained(
            name,
            torch_dtype=torch.bfloat16,
            device_map='auto',
            attn_implementation="flash_attention_2" if is_flash_attn_2_available() else None,
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
            embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
            coarse_vector = self. _get_coarse_embedding(embeddings).flatten().tolist()
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

    def __init__(self, model_name=os.getenv('sparse_embedding_model'), use_threads=8):

        self.model = SparseTextEmbedding(model_name=model_name, parallel=use_threads)

    
    def _calculate_embedding(self, page_markdown):
        embedding = list(self.model.embed(page_markdown))[0]
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
        self.url = os.getenv('jina_url')
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JINA_API_KEY}"
        }

    def text_rerank(self, query, sources):
        ordered_page_ids = list(sources.keys())
        markdowns = [sources[page_id]['markdown'] for page_id in ordered_page_ids]
        
        data = {
            "model": "jina-reranker-v3",
            "query": query,
            "documents": markdowns,
            "top_n": len(markdowns)
        }

        response = requests.post(self.url, headers=self.headers, json=data).json()

        for item in response.get("results", []):
            origin = item["index"]            
            score = item["relevance_score"]

            page_id = ordered_page_ids[origin]

            sources[page_id]["text_score"] = score

        return sources

