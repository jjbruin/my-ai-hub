import streamlit as st
import hmac, smtplib
from openai import OpenAI
from tavily import TavilyClient
import google.generativeai as genai

# --- 1. LOGIN ---
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

# --- 2. MAIN HUB ---
if check_password():
    st.set_page_config(page_title="AI Intelligence Hub", layout="wide")
    st.title("⚖️ Private AI Intelligence Hub")
    
    query = st.chat_input("Enter your research query...")

    if query:
        # Initialize Clients
        ai = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86NTI1OWU1ZTM1MWEwNDdhYmZlOGNlOGM0ZGIwOTJjNTE6Nzo1NWNiOmU4OWY4ODdlNGZmYzM4OTg1ZjBlMzRiNjgzNzM2Y2IyMjY5MDU0OTA3NTgyZWNiM2RmZDhkYTUwMGMwNDE0YWY6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv = TavilyClient(api_key=st.secrets["TAVILY_KEY"])
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"]) # Direct Google Connection
        
        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. Search
            st.write("🔎 Web Audit...")
            try:
                res = tv.search(query, search_depth="basic", max_results=1)
                web = res.get('results', [])[0]['content'][:1000] if res.get('results') else "No facts."
            except: web = "Search error."

            # B. Expert Analysis (Via OpenRouter)
            st.write("🤖 Expert Board...")
            try:
                r1 = ai.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=[{"role": "user", "content": f"Analyze: {web}\n\nQ: {query}"}]
                )
                expert_view = r1.choices[0].message.content
            except: expert_view = "Expert failed."

            # C. THE JUDGE (Direct Google bypass)
            st.write("⚖️ Final Audit...")
            try:
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                response = model.generate_content(f"You are the Final Judge. Synthesize this expert report: {expert_view}")
                st.session_state.report = response.text
                status.update(label="✅ Success", state="complete")
            except Exception as e:
                st.error(f"Critical System Error: {e}")

    if "report" in st.session_state:
        st.divider()
        st.markdown(st.session_state.report)

