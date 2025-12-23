import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- 1. PAGE CONFIGURATION & UI SETUP ---
st.set_page_config(
    page_title="AI Interviewer", 
    page_icon="👔",
    layout="centered" # Keeps the chat centered nicely
)

# --- 2. SECURITY CHECK ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except FileNotFoundError:
    st.error("🚨 Security Alert: Secrets file not found. Check .streamlit/secrets.toml")
    st.stop()

# --- 3. MEMORY INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "cv_text" not in st.session_state:
    st.session_state["cv_text"] = ""

if "interview_started" not in st.session_state:
    st.session_state["interview_started"] = False

# --- 4. SIDEBAR: CONTROL PANEL ---
with st.sidebar:
    st.header("⚙️ Controls")
    st.write("Upload your CV to begin the simulation.")
    
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
    
    # Only show button if file is there
    if uploaded_file:
        if st.button("🚀 Start Interview", type="primary"):
            
            with st.spinner("🤖 AI Recruiter is reading your resume..."):
                # A. Read PDF
                reader = PdfReader(uploaded_file)
                raw_text = ""
                for page in reader.pages:
                    raw_text += page.extract_text()
                
                # B. Save Context
                st.session_state["cv_text"] = raw_text
                st.session_state["interview_started"] = True
                
                # C. Clear old chat if restarting
                st.session_state["messages"] = []
                
                # D. GENERATE FIRST QUESTION (Reverse RAG)
                model = genai.GenerativeModel("gemini-2.5-flash-lite") # Stable model
                
                start_prompt = f"""
                You are a senior recruiter at a top tech company.
                I have just handed you my CV.
                
                CV CONTENT:
                {raw_text}
                
                TASK:
                1. Analyze the CV quickly.
                2. Start the conversation by greeting the candidate by name (if found) or just "Candidate".
                3. Ask the FIRST difficult behavioral question based on their specific experience.
                """
                
                response = model.generate_content(start_prompt)
                
                # Add AI opening move to history
                st.session_state["messages"].append({"role": "assistant", "content": response.text})
                
                # Rerun to show the chat interface immediately
                st.rerun()
    
    st.divider()
    st.caption("Powered by Gemini 1.5 & Streamlit")

# --- 5. MAIN PAGE UI ---

st.title("👔 AI Job Interview Simulator")

if not st.session_state["interview_started"]:
    # === WELCOME SCREEN ===
    st.markdown("""
    ### 👋 Welcome, Candidate.
    
    Ready to test your skills? This AI will:
    1. Read your actual **PDF Resume**.
    2. Ask you **custom questions** based on your experience.
    3. **Grade your answers** in real-time.
    
    **👈 Upload your CV in the sidebar to begin.**
    """)
    st.info("Tip: Treat this like a real video call. Be professional!")

else:
    # === CHAT INTERFACE ===
    st.caption("🔴 Interview in Progress...")
    st.divider()

    # A. Display Chat History
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # B. Chat Input (Only appears when interview is active)
    if prompt := st.chat_input("Type your answer here..."):
        
        # 1. Show User Message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state["messages"].append({"role": "user", "content": prompt})

        # 2. AI Response
        with st.chat_message("assistant"):
            with st.spinner("Recruiter is taking notes..."):
                try:
                    # Context-Aware Prompt
                    interview_prompt = f"""
                    ROLE: You are a strict but fair Recruiter.
                    CONTEXT: The candidate's CV is: {st.session_state["cv_text"]}
                    
                    CONVERSATION HISTORY:
                    {st.session_state["messages"][-6:]}
                    
                    CANDIDATE'S LAST ANSWER: "{prompt}"
                    
                    YOUR GOAL:
                    1. Provide brief feedback on their answer (Is it vague? Is it STAR method?).
                    2. Ask the NEXT follow-up question. Make it harder.
                    """
                    
                    # Call Gemini
                    model = genai.GenerativeModel("gemini-2.5-flash-lite")
                    response = model.generate_content(interview_prompt)
                    
                    st.markdown(response.text)
                    st.session_state["messages"].append({"role": "assistant", "content": response.text})
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")