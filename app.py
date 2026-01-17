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
            st.session_state["password_correct"], st.session_state["user"] = True, u
            st.rerun()
        else: st.error("Invalid Login")
    return False

# --- 2. MAIN APPLICATION ---
if check_password():
    st.set_page_config(page_title="AI Intelligence Hub", layout="wide")
    st.title("⚖️ Private AI Intelligence Hub")
    
    query = st.chat_input("Ask about the Eagles vs 49ers controversies...")

    if query:
        # Initialize API Clients
        # OpenRouter for the Experts, Google Direct for the Judge
        ai_client = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86YWM1NjI5M2Y2ZTMwM2YwODMzZjJmMTJhYzJjMjUzZDA6NzowMWJlOjJhYzM3YWI3NTE4YmI4N2JiYjhmNjA5YzdiNjU1ODFiMTBiMTI5OTYzOTQwYTIwNDk4Zjk0ODYxMTAyZjkxMzg6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv_client = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        google_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. LIVE SEARCH
            st.write("🔎 Performing live web audit...")
            try:
                res = tv_client.search(query, search_depth="basic", max_results=2)
                web_context = "\n".join([r['content'][:500] for r in res.get('results', [])])
            except: web_context = "Web search failed."

            # B. THE EXPERTS (OpenRouter)
            st.write("🤖 Consulting Board of Experts...")
            experts = ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]
            expert_responses = []
            
            for model_name in experts:
                try:
                    resp = ai_client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": f"Summarize key facts (3 bullets): {web_context}\n\nQ: {query}"}]
                    )
                    expert_responses.append(f"{model_name}: {resp.choices[0].message.content}")
                except: expert_responses.append(f"{model_name}: Analysis failed.")

            # C. THE FINAL JUDGE (Google Direct + Thinking Mode)
            st.write("⚖️ Final Audit (Thinking Mode Enabled)...")
            try:
                # Combining expert views into one string
                combined_reports = "\n\n".join(expert_responses)
                
                # Using the 2026 google-genai SDK
                response = google_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"You are the Final Judge. Review these expert reports and provide a verified final answer: {combined_reports}",
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=2000)
                    )
                )
                
                st.session_state.report = response.text
                status.update(label="✅ Success", state="complete")
            except Exception as e:
                st.error(f"Judge Error: {e}")

    # Display results
    if "report" in st.session_state:
        st.divider()
        st.markdown("### 📝 Verified Final Report")
        st.markdown(st.session_state.report)

