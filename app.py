import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- 1. SETUP AND CONFIGURATION ---

st.set_page_config(page_title="Expert Program Advisor Bot", layout="centered")

# Configure the Gemini API key securely
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (AttributeError, KeyError):
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    except KeyError:
        st.error("API Key not found. Please set your GEMINI_API_KEY in Streamlit secrets or as an environment variable.", icon="🚨")
        st.stop()

# --- 2. HELPER FUNCTIONS ---

@st.cache_data
def load_data():
    """Loads the recommendation data from CSV files."""
    try:
        recommendations_df = pd.read_csv('recommendations_final.csv')
        problem_rec_df = pd.read_csv('problem_recommendations_final.csv')
        return recommendations_df, problem_rec_df
    except FileNotFoundError as e:
        st.error(f"Error: A required data file was not found: `{e.filename}`.", icon="🚨")
        return None, None

def find_problem_recommendation(user_problem_text, recommendations_df):
    """Scans user text for keywords to find the correct client audience."""
    if not user_problem_text or not isinstance(user_problem_text, str): return None
    for _, row in recommendations_df.iterrows():
        if row['problem_keyword'].lower() in user_problem_text.lower(): return row
    return None

def generate_content(prompt):
    """A single function to send any prompt to the Gemini API."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred while contacting the AI model: {e}", icon="🔥")
        return None

# Initialize session state to manage the multi-step form
if 'stage' not in st.session_state:
    st.session_state.stage = 0
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}

def set_stage(stage):
    st.session_state.stage = stage

# --- 3. MAIN APPLICATION UI ---

load_data_result = load_data()
if load_data_result:
    recommendations_df, problem_rec_df = load_data_result
else:
    st.stop()

# STAGE 0: Initial Profile Form
if st.session_state.stage == 0:
    st.title("🎓 Welcome to the Program Advisor!")
    st.info("**Hello!** This bot will help you design your next educational program.", icon="👋")

    with st.form("expert_form_1"):
        st.header("Step 1: Your Profile", divider="rainbow")
        q1_options = ["Dermatologist", "Facialist", "Esthetician", "Skincare Coach", "Skincare Influencer", "Other"]
        q2_options = ["Educational content", "Hands-on techniques", "A combination of both"]
        q3_options = ["1-2 hours", "3-4 hours a week", "8-10 hours a week"]

        answer1 = st.selectbox("Which of the following best describes your professional role?", q1_options, index=None, placeholder="Select your role...")
        answer2 = st.radio("What is your primary method for treating clients?", q2_options, index=1)
        answer3 = st.select_slider("How many hours a week can you spare?", q3_options, value="3-4 hours a week")

        st.header("Step 2: Your Program Focus", divider="rainbow")
        answer4 = st.text_area("Describe the main problem you solve for your clients.", placeholder="Example: I help clients get rid of persistent acne.")
        answer5 = st.text_input("In one sentence, describe your main expertise.", placeholder="Example: I specialize in holistic solutions for aging skin.")

        submitted = st.form_submit_button("Next Step", use_container_width=True)
        if submitted:
            st.session_state.form_data.update({
                "role": answer1, "method": answer2, "time": answer3,
                "problem": answer4, "expertise": answer5
            })
            if answer3 == "3-4 hours a week":
                set_stage(1) # Go to decision stage
            elif answer3 == "8-10 hours a week":
                set_stage(2) # Go directly to deep dive
            else:
                set_stage(3) # Go directly to blueprint for single lesson
            st.rerun()

# STAGE 1: Decision Point for 3-4 Hour Users
if st.session_state.stage == 1:
    st.header("Step 3: What is Your Goal Right Now?", divider="rainbow")
    st.write("With 3-4 hours per week, you have two great options. What would you like to focus on now?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create a Single Lesson", use_container_width=True, type="primary"):
            st.session_state.form_data['goal'] = 'single_lesson'
            set_stage(3)
            st.rerun()
    with col2:
        if st.button("Outline a Full 12-Lesson Program", use_container_width=True):
            st.session_state.form_
