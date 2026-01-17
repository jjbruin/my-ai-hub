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
           st.session_state["password_correct"] = True
           st.rerun()
       else: st.error("Invalid Login")
   return False

# --- 2. MAIN APPLICATION ---
if check_password():
   st.set_page_config(page_title="2026 Intelligence Hub", layout="wide")
   st.title("⚖️ Live Multi-AI Intelligence Hub")

   # Sidebar: Source & Reset Tools
   with st.sidebar:
       st.header("Settings")
       if st.button("🧹 Clear All Data"):
           for key in ["report", "thoughts", "sources", "debug"]:
               if key in st.session_state: del st.session_state[key]
           st.rerun()

   query = st.chat_input("E.g., What happened in the Eagles vs 49ers game last week?")

   if query:
       # Initialize Clients
       expert_client = OpenAI(base_url="https://api.together.xyz/v1", api_key=st.secrets["TOGETHER_KEY"])
       google_client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
       tv_client = TavilyClient(api_key=st.secrets["TAVILY_KEY"])

       with st.status("📡 Orchestrating Live Audit...", expanded=True) as status:

           # A. REAL-TIME SEARCH (The "Eyes" of the AI)
           st.write("🔎 Scanning 2026 Web Data...")
           try:
               # search_depth="advanced" is better for breaking sports news
               search = tv_client.search(query, search_depth="advanced", max_results=4)
               live_context = "\n".join([f"Source: {r['url']}\nContent: {r['content']}" for r in search['results']])
               st.session_state.sources = search['results'] # Save for UI display
           except Exception as e:
               live_context = "Web search failed. Proceeding with internal knowledge."
               st.error(f"Search Error: {e}")

           # B. THE EXPERTS (Knowledge-Injected)
           st.write("🤖 Consulting Experts with Live Context...")
           expert_reports = []
           experts = {
               "Meta Llama 3.3": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
               "Alibaba Qwen 2.5": "Qwen/Qwen2.5-72B-Instruct-Turbo"
           }

           for name, model_id in experts.items():
               try:
                   resp = expert_client.chat.completions.create(
                       model=model_id,
                       messages=[
                           {"role": "system", "content": f"You are a helpful expert. USE THIS LIVE 2026 DATA to answer: {live_context}"},
                           {"role": "user", "content": query}
                       ]
                   )
                   expert_reports.append(f"### {name} Analysis\n{resp.choices[0].message.content}")
               except Exception as e:
                   expert_reports.append(f"### {name}\n[Expert Unavailable: {e}]")

           # C. THE JUDGE (Thinking Synthesis)
           st.write("⚖️ Final Judicial Verdict...")
           try:
               combined_input = "\n\n---\n\n".join(expert_reports)

               # We give the Judge the direct live_context too, to prevent hallucinations
               response = google_client.models.generate_content(
                   model='gemini-2.5-flash',
                   contents=f"REAL-TIME DATA: {live_context}\n\nEXPERT REPORTS: {combined_input}\n\nTASK: {query}",
                   config=types.GenerateContentConfig(
                       thinking_config=types.ThinkingConfig(thinking_budget=2000, include_thoughts=True)
                   )
               )

               st.session_state.report = response.text
               st.session_state.thoughts = [p.text for p in response.candidates[0].content.parts if p.thought]
               status.update(label="✅ Success", state="complete")
           except Exception as e:
               st.error(f"Judge Error: {e}")

   # --- 3. DISPLAY RESULTS ---
   if "report" in st.session_state:
       st.divider()

       # Display Source Links First for Verification
       if "sources" in st.session_state:
           with st.expander("🔗 Verified Sources (2026)"):
               for s in st.session_state.sources:
                   st.markdown(f"- [{s.get('title', 'Source link')}]({s['url']})")

       # Display Final Report
       st.markdown("### 📝 Verified Final Report")
       st.markdown(st.session_state.report)

       # Internal Reasoning
       if "thoughts" in st.session_state:
           with st.expander("👁️ View Judge's Internal Reasoning"):
               for thought in st.session_state.thoughts:
                   st.info(thought)
