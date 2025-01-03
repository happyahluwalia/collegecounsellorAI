"""Chat component for the College Compass application."""
import streamlit as st
from agents.orchestrator import AgentOrchestrator
from utils.error_handling import handle_error, DatabaseError, ValidationError, AgentError
import logging
import traceback
import asyncio
import json
import re

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

@handle_error
def add_to_plan(actionable_item):
    """Add an actionable item to the student's plan"""
    try:
        if not hasattr(st.session_state, 'user'):
            st.warning("Please log in to add items to your plan")
            return False

        logger.info(f"Adding item to plan: {actionable_item}")

        db = st.session_state.user.db
        user_id = st.session_state.user.id

        # Add to plan table with enhanced schema
        try:
            # Log the values being inserted
            logger.info(f"Inserting plan item - User ID: {user_id}, "
                       f"Text: {actionable_item['text'][:50]}..., "
                       f"Category: {actionable_item['category']}, "
                       f"Year: {actionable_item['year']}")

            db.execute(
                """
                INSERT INTO plan_items 
                (user_id, activity_text, category, grade_year, url, status, metadata)
                VALUES (%s, %s, %s, %s, %s, 'pending', %s)
                RETURNING id
                """,
                (
                    user_id, 
                    actionable_item["text"], 
                    actionable_item["category"],
                    actionable_item["year"],
                    actionable_item.get("url"),
                    json.dumps({"source": "chat_recommendation"})
                )
            )

            logger.info("Successfully added item to plan")
            return True

        except Exception as db_error:
            logger.error(f"Database error adding item to plan: {str(db_error)}\n{traceback.format_exc()}")
            st.error("Failed to add item to your plan. Please try again.")
            return False

    except Exception as e:
        logger.error(f"Error in add_to_plan: {str(e)}\n{traceback.format_exc()}")
        st.error("Failed to add item to your plan. Please try again.")
        return False

def parse_and_render_message(content: str, actionable_items: list):
    """Parse message content and render with inline Add to Plan links"""
    try:
        # Create a mapping of item_id to item details
        actionable_map = {str(item['id']): item for item in actionable_items}
        logger.info(f"Actionable items map: {actionable_map}")

        # Split the content into paragraphs
        paragraphs = content.split('\n\n')

        for p_idx, paragraph in enumerate(paragraphs):
            # Check if this paragraph contains any actionable items
            actionable_pattern = r'<actionable id="(\d+)">(.*?)</actionable>'
            matches = list(re.finditer(actionable_pattern, paragraph))
            logger.debug(f"Found {len(matches)} actionable items in paragraph {p_idx}")

            if matches:
                # If paragraph contains actionable items, process them
                last_end = 0
                for match in matches:
                    # Print text before the actionable item
                    if match.start() > last_end:
                        st.markdown(paragraph[last_end:match.start()])

                    # Get the actionable item details
                    item_id = match.group(1)
                    text = match.group(2)

                    logger.debug(f"Processing actionable item {item_id}: {text[:50]}...")

                    if item_id in actionable_map:
                        # Generate a unique key for this specific item
                        unique_key = f"add_plan_{p_idx}_{item_id}"

                        # Create a container for the text and link
                        with st.container():
                            # Display the text and link in a clean format
                            if st.button("➕ Add to Plan", key=unique_key, type="secondary"):
                                if add_to_plan(actionable_map[item_id]):
                                    st.toast('✅ Added to plan', icon='✅')
                            st.markdown(text)

                    last_end = match.end()

                # Print any remaining text after the last actionable item
                if last_end < len(paragraph):
                    st.markdown(paragraph[last_end:])
            else:
                # If no actionable items in this paragraph, just print it
                st.markdown(paragraph)

    except Exception as e:
        logger.error(f"Error in parse_and_render_message: {str(e)}\n{traceback.format_exc()}")
        st.error("Error displaying message content")

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
                if isinstance(message.get("content"), dict):
                    # Parse and render content with inline actionable items
                    parse_and_render_message(
                        message["content"]["content"],
                        message["content"].get("actionable_items", [])
                    )
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
                                    parse_and_render_message(
                                        response["content"],
                                        response.get("actionable_items", [])
                                    )
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

# Helper functions for chat management
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
__all__ = ['render_chat', 'new_chat_session']