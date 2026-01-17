import streamlit as st
import hmac, smtplib, pandas as pd
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
    
    query = st.chat_input("Enter your research query...")

    if query:
        ai = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86OWQwYzFkNzhlODM3ZDE3NzU2ZDliNDZkNzNhYjk5MzI6Nzo2NTE2OmU2MjQwYTdiY2UwMjU5MzVkZWVmM2U3NzJjNjYxMTNiMjI0ODkxYWVhYzVjOTg4NmE3NjNmYmE3MDE2MWM3ODg6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv = TavilyClient(api_key=st.secrets["TAVILY_KEY"])

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. Search
            st.write("🔎 Web Audit...")
            try:
                res = tv.search(query, search_depth="basic", max_results=2)
                web = "\n".join([r['content'][:300] for r in res.get('results', [])])
            except: web = "Search error."

            # B. Experts (Forced to be tiny to save the Judge)
            st.write("🤖 Consulting Board...")
            experts = ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]
            summaries = []
            
            for m in experts:
                try:
                    r = ai.chat.completions.create(
                        model=m,
                        messages=[{"role": "user", "content": f"Answer in 3 SHORT bullets only: {web}\n\nQ: {query}"}]
                    )
                    summaries.append(r.choices[0].message.content)
                except: summaries.append("- Expert unavailable.")

            # C. THE JUDGE (Receiving a small, safe packet)
            st.write("⚖️ Final Audit...")
            try:
                judge_input = "\n".join(summaries)
                final = ai.chat.completions.create(
                    model="google/gemini-2.0-flash-exp",
                    messages=[{"role": "user", "content": f"Synthesize these bullets into a final report: {judge_input}"}]
                )
                st.session_state.report = final.choices[0].message.content
                status.update(label="✅ Success", state="complete")
            except Exception:
                st.error("The network is still too crowded. Please try a simpler question.")

    if "report" in st.session_state:
        st.divider()
        st.markdown(st.session_state.report)




