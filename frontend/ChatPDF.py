import streamlit as st
import time
from PIL import Image
import fitz
import base64
from io import BytesIO

FASTAPI_URL = "http://127.0.0"

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
    query = st.text_input("Ask a question across all uploaded policies:", placeholder="Ask anything")