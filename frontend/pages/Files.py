import streamlit as st
import pandas as pd
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
DOCUMENTS_URL = f"{BASE_URL}/documents"
UPLOAD_URL = f"{BASE_URL}/upload"

st.title("Supabase Document Management")

# 🟢 Fetch live list from FastAPI backend
table_data = []
try:
    res = requests.get(DOCUMENTS_URL, timeout=10)
    if res.status_code == 200:
        docs = res.json().get("documents", [])
        for doc in docs:
            # Format size into Megabytes
            size_mb = doc["size_bytes"] / (1024 * 1024)
            
            # Format Supabase ISO string (e.g., 2026-06-17T07:38:21Z) to clean viewing string
            try:
                dt = datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00"))
                formatted_date = dt.strftime("%b %d, %Y %H:%M")
            except Exception:
                formatted_date = doc["created_at"]

            table_data.append({
                "Document Name": doc["name"],
                "File Size": f"{round(size_mb, 2)} MB",
                "Date Created": formatted_date,
                "Status": "✅"
            })
    else:
        st.error("Failed to load documents from server database storage.")
except Exception as e:
    st.error(f"Error connecting to backend: {e}")

# Build DataFrame
df = pd.DataFrame(table_data)

if not df.empty:
    st.dataframe(
        df, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "Document Name": st.column_config.TextColumn(width="large"),
            "Status": st.column_config.TextColumn(width="small")
        }
    )
else:
    st.info("No documents found in cloud storage.")

# Upload form logic
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
            response = requests.post(UPLOAD_URL, files=files_payload, timeout=15)

            if response.status_code == 200:
                st.toast(f"Uploaded {uploaded_file.name} successfully")
            else:
                st.error(f"Upload failed: {response.text}")
        except Exception as e:
            st.error(f"Upload failed: {e}")
            
    # Trigger interface refresh to reflect new storage updates
    st.rerun()










# import streamlit as st
# import os 
# import time 
# import pandas as pd
# import requests

# BASE_URL = "http://127.0.0.1:8000"
# UPLOAD_URL = f"{BASE_URL}/upload"

# STORAGE_DIR = r"C:\Users\UserAdmin\Documents\Multimodal-RAG\pdfs"
# os.makedirs(STORAGE_DIR, exist_ok=True)

# if os.path.exists(STORAGE_DIR):
#     all_files = [f for f in os.listdir(STORAGE_DIR)]
# else:
#     all_files = []

# table_data = []
# for filename in all_files:
#     full_path = os.path.join(STORAGE_DIR, filename)
#     full_size_mb = os.path.getsize(full_path) / (1024*1024)
#     last_modified = time.ctime(os.path.getmtime(full_path))

#     table_data.append({
#         "Document Name": filename,
#         "File Size": f"{round(full_size_mb, 2)} MB",
#         "Date": last_modified,
#         "Status": "✅"
#     })

# df = pd.DataFrame(table_data)

# st.dataframe(
#     df, 
#     use_container_width=True,
#     hide_index=True,
#     column_config={
#         "Document Name": st.column_config.TextColumn(width="large"),
#         "Status": st.column_config.TextColumn(width="small")
#     }
# )

# with st.form("upload_form", clear_on_submit=True):
#     uploaded_files = st.file_uploader(
#         "Drag and drop your PDF files here", 
#         type=["pdf"], 
#         accept_multiple_files=True
#     )
#     submit_button = st.form_submit_button("Upload", use_container_width=True)

# if submit_button and uploaded_files:
#     for uploaded_file in uploaded_files:
#         try: 
#             file_bytes = uploaded_file.getvalue()
#             files_payload = {"file": (uploaded_file.name, file_bytes, "application/pdf")}
#             response = requests.post(UPLOAD_URL, files=files_payload, timeout=10)

#             if response.status_code == 200:
#                 st.toast(f"Upload successful")
#             else:
#                 st.error(f"Upload failed: {response.text}")
#         except Exception as e:
#             st.error(f"Upload failed: {e}")

# st.rerun()