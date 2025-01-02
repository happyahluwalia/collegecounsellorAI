import streamlit as st
from agents.orchestrator import AgentOrchestrator
from utils.error_handling import handle_error, DatabaseError, ValidationError, AgentError
import logging
import traceback
import asyncio

logger = logging.getLogger(__name__)

def init_chat():
    """Initialize chat session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None
    if 'error_details' not in st.session_state:
        st.session_state.error_details = None
    if 'agent_orchestrator' not in st.session_state:
        try:
            logger.info("Initializing AgentOrchestrator")
            st.session_state.agent_orchestrator = AgentOrchestrator()
            logger.info("AgentOrchestrator initialized successfully")
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Failed to initialize AgentOrchestrator: {str(e)}\n{error_trace}")
            st.session_state.error_message = "Failed to initialize AI system"
            st.session_state.error_details = error_trace
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None

def add_to_plan(actionable_item):
    """Add an actionable item to the student's plan"""
    try:
        if not hasattr(st.session_state, 'user'):
            st.warning("Please log in to add items to your plan")
            return

        db = st.session_state.user.db
        user_id = st.session_state.user.id

        # Add to plan table
        db.execute(
            """
            INSERT INTO plan_items 
            (user_id, category, year, url, status)
            VALUES (%s, %s, %s, %s, 'pending')
            """,
            (user_id, actionable_item["category"], actionable_item["year"], actionable_item.get("url"))
        )
        st.success("Added to your plan! 🎯")
        logger.info(f"Added actionable item to plan for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to add item to plan: {str(e)}")
        st.error("Failed to add item to your plan. Please try again.")

@handle_error
def render_chat():
    """Render the chat interface with multi-agent counseling system."""
    try:
        init_chat()

        # Display any existing error
        if st.session_state.error_message:
            st.error(st.session_state.error_message)
            if st.checkbox("Show Error Details"):
                st.code(st.session_state.error_details)
            if st.button("Clear Error"):
                st.session_state.error_message = None
                st.session_state.error_details = None
                st.rerun()

        st.subheader("Chat with your AI College Counseling Team")

        # Add quick action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🎯 Get College Suggestions"):
                st.session_state.messages.append({"role": "user", "content": "Based on my profile, what colleges would you recommend?"})
        with col2:
            if st.button("📈 Improve Application"):
                st.session_state.messages.append({"role": "user", "content": "How can I improve my college application?"})
        with col3:
            if st.button("❓ Common Questions"):
                st.session_state.messages.append({"role": "user", "content": "What are the key steps in the college application process?"})

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if isinstance(message.get("content"), dict) and "content" in message["content"]:
                    # Display main response
                    st.markdown(message["content"]["content"])

                    # Display actionable item if present
                    if message["content"].get("actionable_item"):
                        with st.container():
                            st.markdown("---")
                            st.markdown("**📌 Actionable Item Detected:**")
                            item = message["content"]["actionable_item"]
                            st.markdown(f"**Category:** {item['category']}")
                            st.markdown(f"**Relevant Years:** {item['year']}")
                            if item.get('url'):
                                st.markdown(f"**Resource:** [Click here]({item['url']})")
                            if st.button("➕ Add to Plan", key=f"add_plan_{len(st.session_state.messages)}"):
                                add_to_plan(item)
                else:
                    st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask your college admissions question..."):
            try:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get AI response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            logger.info(f"Processing message through agent orchestrator: {prompt[:100]}...")

                            # Run the async function in the event loop
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                response = loop.run_until_complete(
                                    st.session_state.agent_orchestrator.process_message(
                                        prompt,
                                        st.session_state.user.id if hasattr(st.session_state, 'user') else None
                                    )
                                )
                                logger.info("Successfully got response from agent orchestrator")

                                # Display and save response
                                if isinstance(response, dict):
                                    st.markdown(response["content"])
                                    if response.get("actionable_item"):
                                        with st.container():
                                            st.markdown("---")
                                            st.markdown("**📌 Actionable Item Detected:**")
                                            item = response["actionable_item"]
                                            st.markdown(f"**Category:** {item['category']}")
                                            st.markdown(f"**Relevant Years:** {item['year']}")
                                            if item.get('url'):
                                                st.markdown(f"**Resource:** [Click here]({item['url']})")
                                            if st.button("➕ Add to Plan"):
                                                add_to_plan(item)
                                else:
                                    st.markdown(response)

                                st.session_state.messages.append({"role": "assistant", "content": response})

                                # Save chat session if user is authenticated
                                if hasattr(st.session_state, 'user') and st.session_state.user:
                                    save_chat_session(prompt, response)
                                    logger.info("Chat message saved successfully")

                            except Exception as agent_error:
                                error_trace = traceback.format_exc()
                                logger.error(f"Agent processing error: {str(agent_error)}\n{error_trace}")
                                st.session_state.error_message = f"Failed to process message: {str(agent_error)}"
                                st.session_state.error_details = error_trace
                                st.rerun()
                            finally:
                                loop.close()

                        except Exception as processing_error:
                            error_trace = traceback.format_exc()
                            logger.error(f"Message processing error: {str(processing_error)}\n{error_trace}")
                            st.session_state.error_message = "Unable to process your message"
                            st.session_state.error_details = error_trace
                            st.rerun()

            except Exception as chat_error:
                error_trace = traceback.format_exc()
                logger.error(f"Chat interaction error: {str(chat_error)}\n{error_trace}")
                st.session_state.error_message = "Something went wrong in the chat"
                st.session_state.error_details = error_trace
                st.rerun()

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in render_chat: {str(e)}\n{error_trace}")
        st.session_state.error_message = "Something went wrong"
        st.session_state.error_details = error_trace
        st.rerun()

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

        # Handle response based on its type
        response_content = response["content"] if isinstance(response, dict) else response

        db.execute(
            "INSERT INTO messages (session_id, content, role) VALUES (%s, %s, %s), (%s, %s, %s)",
            (session_id, prompt, 'user', session_id, response_content, 'assistant')
        )
        logger.info(f"Saved messages to session {session_id}")

    except DatabaseError as e:
        error_trace = traceback.format_exc()
        logger.error(f"Failed to save chat session: {str(e)}\n{error_trace}")
        raise DatabaseError("Failed to save chat messages")

# Make sure the functions are properly exported
__all__ = ['render_chat', 'new_chat_session', 'load_chat_session']