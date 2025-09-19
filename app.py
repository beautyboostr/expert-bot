import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- 1. SETUP AND CONFIGURATION ---

# Set the page configuration for your app
st.set_page_config(page_title="Expert Program Advisor Bot", layout="centered")

# Configure the Gemini API key securely
# For deployment, uses Streamlit's secrets management.
# For local development, it falls back to an environment variable.
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (AttributeError, KeyError):
    # This is a fallback for local development
    # Make sure you have an environment variable named "GEMINI_API_KEY"
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    except KeyError:
        st.error("API Key not found. Please set your GEMINI_API_KEY in Streamlit secrets or as an environment variable.", icon="🚨")
        st.stop()


# --- 2. HELPER FUNCTIONS ---

@st.cache_data
def load_data():
    """Loads the recommendation data from CSV files. The cache ensures this runs only once."""
    try:
        recommendations_df = pd.read_csv('recommendations_final.csv')
        problem_rec_df = pd.read_csv('problem_recommendations_final.csv')
        return recommendations_df, problem_rec_df
    except FileNotFoundError as e:
        st.error(f"Error: A required data file was not found: `{e.filename}`. Please make sure all CSV files are in the same folder as the app.", icon="🚨")
        return None, None

def find_problem_recommendation(user_problem_text, recommendations_df):
    """Scans the user's text for keywords and returns the corresponding recommendation row."""
    if not user_problem_text or not isinstance(user_problem_text, str):
        return None
    for _, row in recommendations_df.iterrows():
        if row['problem_keyword'].lower() in user_problem_text.lower():
            return row
    return None

def generate_creative_content(prompt):
    """Sends the prompt to the Gemini API and returns the generated content."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred while contacting the AI model: {e}", icon="🔥")
        return None


# --- 3. MAIN APPLICATION UI ---

# Load the data using the cached function
recommendations_df, problem_rec_df = load_data()

# Enhanced Welcome Message
with st.container(border=True):
    st.title("🎓 Welcome to the Program Advisor!")
    st.info(
        "**Hello!** This bot is designed to help you structure and define your next educational program. "
        "In just a few minutes, you'll have a complete blueprint for your next course or lesson.",
        icon="👋"
    )
    st.write("Please answer the questions below to get started.")

# Only proceed if the data files were loaded successfully
if recommendations_df is not None and problem_rec_df is not None:
    # Use a form to gather all user inputs before processing
    with st.form("expert_form"):
        st.header("Step 1: Your Profile", divider="rainbow")

        # Define question options directly in the code
        q1_options = ["Dermatologist", "Facialist", "Esthetician", "Skincare Coach", "Skincare Influencer", "Other"]
        q2_options = ["Educational content (e.g., skincare routines, lifestyle changes).", "Hands-on techniques (e.g., facial massage, facial yoga).", "A combination of both."]
        q3_options = ["1-2 hours", "3-4 hours a week", "8-10 hours a week"]

        # Render the form widgets
        answer1 = st.selectbox("Which of the following best describes your professional role?", q1_options, index=None, placeholder="Select your role...")
        answer2 = st.radio("What is your primary method for treating clients?", q2_options, index=1)
        answer3 = st.select_slider("How many hours a week can you spare for content creation?", q3_options, value="3-4 hours a week")

        st.header("Step 2: Your Program Focus", divider="rainbow")
        answer4 = st.text_area("Describe the main problem you solve for your clients.", placeholder="Example: I help clients get rid of persistent acne.")
        answer5 = st.text_input("In one sentence, describe your main expertise.", placeholder="Example: I specialize in holistic solutions for aging skin.")

        # The button that submits the form
        submitted = st.form_submit_button("Generate My Program Blueprint", use_container_width=True)

    # This block of code runs ONLY after the user clicks the submit button
    if submitted:
        # --- 4. PROCESSING AND OUTPUT ---

        # Display the final summary blueprint
        st.header("🚀 Your Program Blueprint", divider="rainbow")
        with st.container(border=True):
            st.subheader("Your Profile & Program Focus:")
            st.write(f"**- Professional Role:** `{answer1}`")
            st.write(f"**- Primary Method:** `{answer2}`")
            st.write(f"**- Weekly Time Commitment:** `{answer3}`")
            st.write(f"**- Client Problem to Solve:** `{answer4}`")
            st.write(f"**- Your Core Expertise:** `{answer5}`")

        with st.container(border=True):
            st.subheader("Key Recommendations:")
            # Get rule-based recommendation for program length
            time_based_rec = recommendations_df[recommendations_df['condition_time'] == answer3]
            if not time_based_rec.empty:
                st.success(time_based_rec['recommendation_text'].iloc[0], icon="🕒")
            
            # Get problem-specific content ideas
            problem_specific_rec = find_problem_recommendation(answer4, problem_rec_df)
            if problem_specific_rec is not None:
                st.info(f"**Recommended Content Focus:** {problem_specific_rec['recommended_program']}", icon="💡")
                st.info(f"**Ideal Target Audience:** {problem_specific_rec['target_audience']}", icon="👥")

        # --- 5. GEMINI API CALL AND OUTPUT ---
        st.header("✨ Your AI-Generated Creative Content", divider="rainbow")

        with st.spinner("Our creative AI is brainstorming your program content... Please wait a moment."):
            # Construct the final, constrained prompt
            prompt_for_gemini = f"""
            You are an expert instructional designer and marketing copywriter for the skincare industry. A skincare professional has provided their information. Your task is to help them create a program, but you must follow a very strict set of rules.

            **Expert's Information:**
            * **Professional Role:** {answer1}
            * **Primary Method:** {answer2}
            * **Time Commitment:** {answer3}
            * **Main Problem They Solve:** "{answer4}"
            * **Main Expertise:** "{answer5}"

            **Strict Constraints:**
            - The ONLY two valid program formats are:
                1. A "Full 12-Lesson Monthly Program".
                2. A "Single Additional Lesson".
            - You MUST NOT suggest any other format, such as a mini-course, a 3-part series, a workshop, or any other number of lessons.
            - The generated Program Description and Titles must clearly reflect the recommended format (either a comprehensive monthly program or a single, focused lesson).

            **Your Tasks:**

            **1. Recommend a Program Format:**
            Based on the expert's time commitment, explicitly recommend ONLY ONE of the two valid formats: the "Full 12-Lesson Monthly Program" or the "Single Additional Lesson".

            **2. Write a Program Concept Description:**
            Create a short, engaging description (3-4 sentences) for the format you recommended.

            **3. Generate Title and Tagline Ideas:**
            Generate 4 creative and engaging titles suitable for the recommended format. For each title, also provide a compelling one-sentence tagline.

            The overall tone should be professional, empowering, and results-oriented. Format the entire output using Markdown for easy readability.
            """
            
            # Call the function to get the creative content
            creative_content = generate_creative_content(prompt_for_gemini)
            
            # Display the generated content in a container
            if creative_content:
                with st.container(border=True):
                    st.markdown(creative_content)