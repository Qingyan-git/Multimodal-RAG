import streamlit as st
import os 
import time 
import pandas as pd
import requests

BASE_URL = "http://127.0.0.1:8000"
UPLOAD_URL = f"{BASE_URL}/upload"

STORAGE_DIR = r"C:\Users\UserAdmin\Documents\Multimodal-RAG\pdfs"
os.makedirs(STORAGE_DIR, exist_ok=True)

if os.path.exists(STORAGE_DIR):
    all_files = [f for f in os.listdir(STORAGE_DIR)]
else:
    all_files = []

table_data = []
for filename in all_files:
    full_path = os.path.join(STORAGE_DIR, filename)
    full_size_mb = os.path.getsize(full_path) / (1024*1024)
    last_modified = time.ctime(os.path.getmtime(full_path))

    table_data.append({
        "Document Name": filename,
        "File Size": f"{round(full_size_mb, 2)} MB",
        "Date": last_modified,
        "Status": "✅"
    })

df = pd.DataFrame(table_data)

st.dataframe(
    df, 
    use_container_width=True,
    hide_index=True,
    column_config={
        "Document Name": st.column_config.TextColumn(width="large"),
        "Status": st.column_config.TextColumn(width="small")
    }
)

with st.form("upload_form", clear_on_submit=True):
    uploaded_files = st.file_uploader(
        "Drag and drop your PDF files here", 
        type=["pdf"], 
        accept_multiple_files=True
    )
    submit_button = st.form_submit_button("Upload", use_container_width=True)

if submit_button and uploaded_files:
    for uploaded_file in uploaded_files:
        try: 
            file_bytes = uploaded_file.getvalue()
            files_payload = {"file": (uploaded_file.name, file_bytes, "application/pdf")}
            response = requests.post(UPLOAD_URL, files=files_payload, timeout=10)

            if response.status_code == 200:
                st.toast(f"Upload successful")
            else:
                st.error(f"Upload failed: {response.text}")
        except Exception as e:
            st.error(f"Upload failed: {e}")

st.rerun()