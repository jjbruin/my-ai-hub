import streamlit as st
import hmac, smtplib, pandas as pd
from openai import OpenAI
from tavily import TavilyClient
from PyPDF2 import PdfReader
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- DIAGNOSIS: Remove this line once the app works --- st.sidebar.write("System Keys Found:", list(st.secrets.keys()))

# --- 1. SECURITY: MULTI-USER LOGIN ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔐 Secure Intelligence Hub Login")
    user_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    if st.button("Login"):
        user_db = st.secrets.get("passwords", {})
        if user_input in user_db and hmac.compare_digest(password_input, user_db[user_input]):
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = user_input
            st.rerun()
        else:
            st.error("😕 Invalid username or password")
    return False

# --- 2. UTILITIES ---
def extract_text(file):
    try:
        ext = file.name.split('.')[-1].lower()
        if ext == 'pdf': return " ".join([p.extract_text() for p in PdfReader(file).pages])
        if ext == 'docx': return " ".join([p.text for p in Document(file).paragraphs])
        if ext == 'csv': return pd.read_csv(file).to_string()
    except Exception as e: return f"Error: {str(e)}"
    return ""

def send_report(text, subject):
    try:
        msg = MIMEMultipart(); msg['Subject'] = f"AI Research: {subject}"
        msg['From'] = st.secrets["EMAIL_SENDER"]; msg['To'] = st.secrets["EMAIL_SENDER"]
        msg.attach(MIMEText(text, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls(); server.login(st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_APP_PASSWORD"])
            server.send_message(msg)
        st.success("Sent!")
    except Exception as e: st.error(f"Failed: {e}")

# --- 3. MAIN APP ---
if check_password():
    st.set_page_config(page_title="AI Intelligence Hub", layout="wide")
    if "history" not in st.session_state: st.session_state.history = []

    with st.sidebar:
        st.success(f"User: {st.session_state['current_user']}")
        st.header("📜 History")
        for i, h in enumerate(st.session_state.history):
            if st.button(f"{i+1}. {h['q'][:20]}...", key=f"h_{i}"): st.session_state.view = h

    st.title("⚖️ Private AI Intelligence Hub")
    up_file = st.file_uploader("Upload files", type=['pdf', 'csv', 'docx'])
    query = st.chat_input("Ask anything...")

    if query:
        ai = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86N2NmYmQzNjk0ZjFkOTFkMmU1OGI4YjA5NmI5NmE3OGY6NzozMGE2OjRjYTQ1MDE5MzQzYWIzNGZjY2M0NmI1NmNlZDljMDIxN2I4NzJkNDRkNzAxMWRjZDFhYmQ3NzIyMjllM2NlM2I6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        doc_txt = extract_text(up_file) if up_file else "None."

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. Web Search
            try:
                search_res = tv.search(query, search_depth="advanced")
                web = "\n".join([r['content'] for r in search_res.get('results', [])])
            except: web = "Web search unavailable."

            # B. Experts (Limited to 2000 chars to prevent CloudFront 403 errors)
            st.write("🤖 Consulting Experts...")
            experts = ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"] # Using mini to test stability
            answers = []
            prompt = f"Doc: {doc_txt[:2000]}\nWeb: {web[:2000]}\nQ: {query}"
            
            for m in experts:
                try:
                    res = ai.chat.completions.create(model=m, messages=[{"role": "user", "content": prompt}])
                    answers.append(res.choices[0].message.content)
                except Exception as e: answers.append(f"Expert {m} failed: {e}")
            
            # C. Final Judge (Forced small prompt to bypass CloudFront)
            st.write("⚖️ Finalizing...")
            try:
                summary = "\n\n".join([f"Expert {i+1}: {ans[:1000]}" for i, ans in enumerate(answers)])
                final_res = ai.chat.completions.create(
                    model="google/gemini-2.0-flash-exp", # Using faster Flash model
                    messages=[{"role": "user", "content": f"Compare these views and give a final report:\n{summary}"}]
                )
                res_obj = {"q": query, "report": final_res.choices[0].message.content}
                st.session_state.history.append(res_obj); st.session_state.view = res_obj
                status.update(label="✅ Analysis Complete", state="complete")
            except Exception as e: st.error(f"Synthesis failed: {e}")

    if "view" in st.session_state:
        v = st.session_state.view
        st.divider()
        if st.button("📧 Email Report"): send_report(v['report'], v['q'])
        st.markdown(v['report'])
