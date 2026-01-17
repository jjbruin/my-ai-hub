import streamlit as st
import hmac
from openai import OpenAI
from tavily import TavilyClient
from google import genai
from google.genai import types

# --- 1. LOGIN SYSTEM ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔐 Intelligence Hub Login")
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login"):
        db = st.secrets.get("passwords", {})
        if u in db and hmac.compare_digest(p, db[u]):
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("Invalid Login")
    return False

# --- 2. MAIN APPLICATION ---
if check_password():
    st.set_page_config(page_title="AI Intelligence Hub", layout="wide")
    st.title("⚖️ Private AI Intelligence Hub")
    
    query = st.chat_input("Ask your research question...")

    if query:
        # 2026 Initialization with OpenRouter-specific headers to prevent silent 403s
        ai_client = OpenAI(
            base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86NGQyZWVhYzQ4NjcyNWFhMmFkMjE0Y2U2YmFmNzFkNGI6NzpmMGI5OmE5OTk5Y2EyZDJmNDM0NDg1OGJmOGMyMTQxYzMzZGEwYjVmNzVkMGRmMTU2ZTQyOTVlMWZiMzU3ZGY3ODRhYTY6cDpUOkY", 
            api_key=st.secrets["OPENROUTER_KEY"]
        )
        tv_client = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        google_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. LIVE WEB SEARCH
            st.write("🔎 Web Audit...")
            try:
                res = tv_client.search(query, search_depth="basic", max_results=2)
                web_context = "\n".join([r['content'][:600] for r in res.get('results', [])])
            except: web_context = "No web data available."

            # B. THE EXPERTS (Claude & GPT)
            st.write("🤖 Consulting Experts...")
            expert_reports = []
            
            for m in ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]:
                try:
                    resp = ai_client.chat.completions.create(
                        model=m,
                        extra_headers={
                            "HTTP-Referer": "https://url.avanan.click/v2/r01/___https://streamlit.io___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86NGQyZWVhYzQ4NjcyNWFhMmFkMjE0Y2U2YmFmNzFkNGI6NzplYWE0OmNiOGNhMDM3YjZlNTJkYjM2YTRkMTgxY2QwMjM3Zjg2N2I0OTA4YjFkZmY4ZjliZTA5ODRkOTg1Y2M3ZmNiZGQ6cDpUOkY", # Required for OpenRouter
                            "X-Title": "Intelligence Hub",
                        },
                        messages=[{"role": "user", "content": f"Facts: {web_context}\n\nQ: {query}"}]
                    )
                    content = resp.choices[0].message.content
                    if not content: content = "[Silent Failure: Model returned no text]"
                    expert_reports.append(f"### REPORT FROM {m}\n{content}")
                except Exception as e:
                    expert_reports.append(f"### REPORT FROM {m}\n[CONNECTION FAILED: {str(e)}]")

            # C. THE FINAL JUDGE (Thinking Mode)
            st.write("⚖️ Final Audit...")
            try:
                judge_input = "\n\n---\n\n".join(expert_reports)
                
                # DIAGNOSTIC: This lets us see what the Judge is actually looking at
                with st.expander("🛠️ Debug: Raw Data Sent to Judge"):
                    st.text(judge_input)

                response = google_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"You are the Final Judge. Review these reports and provide a verified final answer:\n\n{judge_input}",
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=2000, 
                            include_thoughts=True
                        )
                    )
                )
                
                st.session_state.report = response.text
                
                # Extract internal thoughts for the button/expander
                st.session_state.thoughts = [p.text for p in response.candidates[0].content.parts if p.thought]
                
                status.update(label="✅ Success", state="complete")
            except Exception as e:
                st.error(f"Judge Error: {e}")

    # --- 3. DISPLAY RESULTS ---
    if "report" in st.session_state:
        st.divider()
        
        # Thinking Button
        if "thoughts" in st.session_state and st.session_state.thoughts:
            with st.expander("👁️ View Judge's Internal Reasoning (Thought Chain)"):
                for thought in st.session_state.thoughts:
                    st.info(thought)

        st.markdown("### 📝 Verified Final Report")
        st.markdown(st.session_state.report)
