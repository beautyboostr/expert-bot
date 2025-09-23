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
    """Scans user text against keywords to find the best recommendation row."""
    if not user_problem_text or not isinstance(user_problem_text, str): return None
    user_words = set(user_problem_text.lower().replace(",", " ").split())
    
    best_match_score = 0
    best_match_row = None

    for index, row in recommendations_df.iterrows():
        search_keywords = set(str(row['search_keywords']).split(','))
        matches = user_words.intersection(search_keywords)
        if len(matches) > best_match_score:
            best_match_score = len(matches)
            best_match_row = row
            
    return best_match_row

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
        q2_options = ["Educational content", "Hands-on (no equipment)", "Hands-on (with equipment)", "Hands-on (posture/body)"]
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
                else: 
                    st.session_state.form_data['goal'] = 'single_lesson'
                    set_stage(3) 
                st.rerun()

# STAGE 1: Decision Point for 3-4 Hour Users
if st.session_state.stage == 1:
    st.header("🤔 Step 3: What is Your Goal Right Now?", divider="gray")
    st.write("With 3-4 hours per week, you have two great options. What would you like to focus on now?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create a Single Lesson", use_container_width=True, type="primary"):
            st.session_state.form_data['goal'] = 'single_lesson'
            set_stage(3)
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
                set_stage(5) 
                st.rerun()

# STAGE 3: CATEGORY SELECTION FOR SINGLE LESSON
# This stage is for users with 1-2 hours, or 3-4 hours who chose "Single Lesson"
if st.session_state.stage == 3:
    st.header("📚 Step 3: Choose a Lesson Category", divider="gray")
    st.info("To give you the best ideas, please select the category for your single lesson.", icon="✨")
    
    lesson_categories = [
        "Educational content",
        "Hands-on (no equipment)",
        "Hands-on (with equipment)",
        "Hands-on (posture/body)"
    ]
    
    category = st.selectbox("Select your lesson category (Required)", lesson_categories, index=None, placeholder="Choose a category...")
    
    if st.button("Next Step", use_container_width=True, type="primary"):
        if not category:
            st.error("⚠️ Please select a category to continue.")
        else:
            st.session_state.form_data['category'] = category
            if category == "Hands-on (with equipment)":
                set_stage(4) # Go to new equipment selection stage
            else:
                set_stage(5) # Go directly to final blueprint
            st.rerun()

# STAGE 4: EQUIPMENT SELECTION
if st.session_state.stage == 4:
    st.header("⚙️ Step 4: Select Your Equipment", divider="gray")
    st.info("Which specific tool will this lesson focus on?", icon="✨")

    equipment_list = ["Guasha", "Facial Cups", "Kansa Wand", "Facial Roller", "Microcurrent Device", "LED Therapy Mask", "Other"]
    equipment = st.selectbox("Select your primary tool (Required)", equipment_list, index=None, placeholder="Choose your equipment...")

    if st.button("Generate My Lesson Blueprint", use_container_width=True, type="primary"):
        if not equipment:
            st.error("⚠️ Please select your equipment to continue.")
        else:
            st.session_state.form_data['equipment'] = equipment
            set_stage(5) # Go to final blueprint
            st.rerun()


# STAGE 5: Final Blueprint Generation
if st.session_state.stage == 5:
    st.header("🚀 Your Program Blueprint", divider="gray")
    data = st.session_state.form_data
    problem_specific_rec = find_problem_recommendation(data.get('problem', ''), problem_rec_df)

    with st.container(border=True):
        st.subheader("Key Recommendations:")
        time_based_rec = recommendations_df[recommendations_df['condition_time'] == data.get('time')]
        if not time_based_rec.empty:
            st.success(time_based_rec['recommendation_text'].iloc[0], icon="🕒")

        if problem_specific_rec is not None:
            expert_method = data.get('category', data.get('method'))
            
            st.markdown("**Recommended Content Ideas:**")
            
            ideas_to_show = ""
            if expert_method == "Educational content":
                ideas_to_show = problem_specific_rec.get('educational_ideas')
            elif expert_method == "Hands-on (no equipment)":
                ideas_to_show = problem_specific_rec.get('hands_on_no_equipment_ideas')
            elif expert_method == "Hands-on (with equipment)":
                ideas_to_show = problem_specific_rec.get('hands_on_with_equipment_ideas')
            elif expert_method == "Hands-on (posture/body)":
                ideas_to_show = problem_specific_rec.get('hands_on_posture_ideas')

            if pd.notna(ideas_to_show):
                lesson_ideas = str(ideas_to_show).split('|')
                for idea in lesson_ideas:
                    st.info(f"💡 {idea.strip()}")
            
            if 'client_target_audience' in problem_specific_rec and pd.notna(problem_specific_rec['client_target_audience']):
                st.info(f"**Ideal Client Target Audience:** {problem_specific_rec['client_target_audience']}", icon="👥")

    st.header("✨ Your AI-Generated Creative Content", divider="gray")
    with st.spinner("Our creative AI is brainstorming for you... This may take a moment."):
        
        base_prompt_info = f"""
        You are an expert curriculum designer creating content for a high-end skincare app. The expert is crafting a lesson for their clients to perform on themselves at home. All ideas must be framed as self-care routines.

        **Expert's Information:**
        * Role: {data.get('role')}
        * Client Problem/Goal: "{data.get('problem')}"
        * Expertise: "{data.get('expertise')}"
        """
        
        equipment_info = ""
        if data.get('equipment'):
            equipment_info = f"* **Specific Equipment:** {data.get('equipment')}"

        single_lesson_prompt = f"""
        {base_prompt_info}
        * **Chosen Lesson Category:** {data.get('category')}
        {equipment_info}

        **Your Task:**
        Generate 4-5 concrete lesson ideas for a **self-care lesson**. For each idea, provide:
        1. An empowering **Self-Care Title**.
        2. A **Self-Care Concept** (1-2 sentences explaining the routine the client will learn and the benefit they will feel).
        
        Format the output using Markdown with a clear heading for each idea.
        """

        full_program_prompt = f"""
        {base_prompt_info}

        **Expert's Transformation Method for a Self-Care Program:**
        * **Client's Starting Point (A):** {data.get('point_a')}
        * **Client's Transformation (B):** {data.get('point_b')}
        * **Expert's Method:** {data.get('method_desc')}
        * **Program Structure:** 12 lessons delivered over ONE MONTH (3 lessons per week).

        **Your Tasks:**
        1.  **Write a Full Program Description:** Write an engaging, client-focused description (3-4 sentences) for the one-month self-care journey.
        2.  **Generate Empowering Title and Tagline Ideas:** Generate 4 creative titles for the program, each with a tagline that speaks to the client's transformation.
        3.  **Create a 4-Week Self-Care Lesson Outline:** Create a logical, 4-week lesson plan. Frame each of the 12 lesson titles as a skill or routine the client will learn for themselves.
        
        Format the entire output using Markdown with clear headings.
        """

        if data.get('goal') == 'single_lesson':
            st.markdown("### Brainstorming Your Single Lesson")
            st.info("Here are some AI-generated ideas for your self-care lesson.", icon="🧠")
            creative_content = generate_content(single_lesson_prompt)
            if creative_content:
                with st.container(border=True):
                    st.markdown(creative_content)
            
            st.success("What to Do Next:", icon="✅")
            st.markdown("""
            1.  **Choose one idea** from the list above that you're most excited about.
            2.  **Edit and refine it** until it perfectly matches your vision.
            3.  **Copy your final idea** and take it to our **Lesson Blueprint Bot** to generate the full structure and script for your video.
            """)
            st.link_button("Go to Lesson Blueprint Bot", "https://individual.streamlit.app/")
            
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
            st.info("Here are AI-generated ideas for the single self-care lesson you can create now.", icon="⚡")
            single_lesson_content = generate_content(single_lesson_prompt)
            if single_lesson_content:
                with st.container(border=True):
                    st.markdown(single_lesson_content)
            
            st.markdown("### Part 2: Your Full Program Outline")
            st.info("And here is the detailed outline for the full self-care program you can build next.", icon="🗺️")
            full_program_content = generate_content(full_program_prompt)
            if full_program_content:
                with st.container(border=True):
                    st.markdown(full_program_content)

    if st.button("Start Over", use_container_width=True):
        st.session_state.stage = 0
        st.session_state.form_data = {}
        st.rerun()

