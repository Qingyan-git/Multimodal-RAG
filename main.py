from fastapi import FastAPI, HTTPException, status, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import os 
import uvicorn
from ingestion import ingest_pdfs
from pathlib import Path
from dotenv import load_dotenv
from retrieval.retrieval import answer_user_question


from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from scripts.models import QueryRequest, QueryResponse

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from fastembed import SparseTextEmbedding
from scripts.models import OpenAIModel, ColQwenModel
from retrieval.retrieval import answer_user_question

BASE_DIR = Path(__file__).resolve().parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=dotenv_path, override=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True
    pipeline_options.generate_page_images = True
    pipeline_options.images_scale = 2.0
    
    app.state.models = {
        "converter": DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        ),
        "openai_model": OpenAIModel(),
        "colqwen_model": ColQwenModel(),
        "sparse_embedder": SparseTextEmbedding()
    }
    
    yield

    app.state.models.clear()


app = FastAPI(title="RAG Backend")
STORAGE_DIR = r"C:\Users\UserAdmin\Documents\Multimodal-RAG\pdfs"

class DocumentSource(BaseModel):
    pdf_name: str
    page_num: int
    image_base64: str 

class QueryRequest(BaseModel):
    text: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[DocumentSource]


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try: 
        query_response = await answer_user_question(request.text)
        return {
            "answer": query_response.answer,
            "sources": query_response.sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


@app.post("/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    target_path = os.path.join(STORAGE_DIR, file.filename)
    
    with open(target_path, "wb") as f:
        content = await file.read()
        f.write(content)

    background_tasks.add_task(ingest_pdfs.ingest_pdf, Path(target_path))

    return {"status": "success", "message": "File received"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)