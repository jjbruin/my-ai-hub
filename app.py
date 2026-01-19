import streamlit as st
import hmac
import json
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
    st.set_page_config(page_title="Multi-Turn Intelligence Hub", layout="wide")
    st.title("⚖️ Live Multi-AI Chat Hub")

    # --- INITIALIZE CHAT HISTORY ---
    if "messages" not in st.session_state:
        st.session_state.messages = [] # Stores user/assistant turn-by-turn history

    # --- SIDEBAR: TOOLS & EXPORT ---
    with st.sidebar:
        st.header("🛠️ Chat Management")
        
        # Download Button: Exports history to a text file
        if st.session_state.messages:
            chat_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            st.download_button(
                label="📥 Save Chat Stream",
                data=chat_text,
                file_name="intelligence_report.txt",
                mime="text/plain"
            )

        if st.button("🧹 New Conversation"):
            st.session_state.messages = []
            st.rerun()

    # --- DISPLAY CHAT HISTORY ---
    # This loop keeps everything on the screen as you interact
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- REACT TO USER INPUT ---
    if prompt := st.chat_input("Ask a follow-up or a new question..."):
        # 1. Immediately show and save User message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 2. Run the Multi-AI Pipeline
        together_client = OpenAI(base_url="https://api.together.xyz/v1", api_key=st.secrets["TOGETHER_KEY"])
        google_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
        tv_client = TavilyClient(api_key=st.secrets["TAVILY_KEY"])

        with st.status("📡 Orchestrating Experts...", expanded=False) as status:
            # A. LIVE SEARCH
            try:
                search = tv_client.search(prompt, search_depth="advanced", max_results=3)
                live_context = "\n".join([r['content'] for r in search['results']])
            except: live_context = "No live data found."

            # B. EXPERTS
            expert_reports = []
            for name, model_id in {"Meta Llama": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "Qwen": "Qwen/Qwen2.5-72B-Instruct-Turbo"}.items():
                try:
                    resp = together_client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": f"Use this data: {live_context}"}, {"role": "user", "content": prompt}]
                    )
                    expert_reports.append(f"### {name}\n{resp.choices[0].message.content}")
                except: expert_reports.append(f"### {name}\n[Offline]")

            # C. JUDGE
            try:
                combined = "\n\n---\n\n".join(expert_reports)
                # Pass the full conversation history to the Judge for context
                history_summary = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-4:]])
                
                judge_resp = google_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"History: {history_summary}\n\nExperts: {combined}\n\nLatest Task: {prompt}",
                    config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=2000))
                )
                final_answer = judge_resp.text
                status.update(label="✅ Success", state="complete")
            except Exception as e:
                final_answer = f"Error in synthesis: {e}"

        # 3. Display and save Assistant message
        with st.chat_message("assistant"):
            st.markdown(final_answer)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})
