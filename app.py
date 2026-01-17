import streamlit as st
import hmac, smtplib, pandas as pd
from openai import OpenAI
from tavily import TavilyClient
from PyPDF2 import PdfReader
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.write("Available Keys:, list(st.secrets.keys()))

# --- 1. SECURITY: MULTI-USER LOGIN ---
def check_password():
    """Returns True if the user provides a valid username and password."""
    if st.session_state.get("password_correct", False):
        return True

    st.title("🔐 Secure Intelligence Hub Login")
    user_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        # Access the [passwords] section from your Streamlit Secrets
        user_db = st.secrets.get("passwords", {})
        
        if user_input in user_db and hmac.compare_digest(password_input, user_db[user_input]):
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = user_input
            st.rerun()
        else:
            st.error("😕 Invalid username or password")
    return False

# --- 2. DATA EXTRACTION UTILITIES ---
def extract_text(file):
    try:
        ext = file.name.split('.')[-1].lower()
        if ext == 'pdf': return " ".join([p.extract_text() for p in PdfReader(file).pages])
        if ext == 'docx': return " ".join([p.text for p in Document(file).paragraphs])
        if ext == 'csv': return pd.read_csv(file).to_string()
    except Exception as e:
        return f"Error reading document: {str(e)}"
    return ""

def send_report(text, subject):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"AI Research Report: {subject}"
        msg['From'] = st.secrets["EMAIL_SENDER"]
        msg['To'] = st.secrets["EMAIL_SENDER"]
        msg.attach(MIMEText(text, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_APP_PASSWORD"])
            server.send_message(msg)
        st.success("Report emailed to your inbox!")
    except Exception as e:
        st.error(f"Email failed: {e}")

# --- 3. MAIN APPLICATION INTERFACE ---
if check_password():
    st.set_page_config(page_title="AI Intelligence Hub", layout="wide")
    
    # Session state for History
    if "history" not in st.session_state:
        st.session_state.history = []

    # Sidebar: User Info and History
    with st.sidebar:
        st.success(f"User: {st.session_state['current_user']}")
        st.divider()
        st.header("📜 Research History")
        for i, h in enumerate(st.session_state.history):
            if st.button(f"{i+1}. {h['q'][:25]}...", key=f"h_{i}"):
                st.session_state.view = h

    st.title("⚖️ Private AI Intelligence Hub")
    
    # Inputs
    up_file = st.file_uploader("Upload private files (PDF, CSV, DOCX)", type=['pdf', 'csv', 'docx'])
    query = st.chat_input("Analyze your data or perform deep web research...")

    if query:
        # Initialize API Clients
        ai = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86ZmVkMGU4YThjNmUxMjQ0ODNmZjJiMjNkMWY3ZTNkOGQ6Nzo4ZThhOmFmMzA3YWQ4YTkzMDIzZjUxMTZlYzE0NWRiM2Q0ZTZiNGZiOTEwYTQxYjk1NDY1ZDQ2NjI2NzcyNWYwNDhlYmM6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        
        # Safe extraction of uploaded file
        doc_txt = extract_text(up_file) if up_file else "No private document provided."

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. Web Search
            st.write("🔎 Performing live web audit...")
            try:
                search_res = tv.search(query, search_depth="advanced")
                web = "\n".join([r['content'] for r in search_res.get('results', [])])
                if not web: web = "No relevant web results found."
            except:
                web = "Web search unavailable."

            # B. Expert Consultation (Truncated to avoid BadRequest errors)
            st.write("🤖 Consulting Board of Experts...")
            experts = ["anthropic/claude-3.5-sonnet", "openai/gpt-5-preview"]
            answers = []
            # Truncate inputs to 2500 chars each to keep the packet size small
            p_content = f"Doc Snippet: {doc_txt[:2500]}\n\nWeb Facts: {web[:2500]}\n\nQuestion: {query}"
            
            for m in experts:
                try:
                    res = ai.chat.completions.create(
                        model=m,
                        messages=[{"role": "user", "content": p_content}]
                    )
                    answers.append(res.choices[0].message.content)
                except Exception as e:
                    answers.append(f"Expert {m} unavailable: {str(e)}")
            
            # C. Final Synthesis (Consolidated to avoid CloudFront errors)
            st.write("⚖️ Finalizing Consensus Audit...")
            try:
                # Combine experts into a summary for the judge
                exp_summary = "\n\n".join([f"Expert {i+1} View: {ans[:1500]}" for i, ans in enumerate(answers)])
                master_prompt = f"Create a Markdown comparison table and a unified report based on these expert views: {exp_summary}"
                
                final_res = ai.chat.completions.create(
                    model="google/gemini-2.0-pro",
                    messages=[{"role": "user", "content": master_prompt}]
                )
                
                report_data = final_res.choices[0].message.content
                res_obj = {"q": query, "report": report_data}
                
                # Update Session
                st.session_state.history.append(res_obj)
                st.session_state.view = res_obj
                status.update(label="✅ Analysis Complete", state="complete")
            except Exception as e:
                st.error(f"Final synthesis failed: {e}")

    # --- 4. DISPLAY RESULTS ---
    if "view" in st.session_state:
        v = st.session_state.view
        st.divider()
        
        # Layout for Report and Actions
        col_main, col_act = st.columns([4, 1])
        with col_main:
            st.subheader(f"Results: {v['q']}")
            st.markdown(v['report'])
        
        with col_act:
            st.write("Actions")
            if st.button("📧 Email Report"):
                send_report(v['report'], v['q'])
            if st.button("🗑️ Clear View"):
                del st.session_state.view
                st.rerun()

