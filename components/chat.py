import streamlit as st
from agents.counselor import CounselorAgent
from agents.validator import ValidatorAgent

def init_chat():
    """Initialize chat session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'counselor' not in st.session_state:
        st.session_state.counselor = CounselorAgent()
    if 'validator' not in st.session_state:
        st.session_state.validator = ValidatorAgent()
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None

def render_chat():
    """Render the chat interface with enhanced counseling features."""
    init_chat()
    st.subheader("Chat with your AI College Counselor")

    # Add quick action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎯 Get College Suggestions"):
            prompt = "Based on my profile, what colleges would you recommend?"
            st.session_state.messages.append({"role": "user", "content": prompt})
    with col2:
        if st.button("📈 Improve Application"):
            prompt = "How can I improve my college application?"
            st.session_state.messages.append({"role": "user", "content": prompt})
    with col3:
        if st.button("❓ Common Questions"):
            prompt = "What are the key steps in the college application process?"
            st.session_state.messages.append({"role": "user", "content": prompt})

    # Display chat messages with improved styling
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask your college admissions question..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get context from user profile if available
        context = {}
        if hasattr(st.session_state, 'user'):
            profile = st.session_state.user.get_profile()
            if profile:
                context["profile"] = profile

        # Show typing indicator
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Get AI response with context
                response = st.session_state.counselor.get_response(prompt, context)

                # Validate response
                validated_response = st.session_state.validator.validate_response(response)

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

        # Save chat session if user is authenticated
        if hasattr(st.session_state, 'user') and st.session_state.user:
            save_chat_session(prompt, response)

def new_chat_session():
    """Start a new chat session."""
    st.session_state.messages = []
    st.session_state.current_session_id = None

def save_chat_session(prompt, response):
    """Save chat messages to the database."""
    user = st.session_state.user
    db = user.db

    # Create new session if needed
    if not st.session_state.current_session_id:
        result = db.execute_one(
            "INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s) RETURNING id",
            (user.id, prompt[:50] + "...")
        )
        st.session_state.current_session_id = result['id']

    # Save messages
    session_id = st.session_state.current_session_id
    db.execute(
        "INSERT INTO messages (session_id, content, role) VALUES (%s, %s, %s), (%s, %s, %s)",
        (session_id, prompt, 'user', session_id, response, 'assistant')
    )