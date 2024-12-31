import streamlit as st
from components.profile import render_profile
from components.chat import render_chat

def render_dashboard():
    st.title("College Compass Dashboard")
    
    # Create three columns for the layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.subheader("Quick Links")
        if st.button("New Chat Session"):
            st.session_state.messages = []
        
        st.subheader("Recent Sessions")
        sessions = st.session_state.user.get_chat_sessions()
        for session in sessions:
            if st.button(f"📝 {session['title']}", key=f"session_{session['id']}"):
                # Load selected session
                pass

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
