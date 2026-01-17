import streamlit as st
import hmac, smtplib, pandas as pd
from openai import OpenAI
from tavily import TavilyClient

# --- 1. SECURITY ---
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
        ai = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86NmM0NjNlZDg0NmZmOTgwZjYxM2ExNGQwOGQ5ZmFmODA6Nzo2OTdmOjQ5ZWJmZDM2ZjJmNWMxMWNhYTBiMzlkOGVkMjczZDEzOTZmYTA1NjY4YmQxZGNjMjRiYjNkYTk3ZDQ1MDkzNWM6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        tv = TavilyClient(api_key=st.secrets["TAVILY_KEY"])

        with st.status("Gathering Intelligence...", expanded=True) as status:
            # A. Targeted Search
            st.write("🔎 Performing live web audit...")
            try:
                res = tv.search(query, search_depth="basic", max_results=3)
                # Keep only the most relevant snippet of each result
                web = "\n".join([r['content'][:400] for r in res.get('results', [])])
            except: web = "Web data limited."

            # B. The Board of Experts
            st.write("🤖 Consulting Board of Experts...")
            experts = ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]
            answers = []
            
            for m in experts:
                try:
                    # We ask the experts to be extremely brief to save bandwidth for the judge
                    r = ai.chat.completions.create(
                        model=m,
                        messages=[{"role": "user", "content": f"Briefly answer based on this: {web}\n\nQ: {query}"}]
                    )
                    answers.append(r.choices[0].message.content)
                except: answers.append(f"Expert {m} timed out.")

            # C. THE FINAL JUDGE (The core of the app)
            st.write("⚖️ Final Audit & Synthesis...")
            try:
                # We send the expert findings to the Judge
                expert_inputs = "\n\n".join([f"Expert {i+1}: {ans[:600]}" for i, ans in enumerate(answers)])
                
                final = ai.chat.completions.create(
                    model="google/gemini-2.0-flash-exp",
                    messages=[
                        {"role": "system", "content": "You are the Final Judge. Synthesize the expert views into one verified report."},
                        {"role": "user", "content": f"Expert Perspectives:\n{expert_inputs}"}
                    ]
                )
                st.session_state.report = final.choices[0].message.content
                status.update(label="✅ Final Audit Complete", state="complete")
            except Exception as e:
                st.error(f"The Final Judge was blocked by a network limit. Try a more specific query.")

    if "report" in st.session_state:
        st.divider()
        st.markdown("### 📝 Verified Final Report")
        st.markdown(st.session_state.report)


