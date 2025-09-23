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
    # Use split to check each word in the user's input against the keywords
    user_words = set(user_problem_text.lower().split())
    for _, row in recommendations_df.iterrows():
        search_keywords = set(row['search_keywords'].split(','))
        if not user_words.isdisjoint(search_keywords):
            return row
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

st.image("logo.png", width=100)

load_data_result = load_data()
if load_data_result:
    recommendations_df, problem_rec_df = load_data_result
else:
    st.stop()

# STAGE 0: Initial Profile Form
if st.session_state.stage == 0:
    st.title("Unlock Your Next Bestselling Skincare Program")
    st.info(
        "**Welcome, Skincare Expert!** Ready to transform your unique expertise into a powerful, structured online program? "
        "In just a few minutes, this advisor will guide you from a brilliant idea to a complete blueprint, ready for creation. "
        "Let's build something amazing together.", 
        icon="✨"
    )
    st.write("---")

    with st.form("expert_form_1"):
        st.header("👤 Step 1: Your Profile", divider="gray")
        q1_options = ["Dermatologist", "Facialist", "Esthetician", "Skincare Coach", "Skincare Influencer", "Other"]
        q2_options = ["Educational content", "Hands-on techniques", "A combination of both"]
        q3_options = ["1-2 hours", "3-4 hours a week", "8-10 hours a week"]

        answer1 = st.selectbox("Which of the following best describes your professional role? (Required)", q1_options, index=None, placeholder="Select your role...")
        answer2 = st.radio("What is your primary method for treating clients?", q2_options, index=1)
        answer3 = st.radio("How many hours a week can you spare?", q3_options, index=1)

        st.header("🎯 Step 2: Your Program Focus", divider="gray")
        answer4 = st.text_area("Describe the main problem you solve or the result you deliver. (Required)", placeholder="Example: I help clients get rid of persistent acne OR I help clients achieve a natural face lift.")
        answer5 = st.text_input("In one sentence, describe your main expertise. (Required)", placeholder="Example: I specialize in holistic solutions for aging skin.")

        submitted = st.form_submit_button("Next Step", use_container_width=True)
        if submitted:
            if not all([answer1, answer4, answer5]):
                st.error("⚠️ Please fill in all required fields before proceeding.")
            else:
                st.session_state.form_data.update({"role": answer1, "method": answer2, "time": answer3, "problem": answer4, "expertise": answer5})
                if answer3 == "3-4 hours a week": set_stage(1)
                elif answer3 == "8-10 hours a week": set_stage(2)
                else: st.session_state.form_data['goal'] = 'single_lesson'; set_stage(4)
                st.rerun()

# STAGE 1: Decision Point for 3-4 Hour Users
if st.session_state.stage == 1:
    st.header("🤔 Step 3: What is Your Goal Right Now?", divider="gray")
    st.write("With 3-4 hours per week, you have two great options. What would you like to focus on now?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create a Single Lesson", use_container_width=True, type="primary"):
            st.session_state.form_data['goal'] = 'single_lesson'
            set_stage(4)
            st.rerun()
    with col2:
        if st.button("Outline a Full 12-Lesson Program", use_container_width=True):
            st.session_state.form_data['goal'] = 'full_program'
            set_stage(2)
            st.rerun()

# STAGE 2: Deep Dive for Full Program Outline
if st.session_state.stage == 2:
    st.header("🗺️ Step 3: Define Your Program's Transformation", divider="gray")
    st.info("To create a great program outline, we need to understand the journey you provide.", icon="✨")
    with st.form("expert_form_2"):
        point_a = st.text_area("Client's Starting Point (Point A) (Required)", placeholder="Example: My client has painful, inflamed cystic acne and feels hopeless.")
        point_b = st.text_area("Client's Transformation (Point B) (Required)", placeholder="Example: My client will have calm, clear skin and feel confident and in control.")
        method_desc = st.text_area("Your Unique Method (Required)", placeholder="Example: My method involves three phases: 1. Calming inflammation... 2. Rebuilding the skin barrier...")
        
        submitted = st.form_submit_button("Generate My Program Blueprint", use_container_width=True, type="primary")
        if submitted:
            if not all([point_a, point_b, method_desc]):
                st.error("⚠️ Please describe your client's transformation journey to continue.")
            else:
                st.session_state.form_data.update({"point_a": point_a, "point_b": point_b, "method_desc": method_desc})
                if st.session_state.form_data.get('time') == '3-4 hours a week': st.session_state.form_data['goal'] = 'combo'
                else: st.session_state.form_data['goal'] = 'full_program'
                set_stage(3)
                st.rerun()

# STAGE 4: CATEGORY SELECTION FOR SINGLE LESSON
if st.session_state.stage == 4:
    st.header("📚 Step 3: Choose a Lesson Category", divider="gray")
    st.info("To give you the best ideas, please select the category for your single lesson.", icon="✨")
    
    lesson_categories = [
        "Hands-on lesson with no equipment",
        "Hands-on with equipment (e.g., guasha, jars)",
        "Hands-on for posture or body exercises",
        "Educational content (Skin 101)"
    ]
    
    category = st.selectbox("Select your lesson category (Required)", lesson_categories, index=None, placeholder="Choose a category...")
    
    if st.button("Generate My Lesson Blueprint", use_container_width=True, type="primary"):
        if not category:
            st.error("⚠️ Please select a category to continue.")
        else:
            st.session_state.form_data['category'] = category
            set_stage(3)
            st.rerun()

# STAGE 3: Final Blueprint Generation
if st.session_state.stage == 3:
    st.header("🚀 Your Program Blueprint", divider="gray")
    data = st.session_state.form_data
    problem_specific_rec = find_problem_recommendation(data.get('problem', ''), problem_rec_df)

    with st.container(border=True):
        st.subheader("Key Recommendations:")
        time_based_rec = recommendations_df[recommendations_df['condition_time'] == data.get('time')]
        if not time_based_rec.empty:
            st.success(time_based_rec['recommendation_text'].iloc[0], icon="🕒")

        if problem_specific_rec is not None:
            # DYNAMIC RECOMMENDATION LOGIC
            program_goal = problem_specific_rec['program_goal']
            expert_method = data.get('method')
            
            rec_text = f"**Recommended Content Focus:** A program to help clients {program_goal}"
            if expert_method == "Educational content":
                rec_text += ". This can be an educational program focusing on topics like " + ", ".join(problem_specific_rec['educational_ideas'].split('|')) + "."
            elif expert_method == "Hands-on techniques":
                rec_text += ". This can be a hands-on program teaching techniques like " + ", ".join(problem_specific_rec['hands_on_ideas'].split('|')) + "."
            else:
                rec_text += ". This can be a combined program with educational topics like " + ", ".join(problem_specific_rec['educational_ideas'].split('|')) + " and hands-on techniques such as " + ", ".join(problem_specific_rec['hands_on_ideas'].split('|')) + "."

            st.info(rec_text, icon="💡")
            
            if 'client_target_audience' in problem_specific_rec and pd.notna(problem_specific_rec['client_target_audience']):
                st.info(f"**Ideal Client Target Audience:** {problem_specific_rec['client_target_audience']}", icon="👥")

    st.header("✨ Your AI-Generated Creative Content", divider="gray")
    with st.spinner("Our creative AI is brainstorming for you... This may take a moment."):
        
        base_prompt_info = f"""
        **Expert's Information:**
        * Role: {data.get('role')} | Method: {data.get('method')}
        * Client Problem: "{data.get('problem')}" | Expertise: "{data.get('expertise')}"
        """
        
        single_lesson_prompt = f"""
        You are an expert curriculum designer. Your task is to brainstorm 4-5 specific, actionable ideas for a SINGLE LESSON based on the expert's profile and chosen category. Your goal is to provide the *substance* of what the lesson could be about.

        {base_prompt_info}
        * **Chosen Lesson Category:** {data.get('category')}

        **Your Task:**
        Generate 4-5 concrete lesson ideas. For each idea, provide:
        1. A clear, descriptive **Title**.
        2. A **Concept** (1-2 sentences explaining what the student will learn and do, tailored to the chosen category).
        
        Format the output using Markdown with a clear heading for each idea.
        """

        full_program_prompt = f"""
        You are an expert instructional designer. Your task is to create a detailed outline for a FULL 12-LESSON MONTHLY PROGRAM based on the expert's transformation method.
        {base_prompt_info}
        **Expert's Transformation Method:**
        * **Starting Point (A):** {data.get('point_a')}
        * **Ending Result (B):** {data.get('point_b')}
        * **Method Description:** {data.get('method_desc')}
        * **IMPORTANT Program Structure:** The 12 lessons are delivered over ONE MONTH (3 lessons per week). All of your generated text must reflect this monthly timeline.
        **Your Tasks:**
        1.  **Write a Full Program Description:** Write an engaging description (3-4 sentences) for the one-month program.
        2.  **Generate Title and Tagline Ideas:** Generate 4 creative titles for the full program, each with a tagline.
        3.  **Create a 4-Week Lesson Outline:** Based on the expert's A->B method, create a logical, 4-week lesson plan. Each week should contain 3 lesson titles. For each lesson, provide a one-sentence description of what the client will learn.
        Format the entire output using Markdown with clear headings.
        """

        if data.get('goal') == 'single_lesson':
            st.markdown("### Brainstorming Your Single Lesson")
            st.info("Here are some AI-generated ideas to help you brainstorm the content of your lesson.", icon="🧠")
            creative_content = generate_content(single_lesson_prompt)
            if creative_content:
                with st.container(border=True):
                    st.markdown(creative_content)
            
            # ** NEW "WHAT'S NEXT" SECTION **
            st.success("What to Do Next:", icon="✅")
            st.markdown("""
            1.  **Choose one idea** from the list above that you're most excited about.
            2.  **Edit and refine it** until it perfectly matches your vision.
            3.  **Copy your final idea** and take it to our **Lesson Blueprint Bot** to generate the full structure and script for your video.
            """)
            st.link_button("Go to Lesson Blueprint Bot", "YOUR_LINK_TO_THE_SECOND_BOT_HERE")
            
            if data.get('time') == '3-4 hours a week':
                st.write("---")
                if st.button("Ready to Plan Your Full Program?", use_container_width=True, type="primary"):
                    st.session_state.form_data['goal'] = 'full_program_after_lesson'
                    set_stage(2)
                    st.rerun()

        elif data.get('goal') == 'full_program':
            st.markdown("### Your Full Program Content & Outline")
            creative_content = generate_content(full_program_prompt)
            if creative_content:
                with st.container(border=True):
                    st.markdown(creative_content)

        elif data.get('goal') == 'combo':
            st.markdown("### Part 1: Brainstorming Your Single Lesson")
            st.info("Here are AI-generated ideas for the single lesson you can create now.", icon="⚡")
            single_lesson_content = generate_content(single_lesson_prompt)
            if single_lesson_content:
                with st.container(border=True):
                    st.markdown(single_lesson_content)
            
            st.markdown("### Part 2: Your Full Program Outline")
            st.info("And here is the detailed outline for the full program you can build next.", icon="🗺️")
            full_program_content = generate_content(full_program_prompt)
            if full_program_content:
                with st.container(border=True):
                    st.markdown(full_program_content)

    if st.button("Start Over", use_container_width=True):
        st.session_state.stage = 0
        st.session_state.form_data = {}
        st.rerun()

