import streamlit as st
import pandas as pd
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
DOCUMENTS_URL = f"{BASE_URL}/documents"
UPLOAD_URL = f"{BASE_URL}/upload"

st.set_page_config(page_title="Documents Manager", layout="wide")
st.title("Documents")

# Initialize a persistent session in Streamlit state if it doesn't exist
if "http_session" not in st.session_state:
    st.session_state.http_session = requests.Session()

# 📥 Initialize a temporary download buffer state to handle on-demand downloads safely
if "download_buffer" not in st.session_state:
    st.session_state.download_buffer = None

docs = []
connection_success = False

# 🟢 Fetch live list from FastAPI backend using POST
try:
    res = st.session_state.http_session.post(DOCUMENTS_URL, timeout=10)
    
    if res.status_code == 200:
        connection_success = True
        docs = res.json().get("documents", [])
    elif res.status_code == 401:
        st.warning("Please log in first to view documents.")
    else:
        st.error(f"Failed to load documents from server database storage. (Status Code: {res.status_code})")
        
except Exception as e:
    st.error(f"Error connecting to backend: {e}")

# 🔵 Render Data Section
if connection_success:
    if docs:
        st.write("### 📂 Available Documents")
        
        # 🟢 Layout Columns: Name, Upload Date, Size, Action Button
        col_header1, col_header2, col_header3, col_header4 = st.columns([3, 2, 1, 1.5])
        with col_header1:
            st.markdown("**Document Name**")
        with col_header2:
            st.markdown("**Uploaded At**")
        with col_header3:
            st.markdown("**Size**")
        with col_header4:
            st.markdown("**Action**")
        st.markdown("---")
        
        # Dynamic Row Generation
        for idx, doc in enumerate(docs):
            document_name = doc.get("name", "Unknown Document")
            
            # 🟢 Format the timestamp cleanly
            raw_date = doc.get("created_at")
            if raw_date:
                try:
                    dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    formatted_date = dt.strftime("%d %b %Y, %H:%M")
                except Exception:
                    formatted_date = str(raw_date)[:16]
            else:
                formatted_date = "—"
                
            # 🟢 Format raw bytes into human-readable MB or KB
            raw_size = doc.get("filesize")
            if raw_size is not None:
                if raw_size >= 1024 * 1024:
                    formatted_size = f"{raw_size / (1024 * 1024):.2f} MB"
                else:
                    formatted_size = f"{raw_size / 1024:.1f} KB"
            else:
                formatted_size = "—"
            
            # 🟢 Render updated columns layout per document
            row_col1, row_col2, row_col3, row_col4 = st.columns([3, 2, 1, 1.5])
            with row_col1:
                st.write(f"📄 {document_name}")
            with row_col2:
                st.caption(formatted_date)
            with row_col3:
                st.caption(formatted_size)
            with row_col4:
                # 1. Fetch file bytes into state memory upon button interaction
                if st.button("📥 Download", key=f"fetch_{idx}", use_container_width=True):
                    with st.spinner("Downloading..."):
                        try:
                            download_url = f"{BASE_URL}/documents/download/{document_name}"
                            dl_res = st.session_state.http_session.post(download_url, timeout=30)
                            
                            if dl_res.status_code == 200:
                                # Save the data cleanly into Streamlit's state memory
                                st.session_state.download_buffer = {
                                    "name": document_name,
                                    "bytes": dl_res.content
                                }
                                st.rerun()
                            else:
                                st.error(f"Download failed: {dl_res.text}")
                        except Exception as e:
                            st.error(f"Error connecting to download route: {e}")

        # 2. 🟢 If data exists in the buffer, render hidden native button and click it instantly via DOM
        if st.session_state.download_buffer:
            # Render a structural wrapper containing our auto-trigger mechanism
            with st.container():
                st.download_button(
                    label="Processing...",
                    data=st.session_state.download_buffer["bytes"],
                    file_name=st.session_state.download_buffer["name"],
                    mime="application/pdf",
                    key="auto_trigger_download_btn"
                )
                
                # Native, safe JavaScript snippet executed directly on the main page DOM (avoids iframe sandbox)
                st.components.v1.html(
                    """
                    <script>
                        // Target all parent buttons rendered on the main page canvas
                        const buttons = window.parent.document.querySelectorAll("button");
                        for (const button of buttons) {
                            if (button.innerText.includes("Processing...")) {
                                button.click();
                                break;
                            }
                        }
                    </script>
                    """,
                    height=0,
                    width=0
                )
            
            # Flush the memory state immediately to block automated loop recursion re-downloads
            st.session_state.download_buffer = None
    else:
        st.info("No documents found in cloud storage.")

# --- Separator ---
st.markdown("---")

# 🟡 Upload form logic
with st.form("upload_form", clear_on_submit=True):
    uploaded_files = st.file_uploader(
        "Drag and drop your PDF files here", 
        type=["pdf"], 
        accept_multiple_files=True
    )
    submit_button = st.form_submit_button("Upload Documents", use_container_width=True)

if submit_button and uploaded_files:
    upload_occurred = False
    
    for uploaded_file in uploaded_files:
        try: 
            file_bytes = uploaded_file.getvalue()
            files_payload = {"file": (uploaded_file.name, file_bytes, "application/pdf")}
            response = st.session_state.http_session.post(UPLOAD_URL, files=files_payload, timeout=15)

            if response.status_code == 200:
                st.toast(f"Uploaded {uploaded_file.name} successfully!")
                upload_occurred = True
            elif response.status_code == 401:
                # 🛑 Catching the 401 Unauthorized block from FastAPI dependencies
                st.error("🔒 Unauthorized: Please log in first to upload documents.")
                break  # Halt further file processing iterations if unauthorized
            else:
                st.error(f"Upload failed for {uploaded_file.name}: {response.text}")
                
        except Exception as e:
            st.error(f"Upload failed: {e}")
            
    # Only refresh the UI state if at least one upload completed successfully
    if upload_occurred:
        st.rerun()