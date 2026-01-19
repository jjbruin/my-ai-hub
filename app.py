import streamlit as st
import hmac
from openai import OpenAI
from tavily import TavilyClient
from google import genai
from google.genai import types
import time  # For retry logic

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
    return False

# --- 2. MAIN APPLICATION ---
if check_password():
    st.set_page_config(page_title="Multi-Turn Hub", layout="wide")
    st.title("⚖️ Live Multi-AI Chat Hub")

    # Initialize History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- SIDEBAR: TOOLS & EXPORT ---
    with st.sidebar:
        st.header("🛠️ Chat Management")
        if st.session_state.messages:
            # Build chat stream for saving
            chat_stream = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            st.download_button(
                label="📥 Save Chat Stream",
                data=chat_stream,
                file_name="intelligence_history.txt"
            )
        if st.button("🧹 New Conversation"):
            st.session_state.messages = []
            st.rerun()

    # --- DISPLAY CHAT HISTORY ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- REACT TO USER INPUT ---
    if prompt := st.chat_input("Ask a follow-up or a new question..."):
        # Show and store user prompt
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Clients
        together_client = OpenAI(base_url="https://api.together.xyz/v1", api_key=st.secrets["TOGETHER_KEY"])
        google_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
        tv_client = TavilyClient(api_key=st.secrets["TAVILY_KEY"])

        with st.status("📡 Orchestrating Live Audit...", expanded=False) as status:
            # A. LIVE SEARCH
            try:
                search = tv_client.search(prompt, search_depth="advanced", max_results=3)
                live_context = "\n".join([r['content'] for r in search['results']])
            except: live_context = "No new data found."

            # B. EXPERTS
            expert_reports = []
            for name, m_id in {"Llama": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "Qwen": "Qwen/Qwen2.5-72B-Instruct-Turbo"}.items():
                try:
                    resp = expert_client.chat.completions.create(
                        model=m_id,
                        messages=[{"role": "system", "content": f"2026 Data: {live_context}"}, {"role": "user", "content": prompt}]
                    )
                    expert_reports.append(f"### {name}\n{resp.choices[0].message.content}")
                except: expert_reports.append(f"### {name}\n[Model Overloaded]")

            # C. THE JUDGE (With 503 Retry Logic)
            final_answer = "Analysis failed after multiple attempts."
            for attempt in range(3): # Try 3 times to bypass 503 errors
                try:
                    combined = "\n\n---\n\n".join(expert_reports)
                    # Feed history for follow-up capability
                    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-3:]])
                    
                    response = google_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"History: {history_text}\n\nExperts: {combined}\n\nLatest: {prompt}",
                        config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=2000))
                    )
                    final_answer = response.text
                    status.update(label="✅ Success", state="complete")
                    break 
                except Exception as e:
                    if "503" in str(e):
                        st.warning(f"Judge overloaded (Attempt {attempt+1}/3). Retrying in 2s...")
                        time.sleep(2)
                    else:
                        final_answer = f"Error: {e}"
                        break

        # Show and store Assistant response
        with st.chat_message("assistant"):
            st.markdown(final_answer)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})
