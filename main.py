from fastapi import FastAPI, HTTPException, status, UploadFile, File, BackgroundTasks, Depends, Cookie, Response
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

from features.user_login import sign_up, login, verify_session
from scripts.supabase_setup import get_chats, get_chatitems

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

class UserCredentials(BaseModel):
    username : str
    password : str


@app.post("/signup")
async def user_signup(user_data:UserCredentials):
    try:
        username = user_data.username
        password = user_data.password

        await sign_up(username,password)

        return { 
                "message": f"User {username} registered successfully.",
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

        cookie = await login(username,password)

        response.set_cookie(
            key="session_id",
            value=cookie["session_id"],
            httponly=True,
            secure=True,
            samesite="strict",
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
async def query(request: QueryRequest):
    try: 
        query_response = await answer_user_question(request.text)
        return {
            "answer": query_response.answer,
            "sources": query_response.sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

'''
For /query, need to accept a response_model that includes the chat_id from which the question was asked in.
So that the chats can be properly updated.
Also if the user requests a new chat, then the object with a placeholder chat_id is passed to /query, and the
new chat is created in the /query function and saved to db and such.
Streamlit files will need to be updated to reflect this change.
'''


@app.post("/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    target_path = os.path.join(STORAGE_DIR, file.filename)
    
    with open(target_path, "wb") as f:
        content = await file.read()
        f.write(content)

    background_tasks.add_task(ingest_pdfs.ingest_pdf, Path(target_path))

    return {"status": "success", "message": "File received"}


async def user_verification(session_id:str=Cookie(None)):

    if not session_id:
        raise HTTPException(status_code=401, detail="Please log in first.")

    user_id = await verify_session(session_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")
        
    return user_id


@app.post("/chats")
async def show_chats(user_id:int=Depends(user_verification)):

    try:
        user_chats = await get_chats(user_id)
        
        return {
            "status": "success",
            "chats": user_chats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user chats, error \n{e}\n")


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




if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)