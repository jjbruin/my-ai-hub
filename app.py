import streamlit as st
import hmac, smtplib
from openai import OpenAI
from tavily import TavilyClient

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
    
    query = st.chat_input("Ask about the Eagles vs 49ers...")

    if query:
        ai = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86OTBjNDE5NmUwOWRlMzI1ZmU1OWQ5ZDk0MDZiYmI0NTI6NzpiODE2OmQ1NmY4Mzc5MmM2ODA0YWQ0NWQ5YmY3MjE2YWFiMDJiMTg5MjE1MDY1YzAzMzUxZjNiOThlMTc2ODkzNmM4Y2E6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv = TavilyClient(api_key=st.secrets["TAVILY_KEY"])

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. Search (Limit to 1 result, 300 characters only)
            st.write("🔎 Reading one news source...")
            try:
                res = tv.search(query, search_depth="basic", max_results=1)
                web_raw = res.get('results', [])[0]['content'] if res.get('results') else "No facts."
                web = web_raw[:300] # HARD CUT: Only 300 characters
            except: web = "Search error."

            # B. Single Expert Summary
            st.write("🤖 Expert Analysis...")
            try:
                # Ask for a VERY short answer
                r1 = ai.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=[{"role": "user", "content": f"Answer in 50 words: {web}\n\nQ: {query}"}]
                )
                expert_view = r1.choices[0].message.content[:400]
            except: expert_view = "Expert failed."

            # C. THE JUDGE (Receiving a tiny packet)
            st.write("⚖️ Final Audit...")
            try:
                final = ai.chat.completions.create(
                    model="google/gemini-2.0-flash-exp",
                    messages=[{"role": "user", "content": f"Final report: {expert_view}"}]
                )
                st.session_state.report = final.choices[0].message.content
                status.update(label="✅ Success", state="complete")
            except Exception:
                st.error("The network blocked the Final Judge. Try a simpler topic.")

    if "report" in st.session_state:
        st.divider()
        st.markdown(st.session_state.report)


