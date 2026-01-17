import streamlit as st
import hmac
from openai import OpenAI
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
   st.set_page_config(page_title="Multi-AI Intelligence Hub", layout="wide")
   st.title("⚖️ Multi-AI Intelligence Hub")

   # Reset Tool in Sidebar
   if st.sidebar.button("🧹 Clear Conversation"):
       for key in ["report", "thoughts", "debug"]:
           if key in st.session_state: del st.session_state[key]
       st.rerun()

   query = st.chat_input("Test with: What is the square root of 81?")

   if query:
       # Initialize Clients
       # Together AI for diverse Experts; Google for the Final Judge
       together_client = OpenAI(
           base_url="https://api.together.xyz/v1", 
           api_key=st.secrets["TOGETHER_KEY"]
       )
       google_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

       with st.status("📡 Orchestrating Multi-AI Audit...", expanded=True) as status:
           # A. CONSULTING THE EXPERTS
           st.write("🤖 Consulting Meta & Alibaba Experts...")
           expert_reports = []

           # Using the best-in-class 2026 open-source models
           experts = {
               "Llama-3.3-70B": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
               "Qwen-2.5-72B": "Qwen/Qwen2.5-72B-Instruct-Turbo"
           }

           for name, model_id in experts.items():
               try:
                   resp = together_client.chat.completions.create(
                       model=model_id,
                       messages=[{"role": "user", "content": f"Provide a concise expert analysis: {query}"}]
                   )
                   content = resp.choices[0].message.content
                   expert_reports.append(f"### Report from {name}\n{content}")
               except Exception as e:
                   expert_reports.append(f"### Report from {name}\n[Connection Failed: {str(e)}]")

           # B. THE FINAL JUDGE (Thinking Mode)
           st.write("⚖️ Final Judicial Synthesis...")
           try:
               combined_context = "\n\n---\n\n".join(expert_reports)

               # DIAGNOSTIC: Ensure data exists before judging
               st.session_state.debug = combined_context

               # Gemini 2.5 Flash with Thinking Budget for deeper reasoning
               response = google_client.models.generate_content(
                   model='gemini-2.5-flash',
                   contents=f"You are the Lead Judge. Synthesize these expert reports into a final verdict: {combined_context}",
                   config=types.GenerateContentConfig(
                       thinking_config=types.ThinkingConfig(
                           thinking_budget=2000, 
                           include_thoughts=True
                       )
                   )
               )

               st.session_state.report = response.text
               # Capture thoughts for the internal reasoning button
               st.session_state.thoughts = [p.text for p in response.candidates[0].content.parts if p.thought]

               status.update(label="✅ Audit Complete", state="complete")
           except Exception as e:
               st.error(f"Judge Error: {e}")

   # --- 3. DISPLAY RESULTS ---
   if "debug" in st.session_state:
       with st.expander("🛠️ Debug: Expert Handoff Data"):
           st.text(st.session_state.debug)

   if "report" in st.session_state:
       st.divider()

       # Internal Thoughts Button
       if "thoughts" in st.session_state and st.session_state.thoughts:
           with st.expander("👁️ View Judge's Internal Reasoning (Thought Chain)"):
               for thought in st.session_state.thoughts:
                   st.info(thought)

       st.markdown("### 📝 Verified Final Report")
       st.markdown(st.session_state.report)




