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
            st.session_state.form_data['goal'] = 'full_program'
            set_stage(2) # Go to deep dive
            st.rerun()

# STAGE 2: Deep Dive for Full Program Outline
if st.session_state.stage == 2:
    st.header("Step 3: Define Your Program's Transformation", divider="rainbow")
    st.info("To create a great program outline, we need to understand the journey you provide.", icon="🗺️")
    with st.form("expert_form_2"):
        point_a = st.text_area("Client's Starting Point (Point A)", placeholder="Example: My client has painful, inflamed cystic acne and feels hopeless.")
        point_b = st.text_area("Client's Transformation (Point B)", placeholder="Example: My client will have calm, clear skin and feel confident and in control.")
        method_desc = st.text_area("Your Unique Method", placeholder="Example: My method involves three phases: 1. Calming inflammation with gentle techniques. 2. Rebuilding the skin barrier. 3. Creating a long-term maintenance plan.")
        
        submitted = st.form_submit_button("Generate My Program Blueprint", use_container_width=True, type="primary")
        if submitted:
            st.session_state.form_data.update({
                "point_a": point_a, "point_b": point_b, "method_desc": method_desc
            })
            if st.session_state.form_data.get('time') == '3-4 hours a week':
                st.session_state.form_data['goal'] = 'combo'
            else:
                st.session_state.form_data['goal'] = 'full_program'
            set_stage(3) # Go to final blueprint
            st.rerun()

# STAGE 3: Final Blueprint Generation
if st.session_state.stage == 3:
    st.header("🚀 Your Program Blueprint", divider="rainbow")
    data = st.session_state.form_data
    problem_specific_rec = find_problem_recommendation(data.get('problem', ''), problem_rec_df)

    with st.container(border=True):
        st.subheader("Key Recommendations:")
        time_based_rec = recommendations_df[recommendations_df['condition_time'] == data.get('time')]
        if not time_based_rec.empty:
            st.success(time_based_rec['recommendation_text'].iloc[0], icon="🕒")

        if problem_specific_rec is not None:
            if data.get('goal') in ['full_program', 'combo'] or data.get('time') == '8-10 hours a week':
                st.info(f"**Recommended Content Type (for Full Program):** {problem_specific_rec['recommended_program']}", icon="💡")
            else:
                st.info(f"**Recommended Content Type (for Single Lesson):** {problem_specific_rec['recommended_content']}", icon="💡")
            
            if 'client_target_audience' in problem_specific_rec and pd.notna(problem_specific_rec['client_target_audience']):
                st.info(f"**Ideal Client Target Audience:** {problem_specific_rec['client_target_audience']}", icon="👥")

    st.header("✨ Your AI-Generated Creative Content", divider="rainbow")
    with st.spinner("Our creative AI is brainstorming for you... This may take a moment."):
        
        base_prompt_info = f"""
        **Expert's Information:**
        * Role: {data.get('role')} | Method: {data.get('method')}
        * Client Problem: "{data.get('problem')}" | Expertise: "{data.get('expertise')}"
        """
        
        # PROMPTS FOR SINGLE LESSONS
        if data.get('method') == 'Educational content':
            single_lesson_prompt = f"""
            You are an expert curriculum designer. Your task is to brainstorm 4-5 specific, actionable ideas for a SINGLE EDUCATIONAL LESSON based on the expert's profile.
            {base_prompt_info}
            **Your Tasks:**
            1.  **State Lesson Length:** Start by recommending the ideal lesson length is **5-12 minutes**.
            2.  **Generate 4-5 Concrete Lesson Ideas:** For each idea, provide a clear title and a 1-2 sentence description of what the client will learn and do. These ideas must be highly specific and based on the expert's problem and expertise.
            Format the output using Markdown with a clear heading for the lesson ideas.
            """
        else: # For "Hands-on techniques"
            single_lesson_prompt = f"""
            You are an expert instructional designer. Generate creative marketing content for a SINGLE, HANDS-ON LESSON (e.g., face massage, yoga) based on the expert's information.
            {base_prompt_info}
            **Your Tasks:**
            1.  **Write a Lesson Description:** Create a short, engaging description (3-4 sentences) that focuses on the physical practice and its benefits.
            2.  **Generate Title and Tagline Ideas:** Generate 4 creative titles for this single lesson, each with a compelling, benefit-driven tagline.
            Format the output using Markdown.
            """

        # PROMPT FOR FULL PROGRAM
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

        # LOGIC TO HANDLE ALL CASES
        if data.get('goal') == 'single_lesson' or data.get('time') == '1-2 hours':
            st.markdown("### Part 1: Your Single Lesson Content")
            creative_content = generate_content(single_lesson_prompt)
            if creative_content:
                with st.container(border=True):
                    st.markdown(creative_content)

        elif data.get('goal') == 'full_program':
            st.markdown("### Your Full Program Content & Outline")
            creative_content = generate_content(full_program_prompt)
            if creative_content:
                with st.container(border=True):
                    st.markdown(creative_content)

        elif data.get('goal') == 'combo':
            st.markdown("### Part 1: Your Single Lesson Content")
            st.info("Here are creative ideas for the single lesson you can create now.", icon="⚡")
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
        st.rerun()        if row['problem_keyword'].lower() in user_problem_text.lower(): return row
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
            st.session_state.form_data['goal'] = 'full_program'
            set_stage(2) # Go to deep dive
            st.rerun()

# STAGE 2: Deep Dive for Full Program Outline
if st.session_state.stage == 2:
    st.header("Step 3: Define Your Program's Transformation", divider="rainbow")
    st.info("To create a great program outline, we need to understand the journey you provide.", icon="🗺️")
    with st.form("expert_form_2"):
        point_a = st.text_area("Client's Starting Point (Point A)", placeholder="Example: My client has painful, inflamed cystic acne and feels hopeless.")
        point_b = st.text_area("Client's Transformation (Point B)", placeholder="Example: My client will have calm, clear skin and feel confident and in control.")
        method_desc = st.text_area("Your Unique Method", placeholder="Example: My method involves three phases: 1. Calming inflammation with gentle techniques. 2. Rebuilding the skin barrier. 3. Creating a long-term maintenance plan.")
        
        submitted = st.form_submit_button("Generate My Program Blueprint", use_container_width=True, type="primary")
        if submitted:
            st.session_state.form_data.update({
                "point_a": point_a, "point_b": point_b, "method_desc": method_desc
            })
            if st.session_state.form_data.get('time') == '3-4 hours a week':
                st.session_state.form_data['goal'] = 'combo'
            else:
                st.session_state.form_data['goal'] = 'full_program'
            set_stage(3) # Go to final blueprint
            st.rerun()

# STAGE 3: Final Blueprint Generation
if st.session_state.stage == 3:
    st.header("🚀 Your Program Blueprint", divider="rainbow")
    data = st.session_state.form_data
    problem_specific_rec = find_problem_recommendation(data.get('problem', ''), problem_rec_df)

    with st.container(border=True):
        st.subheader("Key Recommendations:")
        time_based_rec = recommendations_df[recommendations_df['condition_time'] == data.get('time')]
        if not time_based_rec.empty:
            st.success(time_based_rec['recommendation_text'].iloc[0], icon="🕒")

        if problem_specific_rec is not None:
            if data.get('goal') in ['full_program', 'combo'] or data.get('time') == '8-10 hours a week':
                st.info(f"**Recommended Content Type (for Full Program):** {problem_specific_rec['recommended_program']}", icon="💡")
            else:
                st.info(f"**Recommended Content Type (for Single Lesson):** {problem_specific_rec['recommended_content']}", icon="💡")
            
            if 'client_target_audience' in problem_specific_rec and pd.notna(problem_specific_rec['client_target_audience']):
                st.info(f"**Ideal Client Target Audience:** {problem_specific_rec['client_target_audience']}", icon="👥")

    st.header("✨ Your AI-Generated Creative Content", divider="rainbow")
    with st.spinner("Our creative AI is brainstorming for you... This may take a moment."):
        
        base_prompt_info = f"""
        **Expert's Information:**
        * Role: {data.get('role')} | Method: {data.get('method')}
        * Client Problem: "{data.get('problem')}" | Expertise: "{data.get('expertise')}"
        """
        
        # PROMPTS FOR SINGLE LESSONS
        if data.get('method') == 'Educational content':
            single_lesson_prompt = f"""
            You are an expert curriculum designer. Your task is to brainstorm 4-5 specific, actionable ideas for a SINGLE EDUCATIONAL LESSON based on the expert's profile.
            {base_prompt_info}
            **Your Tasks:**
            1.  **State Lesson Length:** Start by recommending the ideal lesson length is **5-12 minutes**.
            2.  **Generate 4-5 Concrete Lesson Ideas:** For each idea, provide a clear title and a 1-2 sentence description of what the client will learn and do. These ideas must be highly specific and based on the expert's problem and expertise.
            Format the output using Markdown with a clear heading for the lesson ideas.
            """
        else: # For "Hands-on techniques"
            single_lesson_prompt = f"""
            You are an expert instructional designer. Generate creative marketing content for a SINGLE, HANDS-ON LESSON (e.g., face massage, yoga) based on the expert's information.
            {base_prompt_info}
            **Your Tasks:**
            1.  **Write a Lesson Description:** Create a short, engaging description (3-4 sentences) that focuses on the physical practice and its benefits.
            2.  **Generate Title and Tagline Ideas:** Generate 4 creative titles for this single lesson, each with a compelling, benefit-driven tagline.
            Format the output using Markdown.
            """

        # PROMPT FOR FULL PROGRAM
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

        # LOGIC TO HANDLE ALL CASES
        if data.get('goal') == 'single_lesson' or data.get('time') == '1-2 hours':
            st.markdown("### Part 1: Your Single Lesson Content")
            creative_content = generate_content(single_lesson_prompt)
            if creative_content:
                with st.container(border=True):
                    st.markdown(creative_content)

        elif data.get('goal') == 'full_program':
            st.markdown("### Your Full Program Content & Outline")
            creative_content = generate_content(full_program_prompt)
            if creative_content:
                with st.container(border=True):
                    st.markdown(creative_content)

        elif data.get('goal') == 'combo':
            st.markdown("### Part 1: Your Single Lesson Content")
            st.info("Here are creative ideas for the single lesson you can create now.", icon="⚡")
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
        st.rerun()                    st.markdown(full_program_content)


    if st.button("Start Over", use_container_width=True):
        st.session_state.stage = 0
        st.session_state.form_data = {}
        st.rerun()        if row['problem_keyword'].lower() in user_problem_text.lower(): return row
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
            st.session_state.form_data['goal'] = 'full_program'
            set_stage(2) # Go to deep dive
            st.rerun()

# STAGE 2: Deep Dive for Full Program Outline
if st.session_state.stage == 2:
    st.header("Step 3: Define Your Program's Transformation", divider="rainbow")
    st.info("To create a great program outline, we need to understand the journey you provide.", icon="🗺️")
    with st.form("expert_form_2"):
        point_a = st.text_area("Client's Starting Point (Point A)", placeholder="Example: My client has painful, inflamed cystic acne and feels hopeless.")
        point_b = st.text_area("Client's Transformation (Point B)", placeholder="Example: My client will have calm, clear skin and feel confident and in control.")
        method_desc = st.text_area("Your Unique Method", placeholder="Example: My method involves three phases: 1. Calming inflammation with gentle techniques. 2. Rebuilding the skin barrier. 3. Creating a long-term maintenance plan.")
        
        submitted = st.form_submit_button("Generate My Program Blueprint", use_container_width=True, type="primary")
        if submitted:
            st.session_state.form_data.update({
                "point_a": point_a, "point_b": point_b, "method_desc": method_desc
            })
            st.session_state.form_data['goal'] = 'full_program' # Ensure goal is set
            set_stage(3) # Go to final blueprint
            st.rerun()

# STAGE 3: Final Blueprint Generation
if st.session_state.stage == 3:
    st.header("🚀 Your Program Blueprint", divider="rainbow")
    data = st.session_state.form_data
    problem_specific_rec = find_problem_recommendation(data.get('problem', ''), problem_rec_df)

    with st.container(border=True):
        st.subheader("Key Recommendations:")
        time_based_rec = recommendations_df[recommendations_df['condition_time'] == data.get('time')]
        if not time_based_rec.empty:
            st.success(time_based_rec['recommendation_text'].iloc[0], icon="🕒")

        if problem_specific_rec is not None:
            # Logic to show the right content focus
            if data.get('goal') == 'full_program' or data.get('time') == '8-10 hours a week':
                st.info(f"**Recommended Content Type:** {problem_specific_rec['recommended_program']}", icon="💡")
            else:
                st.info(f"**Recommended Content Type:** {problem_specific_rec['recommended_content']}", icon="💡")
            
            if 'client_target_audience' in problem_specific_rec and pd.notna(problem_specific_rec['client_target_audience']):
                st.info(f"**Ideal Client Target Audience:** {problem_specific_rec['client_target_audience']}", icon="👥")

    st.header("✨ Your AI-Generated Creative Content", divider="rainbow")
    with st.spinner("Our creative AI is brainstorming for you... This may take a moment."):
        prompt_for_gemini = ""
        base_prompt_info = f"""
        **Expert's Information:**
        * Role: {data.get('role')} | Method: {data.get('method')}
        * Client Problem: "{data.get('problem')}" | Expertise: "{data.get('expertise')}"
        """

        # Generate prompt for single lesson
        if data.get('goal') == 'single_lesson' or data.get('time') == '1-2 hours':
            prompt_for_gemini = f"""
            You are an expert instructional designer. Generate creative ideas for a SINGLE, FOCUSED ADDITIONAL LESSON based on the expert's information.
            {base_prompt_info}
            **Your Tasks:**
            1.  **Write a Lesson Description:** Create a short, engaging description (3-4 sentences).
            2.  **Generate Title and Tagline Ideas:** Generate 4 creative titles for this single lesson, each with a compelling one-sentence tagline.
            Format the output using Markdown.
            """
        # Generate prompt for full program
        elif data.get('goal') == 'full_program':
            prompt_for_gemini = f"""
            You are an expert instructional designer. Your task is to create a detailed outline for a FULL 12-LESSON MONTHLY PROGRAM based on the expert's transformation method.
            {base_prompt_info}
            **Expert's Transformation Method:**
            * **Starting Point (A):** {data.get('point_a')}
            * **Ending Result (B):** {data.get('point_b')}
            * **Method Description:** {data.get('method_desc')}

            **Your Tasks:**
            1.  **Write a Full Program Description:** Write an engaging description (3-4 sentences) for the program.
            2.  **Generate Title and Tagline Ideas:** Generate 4 creative titles for the full program, each with a tagline.
            3.  **Create a 12-Week Lesson Outline:** Based on the expert's A->B method, create a logical, week-by-week lesson plan. Each week should have a clear title and a one-sentence description of what the client will learn.
            
            Format the entire output using Markdown with clear headings.
            """

        creative_content = generate_content(prompt_for_gemini)
        if creative_content:
            with st.container(border=True):
                st.markdown(creative_content)

    if st.button("Start Over", use_container_width=True):
        st.session_state.stage = 0
        st.session_state.form_data = {}
        st.rerun()
