from fastapi import FastAPI, HTTPException, status, UploadFile, File, BackgroundTasks, Depends, Cookie, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import os 
import uvicorn
from ingestion import ingest_pdfs
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from io import BytesIO

from scripts.models import QueryRequest, QueryResponse

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from fastembed import SparseTextEmbedding

from scripts.config import settings
from scripts.models import openai_model, colqwen_model, qwen3vl_model, sparse_embedder, jina
from retrieval.retrieval import answer_user_question
from features.user_login import sign_up, login, verify_session
from features.history_aware_answer import process_user_question
from scripts.supabase import get_chats, get_chatitems, create_chat, create_chatitem, get_chat_history, get_documents, download_document

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
    question : str
    chat_id : int


class QueryResponse(BaseModel):
    chat_id : int
    answer: str
    sources: List[DocumentSource]


class UserCredentials(BaseModel):
    username : str
    password : str


async def user_verification(session_id:str=Cookie(None)):

    if not session_id:
        raise HTTPException(status_code=401, detail="Please log in first.")

    user_id = await verify_session(session_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired or invalid, please log in again.")
        
    return user_id


@app.post("/signup")
async def user_signup(user_data: UserCredentials, response: Response):
    try:
        username = user_data.username
        password = user_data.password

        await sign_up(username, password)

        session_id = await login(username, password)

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=300
        )

        return { 
            "message": f"User {username} registered and logged in successfully.",
            "status": "success"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Unable to sign up, error \n{e}\n')


@app.post("/login")
async def user_login(user_data:UserCredentials, response:Response):
    try:
        username = user_data.username
        password = user_data.password

        session_id = await login(username,password)

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=300
        )

        return {
            "message" : f"Welcome back, {username}",
            "status" : "success"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Unable to login, error \n{e}\n')


@app.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest, user_id: int = Depends(user_verification)):
    try:
        question = payload.question
        chat_id = payload.chat_id
        
        response = await process_user_question(question,chat_id,user_id)

        query_response = QueryResponse(
            chat_id=response['chat_id'],
            answer=response['answer'],
            sources=[
            DocumentSource(
                    pdf_name=src["pdf_name"],
                    page_num=src["page_num"],
                    image_base64=src["image_base64"]
                )
                for src in response['sources']]
        )

        return query_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer user question, error \n{e}\n")


@app.post("/chats")
async def show_chats(user_id:int=Depends(user_verification)):
    try:
        user_chats = await get_chats(user_id)
        
        return {
            "status": "success",
            "chats": user_chats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user chats, error \n{e}\n")


@app.post("/chats/{chat_id}")
async def enter_chat(chat_id:str,user_id: int = Depends(user_verification)):
    try:
        chat_items = await get_chatitems(user_id,chat_id)

        return {
            "status": "success",
            "chat_items": chat_items
        }        
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enter chat and load history, error \n{e}\n")


@app.post("/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:

        content = await file.read()
        filesize_bytes = len(content)
        target_path = settings.local_storage_dir / file.filename
        with open(target_path, "wb") as f:
            f.write(content)
        absolute_local_path = str(target_path.resolve())
        background_tasks.add_task(ingest_pdfs.ingest_pdf, Path(absolute_local_path), filesize_bytes)

        return {
            "status": "success",
            "message": f"'{file.filename}' successfully processed.",
        }


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {e}")


@app.post("/documents")
async def return_documents(user_id: int = Depends(user_verification)):
    try:
        uploaded_documents = await get_documents()

        documents = []
        for document in uploaded_documents:
            documents.append({
                'name' : document['name'],
                'filesize' : document['filesize'],
                'created_at' : document['created_at'] 
            })

        return {
            "status" : "success",
            "documents" : documents
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unable to retrieve uploaded documents, error \n{e}\n')


@app.post("/documents/download/{document_name}")
async def download_document_name(document_name: str, user_id: int = Depends(user_verification)):
    try:
        pdf = await download_document(document_name)

        if not pdf:
            raise HTTPException(status_code=404, detail="File bytes not found in storage bucket.")

        return StreamingResponse(
            BytesIO(pdf),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={document_name}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unable to download selected document, error \n{e}\n')



if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)