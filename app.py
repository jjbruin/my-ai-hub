import streamlit as st
import hmac
from openai import OpenAI
from tavily import TavilyClient
from google import genai
from google.genai import types

# --- 1. LOGIN ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔐 Hub Login")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        db = st.secrets.get("passwords", {})
        if u in db and hmac.compare_digest(p, db[u]):
            st.session_state["password_correct"] = True
            st.rerun()
    return False

# --- 2. THE APP ---
if check_password():
    st.title("⚖️ Verified Intelligence Hub")
    
    # Sidebar Reset
    if st.sidebar.button("Clear All Data"):
        for key in list(st.session_state.keys()):
            if key != "password_correct": del st.session_state[key]
        st.rerun()

    query = st.chat_input("Enter math test or research...")

    if query:
        # Initialize Clients
        ai_client = OpenAI(base_url="https://url.avanan.click/v2/r01/___https://openrouter.ai/api/v1___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86NzBkZGZjZWE1MjYzYzRjYzkzMjVhNDRiMTUzMmFlMGQ6NzoxODZlOjQ4NTU2MzI0ZjczNjYzZWEzYzAxNTIzMjQ0NTcwNjIxODE3OWY3OWU3OTFhNWQ5ZDQ5OTdhNWFhNDg2YWFmOGU6cDpUOkY", api_key=st.secrets["OPENROUTER_KEY"])
        google_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

        with st.status("Running Pipeline...", expanded=True) as status:
            # A. THE EXPERTS (Mandatory 2026 Headers)
            st.write("🤖 Consulting Experts...")
            expert_reports = []
            
            for m in ["anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]:
                try:
                    # THE FIX: These headers are no longer optional in 2026
                    resp = ai_client.chat.completions.create(
                        model=m,
                        extra_headers={
                            "HTTP-Referer": "https://url.avanan.click/v2/r01/___https://streamlit.app___.YXAzOnBlYWNlYWJsZXN0cmVldDphOm86NzBkZGZjZWE1MjYzYzRjYzkzMjVhNDRiMTUzMmFlMGQ6NzphNzkyOjg3M2EyNWRmNzk1NDM5ZWM2MDg3Y2M0NzQxMzA5MGE3ZDUwMjg0ZTI1ZWIxYmE5NGRjNjVlMTY4ZGUzZTM5MDA6cDpUOkY", # Identifies the source
                            "X-Title": "Private Intelligence Hub",   # Identifies the app
                        },
                        messages=[{"role": "user", "content": f"Answer concisely: {query}"}]
                    )
                    content = resp.choices[0].message.content
                    if content:
                        expert_reports.append(f"### {m} Result:\n{content}")
                    else:
                        expert_reports.append(f"### {m} Result:\n[ERROR: Empty Response]")
                except Exception as e:
                    expert_reports.append(f"### {m} Result:\n[CRITICAL CONNECTION ERROR: {str(e)}]")

            # B. THE JUDGE
            st.write("⚖️ Judging Results...")
            try:
                combined_context = "\n\n".join(expert_reports)
                
                # DIAGNOSTIC: You MUST see text here
                with st.expander("🛠️ Debug: What the Judge Sees"):
                    st.text(combined_context)

                response = google_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"Review these reports and give a final answer: {combined_context}",
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=1024)
                    )
                )
                st.session_state.report = response.text
                status.update(label="✅ Success", state="complete")
            except Exception as e:
                st.error(f"Judge Error: {e}")

    # Results
    if "report" in st.session_state:
        st.divider()
        st.markdown("### 📝 Final Verdict")
        st.markdown(st.session_state.report)



