import streamlit as st
import hmac, smtplib, pandas as pd
from openai import OpenAI
from tavily import TavilyClient
from PyPDF2 import PdfReader
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. SECURITY & UTILITIES ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔐 Secure Access Required")
    pwd = st.text_input("Enter Hub Password", type="password")
    if pwd == st.secrets["APP_PASSWORD"]:
        st.session_state["password_correct"] = True
        st.rerun()
    return False

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
        msg['Subject'] = f"AI Research: {subject}"
        msg['From'] = st.secrets["EMAIL_SENDER"]
        msg['To'] = st.secrets["EMAIL_SENDER"]
        msg.attach(MIMEText(text, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_APP_PASSWORD"])
            server.send_message(msg)
        st.success("Report emailed successfully!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# --- 2. MAIN HUB APPLICATION ---
if check_password():
    st.set_page_config(page_title="AI Intelligence Hub", layout="wide")
    
    # Initialize session history
    if "history" not in st.session_state: 
        st.session_state.history = []

    # Sidebar for previous research
    with st.sidebar:
        st.title("📜 Research History")
        for i, h in enumerate(st.session_state.history):
            if st.button(f"{i+1}. {h['q'][:20]}...", key=f"hist_{i}"): 
                st.session_state.view = h

    st.title("⚖️ Private AI Intelligence Hub")
    st.info("Upload documents or ask a question. The Board will verify facts against the web.")
    
    up_file = st.file_uploader("Upload internal data (PDF, CSV, DOCX)", type=['pdf', 'csv', 'docx'])
    query = st.chat_input("Analyze data or search the world...")

    if query:
        # Initialize clients with keys from Secrets
        ai = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86MjEwYmMyM2JhN2I4MmMzOWUyM2VkYWEzZTRlNmM3ZDc6NzplMjQ3OmMzN2YzMDRjY2JlMmRkMGVjNmNkNTEyMzJmNzczMTMzZmIxZWRhNWM5MzI0M2IwY2IwOWYyNjJjYTgyNTNiMDk6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        
        # 1. Process document
        doc_txt = extract_text(up_file) if up_file else "No private document provided."

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # 2. Search the web
            st.write("🔎 Performing web research...")
            try:
                search_res = tv.search(query, search_depth="advanced")
                web = "\n".join([r['content'] for r in search_res.get('results', [])])
                if not web: web = "No relevant web results found."
            except Exception:
                web = "Web search unavailable."

            # 3. Consult Experts (with character limits to avoid BadRequest)
            st.write("🤖 Consulting Expert Models...")
            experts = ["anthropic/claude-3.5-sonnet", "openai/gpt-5-preview"]
            answers = []
            
            # Use truncated text (first 3000 chars) to prevent API errors
            prompt_content = f"Document Snippet: {doc_txt[:3000]}\n\nWeb Facts: {web[:3000]}\n\nQuestion: {query}"
            
            for m in experts:
                try:
                    res = ai.chat.completions.create(
                        model=m,
                        messages=[{"role": "user", "content": prompt_content}]
                    )
                    answers.append(res.choices[0].message.content)
                except Exception as e:
                    answers.append(f"Model {m} failed: {str(e)}")
            
            # 4. Final Audit & Comparison Table
            st.write("⚖️ Finalizing Verified Report...")
            try:
                # Generate Comparison Table
                table_p = f"Create a Markdown table comparing the different perspectives provided: {answers}"
                table_res = ai.chat.completions.create(model="google/gemini-2.0-pro", messages=[{"role": "user", "content": table_p}])
                
                # Generate Synthesis
                final_p = f"Synthesize these expert views into one definitive, cited report: {answers}"
                final_res = ai.chat.completions.create(model="google/gemini-2.0-pro", messages=[{"role": "user", "content": final_p}])
                
                res_obj = {
                    "q": query, 
                    "report": final_res.choices[0].message.content, 
                    "table": table_res.choices[0].message.content
                }
                st.session_state.history.append(res_obj)
                st.session_state.view = res_obj
                status.update(label="✅ Analysis Complete", state="complete")
            except Exception as e:
                st.error(f"Final synthesis failed: {e}")

    # Display results if available
    if "view" in st.session_state:
        v = st.session_state.view
        st.divider()
        st.subheader(f"Results for: {v['q']}")
        
        # Action Bar
        if st.button("📧 Email Final Report"):
            send_report(v['report'], v['q'])
            
        # Display Sections
        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.markdown("### 📊 Expert Comparison")
            st.markdown(v['table'])
        with col_b:
            st.markdown("### 📝 Verified Final Report")
            st.markdown(v['report'])
