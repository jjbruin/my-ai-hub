import streamlit as st
import hmac, smtplib, pandas as pd
from openai import OpenAI
from tavily import TavilyClient
from PyPDF2 import PdfReader
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. SECURITY ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔐 Intelligence Hub Login")
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login"):
        db = st.secrets.get("passwords", {})
        if u in db and hmac.compare_digest(p, db[u]):
            st.session_state["password_correct"], st.session_state["user"] = True, u
            st.rerun()
        else: st.error("Invalid Login")
    return False

def extract_text(file):
    try:
        ext = file.name.split('.')[-1].lower()
        if ext == 'pdf': return " ".join([p.extract_text() for p in PdfReader(file).pages])
        if ext == 'docx': return " ".join([p.text for p in Document(file).paragraphs])
        if ext == 'csv': return pd.read_csv(file).to_string()
    except: return "Error reading file."
    return ""

# --- 2. MAIN HUB ---
if check_password():
    st.set_page_config(page_title="AI Intelligence Hub", layout="wide")
    if "history" not in st.session_state: st.session_state.history = []

    st.title("⚖️ Private AI Intelligence Hub")
    up_file = st.file_uploader("Upload files", type=['pdf', 'csv', 'docx'])
    query = st.chat_input("Ask about the Eagles vs 49ers...")

    if query:
        ai = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86ZTA4MGU0NmJlNGE3ZDcxMDE0NmY3YWVhOWJmMGI3NjA6NzpkMjJiOjkwMDg5NTg1NDY3MGY2YTY3ODY0NWVmOGM1MDRkOGQzNGMyOTcwMzNlYzg3MjQ4NzZlMGU1MjY3ZTczZjFmM2Y6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        doc = extract_text(up_file) if up_file else "None."

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. Search (CRITICAL FIX: Limit to only 2 results to keep packet small)
            try:
                res = tv.search(query, search_depth="basic", max_results=2)
                web = "\n".join([r['content'][:500] for r in res.get('results', [])])
            except: web = "Search error."

            # B. Experts (Drastic Truncation to bypass CloudFront)
            st.write("🤖 Consulting Experts...")
            prompt = f"Data: {web}\n\nQuestion: {query}"
            answers = []
            for m in ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]:
                try:
                    r = ai.chat.completions.create(model=m, messages=[{"role": "user", "content": prompt[:1000]}])
                    answers.append(r.choices[0].message.content)
                except: answers.append("Expert unavailable.")
            
            # C. Final Synthesis
            st.write("⚖️ Finalizing Audit...")
            try:
                judge_input = "\n".join([a[:500] for a in answers])
                final = ai.chat.completions.create(
                    model="google/gemini-2.0-flash-exp",
                    messages=[{"role": "user", "content": f"Summarize these findings: {judge_input}"}]
                )
                res_obj = {"q": query, "report": final.choices[0].message.content}
                st.session_state.history.append(res_obj); st.session_state.view = res_obj
                status.update(label="✅ Complete", state="complete")
            except: st.error("Network limit reached. Try a more specific question.")

    if "view" in st.session_state:
        st.divider()
        st.markdown(st.session_state.view['report'])
