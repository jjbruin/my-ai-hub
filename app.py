import streamlit as st
import hmac, smtplib, pandas as pd
from openai import OpenAI
from tavily import TavilyClient
from PyPDF2 import PdfReader
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. SECURITY & UTILS ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔐 Secure Access Required")
    pwd = st.text_input("Enter Hub Password", type="password")
    if pwd == st.secrets["APP_PASSWORD"]:
        st.session_state["password_correct"] = True
        st.rerun()
    return False

def extract_text(file):
    ext = file.name.split('.')[-1].lower()
    if ext == 'pdf': return " ".join([p.extract_text() for p in PdfReader(file).pages])
    if ext == 'docx': return " ".join([p.text for p in Document(file).paragraphs])
    if ext == 'csv': return pd.read_csv(file).to_string()
    return ""

def send_report(text, subject):
    msg = MIMEMultipart(); msg['Subject'] = f"AI Research: {subject}"
    msg['From'] = st.secrets["EMAIL_SENDER"]; msg['To'] = st.secrets["EMAIL_SENDER"]
    msg.attach(MIMEText(text, 'plain'))
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_APP_PASSWORD"])
        server.send_message(msg)

# --- 2. MAIN APP ---
if check_password():
    st.set_page_config(page_title="AI Intelligence Hub", layout="wide")
    if "history" not in st.session_state: st.session_state.history = []

    with st.sidebar:
        st.title("📜 History")
        for i, h in enumerate(st.session_state.history):
            if st.button(f"{i+1}. {h['q'][:20]}..."): st.session_state.view = h

    st.title("⚖️ Private AI Intelligence Hub")
    up_file = st.file_uploader("Upload internal data (PDF, CSV, DOCX)", type=['pdf', 'csv', 'docx'])
    query = st.chat_input("Analyze data or search the world...")

    if query:
        ai = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_KEY"])
        tv = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        doc_txt = extract_text(up_file) if up_file else "No document provided."

        with st.status("Gathering Intelligence...", expanded=True):
            web = "\n".join([r['content'] for r in tv.search(query, search_depth="advanced")['results']])
            experts = ["anthropic/claude-3.5-sonnet", "openai/gpt-5-preview"]
            answers = [ai.chat.completions.create(model=m, messages=[{"role": "user", "content": f"Doc: {doc_txt}\nWeb: {web}\nQ: {query}"}]).choices[0].message.content for m in experts]
            
            # Comparison Table Logic
            table_p = f"Create a Markdown table comparing these two AI outputs on accuracy and depth: {answers}"
            table_res = ai.chat.completions.create(model="google/gemini-2.0-pro", messages=[{"role": "user", "content": table_p}])
            
            final = ai.chat.completions.create(model="google/gemini-2.0-pro", messages=[{"role": "user", "content": f"Final Report: {answers}"}])
            
            res_obj = {"q": query, "report": final.choices[0].message.content, "table": table_res.choices[0].message.content}
            st.session_state.history.append(res_obj); st.session_state.view = res_obj

    if "view" in st.session_state:
        v = st.session_state.view
        st.subheader("Comparison Table")
        st.markdown(v['table'])
        st.subheader("Verified Final Report")
        st.markdown(v['report'])
        if st.button("📧 Email Report"):
            send_report(v['report'], v['q'])
            st.success("Sent!")
