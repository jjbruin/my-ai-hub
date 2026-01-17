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
    
    # Sidebar tools
    with st.sidebar:
        if st.button("🧹 Clear All Data"):
            for key in list(st.session_state.keys()):
                if key != "password_correct": del st.session_state[key]
            st.rerun()

    query = st.chat_input("Start with: What is the square root of 81?")

    if query:
        # Initialize the Expert Client with MANDATORY 2026 headers
        # These headers tell OpenRouter's CloudFront firewall that the request is legitimate.
        ai_client = OpenAI(
            base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86MmZhY2VhNDQ4MWUxNjNkYTViNWE5MWI1NDEzOTc1ZWI6NzoyOGQ4OjFlZTIwODQ0YWQ5YjhmM2E3OWI2Mzc5YzhiYWY2ZTQxYTA0NGI2ZjkwZjZkZGFhZmQ3NjI4NTE1OGQwZDEzY2U6cDpUOkY",
            api_key=st.secrets["OPENROUTER_KEY"],
            default_headers={
                "HTTP-Referer": "https://url.avanan.click/v2/r01/___https://streamlit.app___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86MmZhY2VhNDQ4MWUxNjNkYTViNWE5MWI1NDEzOTc1ZWI6NzplNDRhOjE3OWMxMGYyZjNhNTIwMTAxOGJiODgzOGRmNTUyNWFmOGYzNjVmY2VmZmFhZDZhYWQ2NDMwZWE0OTA1OTNkNGM6cDpUOkY", 
                "X-Title": "Private Intelligence Hub",
            }
        )
        tv_client = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        google_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

        with st.status("🔍 Analyzing Request...", expanded=True) as status:
            # A. SEARCH (Skip for pure math, but active for research)
            st.write("🔎 Web Audit...")
            try:
                res = tv_client.search(query, search_depth="basic", max_results=2)
                web_context = "\n".join([r['content'][:600] for r in res.get('results', [])])
            except: web_context = "No additional web data needed."

            # B. THE EXPERTS (Claude & GPT)
            st.write("🤖 Consulting Experts...")
            expert_reports = []
            
            for m in ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]:
                try:
                    resp = ai_client.chat.completions.create(
                        model=m,
                        messages=[{"role": "user", "content": f"Context: {web_context}\n\nQ: {query}"}]
                    )
                    content = resp.choices[0].message.content
                    if content:
                        expert_reports.append(f"### REPORT FROM {m}\n{content}")
                    else:
                        expert_reports.append(f"### REPORT FROM {m}\n[ERROR: Empty response body]")
                except Exception as e:
                    # This will catch the 403 if headers are still rejected
                    expert_reports.append(f"### REPORT FROM {m}\n[CONNECTION FAILED: {str(e)}]")

            # C. THE FINAL JUDGE (Thinking Mode Enabled)
            st.write("⚖️ Final Audit...")
            try:
                judge_input = "\n\n---\n\n".join(expert_reports)
                
                # DIAGNOSTIC: Check if text actually reached this stage
                with st.expander("🛠️ Debug: Expert Handoff Data"):
                    st.text(judge_input)

                response = google_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"Review these reports and provide a final answer: {judge_input}",
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=2000)
                    )
                )
                
                st.session_state.report = response.text
                status.update(label="✅ Analysis Complete", state="complete")
            except Exception as e:
                st.error(f"Judge Error: {e}")

    # --- 3. DISPLAY RESULTS ---
    if "report" in st.session_state:
        st.divider()
        st.markdown("### 📝 Verified Final Report")
        st.markdown(st.session_state.report)


