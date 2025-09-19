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
        st.error(f"Error: A required data file was not found: `{e.filename}`. Please make sure all CSV files are in the same folder as the app.", icon="🚨")
        return None, None

def find_problem_recommendation(user_problem_text, recommendations_df):
    """Scans user text for keywords and returns the recommendation row."""
    if not user_problem_text or not isinstance(user_problem_text, str):
        return None
    for _, row in recommendations_df.iterrows():
        if row['problem_keyword'].lower() in user_problem_text.lower():
            return row
    return None

def generate_creative_content(prompt):
    """Sends the prompt to the Gemini API and returns the generated content."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred while contacting the AI model: {e}", icon="🔥")
        return None


# --- 3. MAIN APPLICATION UI ---

load_data_result = load_data()
if load_data_result:
    recommendations_df, problem_rec_df = load_data_result
else:
    st.stop()

with st.container(border=True):
    st.title("🎓 Welcome to the Program Advisor!")
    st.info(
        "**Hello!** This bot is designed to help you structure and define your next educational program. "
        "In just a few minutes, you'll have a complete blueprint for your next course or lesson.",
        icon="👋"
    )

with st.form("expert_form"):
    st.header("Step 1: Your Profile", divider="rainbow")
    q1_options = ["Dermatologist", "Facialist", "Esthetician", "Skincare Coach", "Skincare Influencer", "Other"]
    q2_options = ["Educational content", "Hands-on techniques", "A combination of both"]
    q3_options = ["1-2 hours", "3-4 hours a week", "8-10 hours a week"]

    answer1 = st.selectbox("Which of the following best describes your professional role?", q1_options, index=None, placeholder="Select your role...")
    answer2 = st.radio("What is your primary method for treating clients?", q2_options, index=1)
    answer3 = st.select_slider("How many hours a week can you spare for content creation?", q3_options, value="3-4 hours a week")

    st.header("Step 2: Your Program Focus", divider="rainbow")
    answer4 = st.text_area("Describe the main problem you solve for your clients.", placeholder="Example: I help clients get rid of persistent acne.")
    answer5 = st.text_input("In one sentence, describe your main expertise.", placeholder="Example: I specialize in holistic solutions for aging skin.")

    submitted = st.form_submit_button("Generate My Program Blueprint", use_container_width=True)

if submitted:
    st.header("🚀 Your Program Blueprint", divider="rainbow")
    problem_specific_rec = find_problem_recommendation(answer4, problem_rec_df)

    with st.container(border=True):
        st.subheader("Key Recommendations:")
        time_based_rec = recommendations_df[recommendations_df['condition_time'] == answer3]
        if not time_based_rec.empty:
            st.success(time_based_rec['recommendation_text'].iloc[0], icon="🕒")

        if problem_specific_rec is not None:
            # ** NEW LOGIC: Show different content focus based on time **
            if answer3 == "8-10 hours a week":
                st.info(f"**Recommended Content Focus:** {problem_specific_rec['recommended_program']}", icon="💡")
            else:
                st.info(f"**Recommended Content Focus:** {problem_specific_rec['recommended_content']}", icon="💡")
            
            # ** NEW LOGIC: Display the correct client audience **
            if 'client_target_audience' in problem_specific_rec and pd.notna(problem_specific_rec['client_target_audience']):
                st.info(f"**Ideal Client Target Audience:** {problem_specific_rec['client_target_audience']}", icon="👥")

    st.header("✨ Your AI-Generated Creative Content", divider="rainbow")
    with st.spinner("Our creative AI is brainstorming for you... This may take a moment."):
        # --- ** NEW LOGIC: ADAPTIVE PROMPT GENERATION ** ---
        prompt_for_gemini = ""
        base_prompt_info = f"""
        **Expert's Information:**
        * Professional Role: {answer1}
        * Primary Method: {answer2}
        * Main Problem They Solve: "{answer4}"
        * Main Expertise: "{answer5}"
        """

        if answer3 == "1-2 hours":
            prompt_for_gemini = f"""
            You are an expert instructional designer. Your task is to generate creative ideas for a SINGLE, FOCUSED ADDITIONAL LESSON based on the expert's information.

            {base_prompt_info}

            **Your Tasks:**
            1.  **Write a Lesson Description:** Create a short, engaging description (3-4 sentences) for this single lesson.
            2.  **Generate Title and Tagline Ideas:** Generate 4 creative and engaging titles for this single lesson. For each title, provide a compelling one-sentence tagline.

            The tone must be professional and empowering. Format the output using Markdown.
            """
        elif answer3 == "8-10 hours a week":
            prompt_for_gemini = f"""
            You are an expert instructional designer. Your task is to generate creative ideas for a FULL 12-LESSON MONTHLY PROGRAM based on the expert's information.

            {base_prompt_info}

            **Your Tasks:**
            1.  **Write a Full Program Description:** Create an engaging description (3-4 sentences) for the complete 12-lesson program.
            2.  **Generate Title and Tagline Ideas:** Generate 4 creative and engaging titles for the full program. For each title, provide a compelling one-sentence tagline.

            The tone must be professional and empowering. Format the output using Markdown.
            """
        else: # This covers "3-4 hours a week"
            prompt_for_gemini = f"""
            You are an expert instructional designer. The expert has time to create one lesson now and plan a full program for later. Perform the following TWO tasks.

            {base_prompt_info}

            ---
            ### **Task 1: Creative Ideas for the Single Additional Lesson**
            Generate creative content for the SINGLE lesson the expert will create now.
            * **Lesson Description:** Write a short, engaging description (3-4 sentences).
            * **Title and Tagline Ideas:** Generate 4 creative titles for this single lesson, each with a compelling one-sentence tagline.

            ---
            ### **Task 2: Outline for the Full 12-Lesson Program**
            Now, provide a high-level topic outline for the full 12-lesson program the expert will build in the future. List 12 lesson titles that logically progress from basics to advanced topics.
            * **Example Format:**
                * Week 1: Understanding the Root Causes of...
                * Week 2: The Essential Daily Ritual for...
                * ...and so on for 12 weeks.

            The tone must be professional and empowering. Format the entire output using Markdown with clear headings for each task.
            """

        creative_content = generate_creative_content(prompt_for_gemini)
        if creative_content:
            with st.container(border=True):
                st.markdown(creative_content)
