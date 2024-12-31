import streamlit as st
from components.profile import render_profile
from components.chat import render_chat, new_chat_session, load_chat_session
from utils.error_handling import handle_error, DatabaseError
import logging

logger = logging.getLogger(__name__)

@handle_error
def render_dashboard():
    """Renders the main dashboard interface of the College Compass application."""
    st.title("College Compass Dashboard")

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
                        load_chat_session(session['id'])
                        logger.info(f"Loaded chat session {session['id']}")
                        st.rerun()
            except DatabaseError as e:
                logger.error(f"Failed to load chat sessions: {str(e)}")
                st.error("Unable to load chat history")

    with col2:
        tab1, tab2 = st.tabs(["Chat", "Profile"])

        with tab1:
            render_chat()

        with tab2:
            render_profile()

    with col3:
        st.subheader("Progress Tracker")

        # Progress bars
        st.progress(0.7, "Profile Completion")
        st.progress(0.3, "College List")
        st.progress(0.5, "Essay Planning")

        # Upcoming Tasks
        st.subheader("Upcoming Tasks")
        tasks = [
            "Complete profile information",
            "Research target schools",
            "Draft personal statement",
            "Prepare activity list"
        ]

        for task in tasks:
            st.checkbox(task, key=f"task_{task}")

# Make sure the function is properly exported
__all__ = ['render_dashboard']