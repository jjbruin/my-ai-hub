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
    except Exception as e: return f"Error: {e}"
    return ""

# --- 2. MAIN HUB ---
if check_password():
    st.set_page_config(page_title="AI Intelligence Hub", layout="wide")
    if "history" not in st.session_state: st.session_state.history = []

    with st.sidebar:
        st.success(f"User: {st.session_state['user']}")
        for i, h in enumerate(st.session_state.history):
            if st.button(f"{h['q'][:20]}...", key=f"h_{i}"): st.session_state.view = h

    st.title("⚖️ Private AI Intelligence Hub")
    up_file = st.file_uploader("Upload files", type=['pdf', 'csv', 'docx'])
    query = st.chat_input("Ask anything...")

    if query:
        ai = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86OGQ1ZTE4YWMyMjEwMjZlYzdmZWE3YWVhMzZmYTc2ZTM6NzozZDBmOmRmYjQ1YWQxN2NhZjA5MGM4NTA1YzE5NTYxYzg0ZTVhNDAwNjM3ODlhYjhjMGJkYjg4M2FiMzU3MTBmYjRkMjg6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        doc = extract_text(up_file) if up_file else "None."

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. Search
            try:
                res = tv.search(query, search_depth="advanced")
                web = "\n".join([r['content'] for r in res.get('results', [])])
            except: web = "Search error."

            # B. Experts (Shortened to 1500 characters)
            st.write("🤖 Consulting Experts...")
            prompt = f"Doc: {doc[:1500]}\nWeb: {web[:1500]}\nQ: {query}"
            answers = []
            for m in ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]:
                try:
                    r = ai.chat.completions.create(model=m, messages=[{"role": "user", "content": prompt}])
                    answers.append(r.choices[0].message.content)
                except Exception as e: answers.append(f"Model failed: {e}")
            
            # C. Final Synthesis (Crucial: Drastically shortened to avoid CloudFront errors)
            st.write("⚖️ Finalizing Audit...")
            try:
                # We only send the first 800 characters of each expert answer to the judge
                judge_input = "\n\n".join([f"Expert {i+1}: {a[:800]}" for i, a in enumerate(answers)])
                final = ai.chat.completions.create(
                    model="google/gemini-2.0-flash-exp",
                    messages=[{"role": "user", "content": f"Briefly summarize these views into a report:\n{judge_input}"}]
                )
                res_obj = {"q": query, "report": final.choices[0].message.content}
                st.session_state.history.append(res_obj); st.session_state.view = res_obj
                status.update(label="✅ Complete", state="complete")
            except Exception as e: st.error(f"Network limit reached. Try a shorter question.")

    if "view" in st.session_state:
        st.divider()
        st.markdown(f"### Results: {st.session_state.view['q']}")
        st.markdown(st.session_state.view['report'])

