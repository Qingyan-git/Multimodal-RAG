import streamlit as st
import time
from PIL import Image
import fitz
import base64
from io import BytesIO
import requests

BASE_URL = "http://127.0.0.1:8000"
QUERY_URL = f"{BASE_URL}/query"
CHATS_URL = f"{BASE_URL}/chats"

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

# --- Initialize Session States ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_sources" not in st.session_state:
    st.session_state.current_sources = []
if "selected_chat_id" not in st.session_state:
    st.session_state.selected_chat_id = None
if "show_auth_modal" not in st.session_state:
    st.session_state.show_auth_modal = None

# 🟢 FIX: Store the requests.Session object in st.session_state so it persists across reruns
if "http_session" not in st.session_state:
    st.session_state.http_session = requests.Session()

is_logged_in = "session_id" in st.session_state.http_session.cookies.get_dict()

# --- SIDEBAR VIEW ---
with st.sidebar:
    # 🟢 UI Indicator Element to explicitly show the account status
    if is_logged_in:
        st.success("🟢 Status: Logged In")
    else:
        st.warning("🔴 Status: Guest / Signed Out")

    st.header("💬 Chats")
    
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.current_sources = []
        st.session_state.selected_chat_id = None
        st.rerun()
        
    st.divider()
    
    # Dynamic Chat History Thread Box
    try:
        # 🟢 FIX: Use the persistent session object
        chats_response = st.session_state.http_session.post(CHATS_URL, timeout=5)
        if chats_response.status_code == 200:
            chats_data = chats_response.json().get("chats", [])
            
            if chats_data:
                for chat in chats_data:
                    chat_id = chat.get("chat_id")
                    title = chat.get("title", f"Chat {chat_id}")
                    
                    is_active = st.session_state.selected_chat_id == chat_id
                    button_label = f"▶️ {title}" if is_active else title
                    
                    if st.button(button_label, key=f"chat_{chat_id}", use_container_width=True):
                        st.session_state.selected_chat_id = chat_id
                        
                        history_url = f"{CHATS_URL}/{chat_id}"
                        # 🟢 FIX: Use the persistent session object
                        history_response = st.session_state.http_session.post(history_url, timeout=5)
                        
                        if history_response.status_code == 200:
                            items = history_response.json().get("chat_items", [])
                            st.session_state.chat_history = [
                                {"role": item["role"], "content": item["content"]} 
                                for item in items
                            ]
                            st.session_state.current_sources = [] 
                            st.rerun()
                        else:
                            st.sidebar.error("Failed to load historical context thread.")
            else:
                st.caption("No previous chats found.")
        else:
            st.caption("🔒 Log in to view saved chat archives.")
            
    except Exception as e:
        st.sidebar.error(f"Debug Error: {e}")

    # Account Management Controls
    st.divider()
    st.subheader("🔐 Account")
    
    auth_col1, auth_col2 = st.columns(2)
    with auth_col1:
        if st.button("🔑 Login", use_container_width=True, disabled=is_logged_in):
            st.session_state.show_auth_modal = "login"
            st.rerun()
            
    with auth_col2:
        if is_logged_in:
            # Add a functional Logout helper button to clear the persistent cookies
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.http_session.cookies.clear()
                st.session_state.chat_history = []
                st.session_state.selected_chat_id = None
                st.session_state.current_sources = []
                st.success("Signed out safely!")
                time.sleep(1)
                st.rerun()
        else:
            if st.button("📝 Sign Up", use_container_width=True):
                st.session_state.show_auth_modal = "signup"
                st.rerun()


# --- POP-UP MODAL OVERLAYS ---
if st.session_state.show_auth_modal == "login":
    with st.form("login_form", clear_on_submit=True):
        st.write("### Account Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Submit Login", use_container_width=True):
                try:
                    # 🟢 FIX: Call login using the persistent state session context so cookies attach properly
                    login_res = st.session_state.http_session.post(
                        f"{BASE_URL}/login", 
                        json={"username": username, "password": password},
                        timeout=10
                    )
                    if login_res.status_code == 200:
                        st.success(f"Welcome back, {username}!")
                        st.session_state.show_auth_modal = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Login failed: {login_res.json().get('detail')}")
                except Exception as e:
                    st.error(f"Network connection error: {e}")
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_auth_modal = None
                st.rerun()

elif st.session_state.show_auth_modal == "signup":
    with st.form("signup_form", clear_on_submit=True):
        st.write("### Create New Account")
        new_username = st.text_input("Choose Username")
        new_password = st.text_input("Choose Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Register", use_container_width=True):
                try:
                    signup_res = requests.post(
                        f"{BASE_URL}/signup", 
                        json={"username": new_username, "password": new_password},
                        timeout=10
                    )
                    if signup_res.status_code == 200:
                        st.success("Account created successfully!")
                        st.session_state.show_auth_modal = "login" 
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Registration failed: {signup_res.json().get('detail')}")
                except Exception as e:
                    st.error(f"Network connection error: {e}")
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_auth_modal = None
                st.rerun()


# --- SPLIT BODY INTERFACE WINDOWS ---
left, right = st.columns([1, 1])

# Left Column: Multimodal Context Viewer 
with left:
    if st.session_state.current_sources:
        sources = st.session_state.current_sources
        
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
                            b64_data = current_page["image_base64"]
                            if "," in b64_data:
                                b64_data = b64_data.split(",")[1]
                                
                            img_data = base64.b64decode(b64_data)
                            pil_img = Image.open(BytesIO(img_data))
                            st.image(pil_img, use_container_width=True)
    else:
        st.info("👋 Welcome to ChatPDF!")
        st.markdown("""
        ### How to get started:
        1. Select an archive conversation path from the **Chats** history panel.
        2. Click **➕ New Chat** inside your sidebar to start fresh.
        3. Enter a question on the right panel to extract real-time image contexts.
        """)

# Right Column: Main Chat Room Interface
with right: 
    chat_container = st.container()
    
    # Block input if not authenticated yet to align gracefully with validation
    if not is_logged_in:
        st.chat_input("Please log in first to chat...", disabled=True)
    else:
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
                            # 🟢 FIX: Notice the payload schema shift from 'text' back to 'question' to line up accurately with your QueryRequest model!
                            payload = {
                                "question": user_input,
                                "chat_id": st.session_state.selected_chat_id or "PLACEHOLDER"
                            }
                            
                            # 🟢 FIX: Run the pipeline request inside the active, cookie-bearing state session context
                            response = st.session_state.http_session.post(QUERY_URL, json=payload, timeout=300)
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
                            st.error(f"Pipeline Query request failed: {e}")