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
    
    query = st.chat_input("Ask about the Eagles vs 49ers controversies...")

    if query:
        # Initialize 2026 API Clients
        ai_client = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86ZWE0OGZhMTNmNWE2MTk0ZjE1ZmZiNTRiYjgyZTlmM2E6NzowZjA5OmYxNjg1YTM3MDg3ZmNkMTBmYWNmZGE2YzVmMTFlYzg5OTZkY2QxMDAzYTVkNWM0OTA1ODAxNDBmNDM3Yjk4ODQ6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv_client = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        
        # New 2026 SDK Client
        google_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. Search
            st.write("🔎 Web Audit...")
            try:
                res = tv_client.search(query, search_depth="basic", max_results=2)
                web_context = "\n".join([r['content'][:600] for r in res.get('results', [])])
            except: web_context = "Web search data missing."

            # B. Experts (OpenRouter)
            st.write("🤖 Consulting Experts...")
            expert_responses = []
            # We explicitly store the text to ensure it's passed to the Judge
            for m in ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]:
                try:
                    resp = ai_client.chat.completions.create(
                        model=m,
                        messages=[{"role": "user", "content": f"Analyze these facts: {web_context}\n\nQ: {query}"}]
                    )
                    # Forcing a text label so the Judge knows which expert is speaking
                    expert_responses.append(f"Expert {m}: {resp.choices[0].message.content}")
                except: expert_responses.append(f"Expert {m}: Request failed.")

            # C. THE JUDGE (Thinking Mode Enabled)
            st.write("⚖️ Final Audit...")
            try:
                combined_reports = "\n\n".join(expert_responses)
                
                # Using gemini-2.5-flash with a thinking budget
                response = google_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"You are the Final Judge. Review these reports and provide a verified final answer: {combined_reports}",
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=2000, # Allocated reasoning tokens
                            include_thoughts=True # Enables capturing the thought process
                        )
                    )
                )
                
                st.session_state.report = response.text
                
                # Extracting internal thoughts for the expander
                st.session_state.thoughts = [p.text for p in response.candidates[0].content.parts if p.thought]
                
                status.update(label="✅ Success", state="complete")
            except Exception as e:
                st.error(f"Judge Error (404 often means model ID mismatch): {e}")

    # Display results
    if "report" in st.session_state:
        st.divider()
        
        # Internal Reasoning Button (Expander)
        if "thoughts" in st.session_state and st.session_state.thoughts:
            with st.expander("👁️ View Judge's Internal Reasoning (Thought Chain)"):
                for thought in st.session_state.thoughts:
                    st.info(thought)

        st.markdown("### 📝 Verified Final Report")
        st.markdown(st.session_state.report)
