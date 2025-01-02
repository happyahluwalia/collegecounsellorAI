import streamlit as st
from agents.orchestrator import AgentOrchestrator
from utils.error_handling import handle_error, DatabaseError, ValidationError
import logging
import traceback

logger = logging.getLogger(__name__)

def init_chat():
    """Initialize chat session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'agent_orchestrator' not in st.session_state:
        try:
            logger.info("Initializing AgentOrchestrator")
            st.session_state.agent_orchestrator = AgentOrchestrator()
            logger.info("AgentOrchestrator initialized successfully")
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Failed to initialize AgentOrchestrator: {str(e)}\n{error_trace}")
            raise Exception(f"Failed to initialize AI system: {str(e)}")
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None

@handle_error
def load_chat_session(session_id):
    """Load messages from a specific chat session."""
    if not hasattr(st.session_state, 'user'):
        raise ValidationError("Please log in to access chat sessions")

    try:
        db = st.session_state.user.db
        messages = db.execute(
            """
            SELECT content, role 
            FROM messages 
            WHERE session_id = %s 
            ORDER BY created_at
            """,
            (session_id,)
        )
        st.session_state.messages = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in messages
        ]
        st.session_state.current_session_id = session_id
        logger.info(f"Loaded chat session {session_id}")
    except DatabaseError as e:
        error_trace = traceback.format_exc()
        logger.error(f"Failed to load chat session {session_id}: {str(e)}\n{error_trace}")
        raise DatabaseError("Unable to load chat history")

@handle_error
def render_chat():
    """Render the chat interface with multi-agent counseling system."""
    try:
        init_chat()
        st.subheader("Chat with your AI College Counseling Team")

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
            try:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get context from user profile if available
                context = {}
                if hasattr(st.session_state, 'user'):
                    try:
                        profile = st.session_state.user.get_profile()
                        if profile:
                            context["profile"] = profile
                    except Exception as profile_error:
                        logger.warning(f"Failed to get user profile: {str(profile_error)}")

                # Show typing indicator
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            # Process message through agent orchestrator
                            logger.info(f"Processing message through agent orchestrator: {prompt[:100]}...")
                            response = st.session_state.agent_orchestrator.process_message(
                                prompt,
                                st.session_state.user.id if hasattr(st.session_state, 'user') else None
                            )
                            logger.info("Successfully got response from agent orchestrator")

                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})

                            # Save chat session if user is authenticated
                            if hasattr(st.session_state, 'user') and st.session_state.user:
                                save_chat_session(prompt, response)
                                logger.info("Chat message saved successfully")

                        except Exception as agent_error:
                            error_trace = traceback.format_exc()
                            logger.error(f"Error in agent processing: {str(agent_error)}\n{error_trace}")
                            raise Exception(f"Failed to process message: {str(agent_error)}")

            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error(f"Error in chat interaction: {str(e)}\n{error_trace}")
                st.error("😕 Something went wrong. Please try again.")
                if st.checkbox("Show Error Details"):
                    st.code(error_trace)

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in render_chat: {str(e)}\n{error_trace}")
        st.error("😔 Something went wrong. Our team has been notified.")
        if st.checkbox("Show Error Details"):
            st.code(error_trace)

@handle_error
def new_chat_session():
    """Start a new chat session."""
    st.session_state.messages = []
    st.session_state.current_session_id = None
    logger.info("Started new chat session")

@handle_error
def save_chat_session(prompt, response):
    """Save chat messages to the database."""
    try:
        user = st.session_state.user
        db = user.db

        # Create new session if needed
        if not st.session_state.current_session_id:
            result = db.execute_one(
                "INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s) RETURNING id",
                (user.id, prompt[:50] + "...")
            )
            st.session_state.current_session_id = result['id']
            logger.info(f"Created new chat session {result['id']}")

        # Save messages
        session_id = st.session_state.current_session_id
        db.execute(
            "INSERT INTO messages (session_id, content, role) VALUES (%s, %s, %s), (%s, %s, %s)",
            (session_id, prompt, 'user', session_id, response, 'assistant')
        )
        logger.info(f"Saved messages to session {session_id}")
    except DatabaseError as e:
        error_trace = traceback.format_exc()
        logger.error(f"Failed to save chat session: {str(e)}\n{error_trace}")
        raise DatabaseError("Failed to save chat messages")

# Make sure the functions are properly exported
__all__ = ['render_chat', 'new_chat_session', 'load_chat_session']