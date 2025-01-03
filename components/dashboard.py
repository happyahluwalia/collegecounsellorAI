import streamlit as st
from components.profile import render_profile
from components.chat import render_chat, new_chat_session
from components.achievements import render_achievements
from components.college_matches import render_college_matches
from components.timeline import render_timeline
from components.internships import render_internships
from components.college_explorer import render_college_explorer
from models.achievement import Achievement
from utils.error_handling import handle_error, DatabaseError
import logging
import traceback

logger = logging.getLogger(__name__)

def show_error_message(error_message: str, error_trace: str = None):
    """Display an error message with expandable details."""
    st.error(error_message)
    if error_trace:
        with st.expander("Show Error Details"):
            st.code(error_trace)

@handle_error
def render_dashboard():
    """Renders the main dashboard interface of the College Compass application."""
    st.title("College Compass Dashboard")

    try:
        # Initialize achievements if needed
        Achievement.initialize_default_achievements()
    except DatabaseError as e:
        error_trace = traceback.format_exc()
        logger.error(f"Failed to initialize achievements: {str(e)}\n{error_trace}")
        show_error_message("System initialization error. Please try again later.", error_trace)

    # Create three columns for the layout
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.subheader("Quick Links")
        if st.button("New Chat Session"):
            new_chat_session()
            logger.info("Started new chat session")

        st.subheader("Recent Sessions")
        if hasattr(st.session_state, 'user'):
            try:
                sessions = st.session_state.user.get_chat_sessions()
                for session in sessions:
                    if st.button(f"📝 {session['title']}", key=f"session_{session['id']}"):
                        #load_chat_session(session['id'])  #load_chat_session removed as per the edit
                        logger.info(f"Loaded chat session {session['id']}")
                        st.rerun()
            except DatabaseError as e:
                error_trace = traceback.format_exc()
                logger.error(f"Failed to load chat sessions: {str(e)}\n{error_trace}")
                show_error_message("Unable to load chat history", error_trace)

    with col2:
        # Initialize active tab if not present
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = "Chat"

        # Create tabs
        tabs = st.tabs(["Chat", "College Explorer", "College Matches", "Timeline", "Internships", "Profile"])

        # Render content for each tab
        with tabs[0]:  # Chat tab
            render_chat()

        with tabs[1]:  # College Explorer tab
            render_college_explorer()

        with tabs[2]:  # College Matches tab
            render_college_matches()

        with tabs[3]:  # Timeline tab
            render_timeline()

        with tabs[4]:  # Internships tab
            render_internships()

        with tabs[5]:  # Profile tab
            render_profile()

    with col3:
        # Render achievements panel
        render_achievements()

# Make render_dashboard available at the module level
# This ensures it can be imported directly
if not globals().get('render_dashboard'):
    globals()['render_dashboard'] = render_dashboard