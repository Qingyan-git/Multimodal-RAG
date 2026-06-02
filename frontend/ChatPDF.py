import streamlit as st
import time
from PIL import Image
import fitz
import base64
from io import BytesIO
import requests

BASE_URL = "http://127.0.0.1:8000"
QUERY_URL = f"{BASE_URL}/query"

def render_pdf_page(pdf_path, page_num):
    try: 
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap(dpi=100)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img 
    except Exception as e:
        st.error(f"Error loading PDF page: {e}")
        return None 

st.set_page_config(page_title="ChatPDF", layout="wide")
st.title("ChatPDF")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_sources" not in st.session_state:
    st.session_state.current_sources = []

left, right = st.columns([1, 1])

with left:
    if st.session_state.current_sources:
        sources = st.session_state.current_sources
        
        # group by pdf name 
        grouped_docs = {}
        for src in sources:
            pdf_name = src.get("pdf_name", "Unknown Document")
            if pdf_name not in grouped_docs:
                grouped_docs[pdf_name] = []
            grouped_docs[pdf_name].append(src)

        for pdf_name, pages in grouped_docs.items():
            with st.expander(f"{pdf_name}", expanded=True):
                page_tab_titles = [f"Page {p['page_num']}" for p in pages]
                page_tabs = st.tabs(page_tab_titles)

                for idx, page_tab in enumerate(page_tabs):
                    with page_tab:
                        current_page = pages[idx]
                        if current_page.get("image_base64"):
                            img_data = base64.b64decode(current_page["image_base64"])
                            pil_img = Image.open(BytesIO(img_data))
                            st.image(pil_img, use_container_width=True)
    else:
        st.image(render_pdf_page("frontend\sample.pdf", 1), use_container_width=True)

with right: 
    chat_container = st.container()

    user_input = st.chat_input("Ask anything")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        if user_input:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try: 
                        response = requests.post(QUERY_URL, json={"text": user_input}, timeout=30)
                        if response.status_code == 200:
                            data = response.json()
                            answer = data["answer"]
                            sources = data.get("sources", [])

                            st.markdown(answer)

                            st.session_state.chat_history.append({"role": "assistant", "content": answer})
                            st.session_state.current_sources = sources

                            st.rerun()
                        else:
                            st.error(f"Error {response.status_code}: {response.text}")
                    except Exception as e:
                        st.error(e)