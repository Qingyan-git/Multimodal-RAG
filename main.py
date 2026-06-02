from fastapi import FastAPI, HTTPException, status, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import os 
import uvicorn
from ingestion import ingest_pdfs
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=dotenv_path, override=True)


app = FastAPI(title="RAG Backend")
STORAGE_DIR = r"C:\Users\UserAdmin\Documents\Multimodal-RAG\pdfs"

class DocumentSource(BaseModel):
    pdf_name: str
    page_num: int
    image_base64: str 

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[DocumentSource]

def process(filename: str):
    try: 
        pass
    except Exception as e:
        pass

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try: 
        answer_string, sources_list = retrieve(request.question)
        return {
            "answer": answer_string,
            "sources": sources_list
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