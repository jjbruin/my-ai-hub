import streamlit as st
import hmac
from openai import OpenAI
from tavily import TavilyClient
from google import genai
from google.genai import types

# --- 1. LOGIN ---
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

# --- 2. MAIN APP ---
if check_password():
    st.set_page_config(page_title="AI Intelligence Hub", layout="wide")
    st.title("⚖️ Private AI Intelligence Hub")
    
    query = st.chat_input("Ask about the Eagles vs 49ers controversies...")

    if query:
        # Initialize
        ai_client = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86ZTFiMTdlYmE2Y2Q3ZjhiNTYzNzRjMDc3ZTg0OWU0YmU6NzpjNjQ2OjFhOWEyNTJjMWJiMmJmODg1N2RiNzdjOWMxNjk4ZWM5NzYyMzkyNDVlODRhMmE5ZWQ2MjUzNDFlOTA4YmNmMWI6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv_client = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        google_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. Search
            st.write("🔎 Live Audit...")
            try:
                res = tv_client.search(query, search_depth="basic", max_results=2)
                web_context = "\n".join([r['content'][:600] for r in res.get('results', [])])
            except: web_context = "Web search data missing."

            # B. Experts (OpenRouter)
            st.write("🤖 Consulting Experts...")
            expert_responses = []
            for m in ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]:
                try:
                    resp = ai_client.chat.completions.create(
                        model=m,
                        messages=[{"role": "user", "content": f"Analyze these facts: {web_context}\n\nQ: {query}"}]
                    )
                    expert_responses.append(f"Expert {m}: {resp.choices[0].message.content}")
                except: expert_responses.append(f"Expert {m}: Request failed.")

            # C. THE JUDGE (Thinking Mode)
            st.write("⚖️ Final Audit...")
            try:
                combined = "\n\n".join(expert_responses)
                
                # We request thought summaries to be returned
                response = google_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"Synthesize these reports into a final verdict: {combined}",
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=2000, 
                            include_thoughts=True
                        )
                    )
                )
                
                # Save both thoughts and final text
                st.session_state.report = response.text
                
                # Extracting internal thoughts if present
                st.session_state.thoughts = [p.text for p in response.candidates[0].content.parts if p.thought]
                
                status.update(label="✅ Success", state="complete")
            except Exception as e:
                st.error(f"Judge Error: {e}")

    # Display Results
    if "report" in st.session_state:
        st.divider()
        
        # New Button: Show Judge's Internal Reasoning
        if "thoughts" in st.session_state and st.session_state.thoughts:
            with st.expander("👁️ View Judge's Internal Reasoning (Thought Chain)"):
                for thought in st.session_state.thoughts:
                    st.info(thought)

        st.markdown("### 📝 Verified Final Report")
        st.markdown(st.session_state.report)

