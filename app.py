import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- 1. SETUP AND CONFIGURATION ---

st.set_page_config(page_title="Expert Program Advisor Bot", layout="wide")

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

# --- 3. LAYOUT AND UI ---

st.title("🎓 Expert Program Advisor")
st.write("---")

# Create a two-column layout
col1, col2 = st.columns([1, 1.5]) # Left column is smaller than the right

# --- LEFT COLUMN / QUESTIONNAIRE ---
with col1:
    load_data_result = load_data()
    if load_data_result:
        recommendations_df, problem_rec_df = load_data_result
    else:
        st.stop()

    # STAGE 0: Initial Profile Form
    if st.session_state.stage == 0:
        with st.form("expert_form_1"):
            st.subheader("Step 1: Your Profile")
            q1_options = ["Dermatologist", "Facialist", "Esthetician", "Skincare Coach", "Skincare Influencer", "Other"]
            q2_options = ["Educational content", "Hands-on techniques", "A combination of both"]
            q3_options = ["1-2 hours", "3-4 hours a week", "8-10 hours a week"]

            answer1 = st.selectbox("Your Role (Required)", q1_options, index=None, placeholder="Select your role...")
            answer2 = st.radio("Your Method", q2_options, index=1)
            answer3 = st.radio("Your Time Commitment", q3_options, index=1)
            
            st.write("---")
            st.subheader("Step 2: Your Focus")
            answer4 = st.text_area("Client's Problem (Required)", placeholder="Example: I help clients get rid of persistent acne.")
            answer5 = st.text_input("Your Expertise (Required)", placeholder="Example: I specialize in holistic solutions for aging skin.")

            submitted = st.form_submit_button("Next Step", use_container_width=True)
            if submitted:
                if not all([answer1, answer4, answer5]):
                    st.error("⚠️ Please fill in all required fields.")
                else:
                    st.session_state.form_data.update({"role": answer1, "method": answer2, "time": answer3, "problem": answer4, "expertise": answer5})
                    if answer3 == "3-4 hours a week": set_stage(1)
                    elif answer3 == "8-10 hours a week": set_stage(2)
                    else: set_stage(3)
                    st.rerun()

    # STAGE 1: Decision Point
    if st.session_state.stage == 1:
        st.subheader("Step 3: Your Goal")
        st.write("What would you like to focus on now?")
        if st.button("Create a Single Lesson", use_container_width=True, type="primary"):
            st.session_state.form_data['goal'] = 'single_lesson'
            set_stage(3); st.rerun()
        if st.button("Outline a Full 12-Lesson Program", use_container_width=True):
            st.session_state.form_data['goal'] = 'full_program'
            set_stage(2); st.rerun()

    # STAGE 2: Deep Dive
    if st.session_state.stage == 2:
        with st.form("expert_form_2"):
            st.subheader("Step 3: Your Method")
            st.info("Describe the transformation you provide.", icon="🗺️")
            point_a = st.text_area("Client's Starting Point (A)", placeholder="Example: My client has painful, inflamed cystic acne...")
            point_b = st.text_area("Client's Transformation (B)", placeholder="Example: My client will have calm, clear skin...")
            method_desc = st.text_area("Your Unique Method", placeholder="Example: My method involves three phases: 1. Calming inflammation...")
            
            submitted = st.form_submit_button("Generate Blueprint", use_container_width=True, type="primary")
            if submitted:
                if not all([point_a, point_b, method_desc]):
                    st.error("⚠️ Please describe the transformation journey.")
                else:
                    st.session_state.form_data.update({"point_a": point_a, "point_b": point_b, "method_desc": method_desc})
                    if st.session_state.form_data.get('time') == '3-4 hours a week': st.session_state.form_data['goal'] = 'combo'
                    else: st.session_state.form_data['goal'] = 'full_program'
                    set_stage(3); st.rerun()

    if st.session_state.stage > 0:
        if st.button("Start Over", use_container_width=True):
            st.session_state.stage = 0
            st.session_state.form_data = {}
            st.rerun()

# --- RIGHT COLUMN / BLUEPRINT DISPLAY ---
with col2:
    if st.session_state.stage < 3:
        st.info("Please complete the questions on the left to generate your program blueprint.")
        st.image("https://i.imgur.com/gYf4g68.png") # A placeholder image

    if st.session_state.stage == 3:
        st.header("🚀 Your Program Blueprint")
        data = st.session_state.form_data
        problem_specific_rec = find_problem_recommendation(data.get('problem', ''), problem_rec_df)

        with st.container(border=True):
            st.subheader("Key Recommendations:")
            time_based_rec = recommendations_df[recommendations_df['condition_time'] == data.get('time')]
            if not time_based_rec.empty:
                st.success(time_based_rec['recommendation_text'].iloc[0], icon="🕒")

            if problem_specific_rec is not None:
                if data.get('goal') in ['full_program', 'combo'] or data.get('time') == '8-10 hours a week':
                    st.info(f"**Recommended Content Type (Full Program):** {problem_specific_rec['recommended_program']}", icon="💡")
                else:
                    st.info(f"**Recommended Content Type (Single Lesson):** {problem_specific_rec['recommended_content']}", icon="💡")
                
                if 'client_target_audience' in problem_specific_rec and pd.notna(problem_specific_rec['client_target_audience']):
                    st.info(f"**Ideal Client Audience:** {problem_specific_rec['client_target_audience']}", icon="👥")

        st.header("✨ Your AI-Generated Creative Content")
        with st.spinner("Our creative AI is brainstorming for you..."):
            base_prompt_info = f"**Expert's Info:**\n* Role: {data.get('role')} | Method: {data.get('method')}\n* Problem: \"{data.get('problem')}\" | Expertise: \"{data.get('expertise')}\""
            
            if data.get('method') == 'Educational content':
                single_lesson_prompt = f"You are a curriculum designer. Brainstorm 4-5 specific ideas for a SINGLE EDUCATIONAL LESSON (5-12 mins) based on the expert's profile.\n{base_prompt_info}\nFor each idea, provide a clear title and a 1-2 sentence description. Format as Markdown."
            else:
                single_lesson_prompt = f"You are an instructional designer. Generate marketing content for a SINGLE, HANDS-ON LESSON based on the expert's profile.\n{base_prompt_info}\nYour tasks:\n1. **Lesson Description:** Write a short, engaging description (3-4 sentences).\n2. **Title & Tagline Ideas:** Generate 4 creative titles, each with a tagline.\nFormat as Markdown."

            full_program_prompt = f"You are an instructional designer. Create a detailed outline for a FULL 12-LESSON MONTHLY PROGRAM based on the expert's A->B method.\n{base_prompt_info}\n**Transformation Method:**\n* Start (A): {data.get('point_a')}\n* Result (B): {data.get('point_b')}\n* Method: {data.get('method_desc')}\n* Structure: 12 lessons over ONE MONTH (3 per week).\n\n**Your Tasks:**\n1. **Program Description:** Write an engaging description (3-4 sentences).\n2. **Title & Tagline Ideas:** Generate 4 creative titles with taglines.\n3. **4-Week Lesson Outline:** Create a 4-week plan with 3 lessons per week. Each lesson needs a title and a 1-sentence description.\nFormat as Markdown."

            if data.get('goal') == 'single_lesson' or data.get('time') == '1-2 hours':
                st.markdown("### Your Single Lesson Content")
                creative_content = generate_content(single_lesson_prompt)
                if creative_content: st.markdown(creative_content)

            elif data.get('goal') == 'full_program':
                st.markdown("### Your Full Program Content & Outline")
                creative_content = generate_content(full_program_prompt)
                if creative_content: st.markdown(creative_content)

            elif data.get('goal') == 'combo':
                st.markdown("### Part 1: Your Single Lesson Content")
                st.info("Here are creative ideas for the single lesson you can create now.", icon="⚡")
                single_lesson_content = generate_content(single_lesson_prompt)
                if single_lesson_content: st.markdown(single_lesson_content)
                
                st.markdown("### Part 2: Your Full Program Outline")
                st.info("And here is the detailed outline for the full program you can build next.", icon="🗺️")
                full_program_content = generate_content(full_program_prompt)
                if full_program_content: st.markdown(full_program_content)
