from fastapi import FastAPI, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="RAG Backend")

class DocumentSource(BaseModel):
    pdf_name: str
    page_num: int
    image_base64: str 

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[DocumentSource]

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


@app.post("/upload", status_code=status.HTTP_204_NO_CONTENT)
async def upload_pdf(file: UploadFile = File(...)):
    try: 
        upload(file)
        return 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")
