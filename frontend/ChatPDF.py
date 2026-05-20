import streamlit as st
import time
from PIL import Image
import fitz

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

left, right = st.columns(2)

with left:
    st.image(render_pdf_page("frontend\sample.pdf", 1), use_container_width=True)

with right: 
    query = st.text_input("Ask a question across all uploaded policies:", placeholder="Ask anything")