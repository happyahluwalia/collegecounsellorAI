"""Chat component for the College Compass application."""
import streamlit as st
from agents.orchestrator import AgentOrchestrator
from utils.error_handling import handle_error, DatabaseError, ValidationError, AgentError
import logging
import traceback
import asyncio
import json
import re
import time
import random

logger = logging.getLogger(__name__)

def generate_unique_key(prefix, item_id):
    """Generate a unique key for streamlit elements"""
    timestamp = int(time.time() * 1000)  # Get current time in milliseconds
    random_num = random.randint(1000, 9999)  # Generate a random 4-digit number
    unique_key = f"{prefix}_{timestamp}_{random_num}_{item_id}"
    logger.debug(f"Generated unique key: {unique_key}")
    return unique_key

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
def add_to_plan(actionable_item: dict) -> tuple[bool, str]:
    """Add an actionable item to the student's plan"""
    try:
        logger.info("=== Starting add_to_plan function ===")
        logger.info(f"Received actionable item: {json.dumps(actionable_item, indent=2)}")

        # Check if user is logged in and has session state
        if not hasattr(st.session_state, 'user'):
            logger.warning("No user in session state")
            return False, "Please log in to add items to your plan"

        if not st.session_state.user:
            logger.warning("User object is None in session state")
            return False, "Please log in to add items to your plan"

        logger.info(f"User authenticated: {st.session_state.user.id}")

        # Verify database connection
        db = st.session_state.user.db
        if not db:
            logger.error("Database connection not available")
            return False, "Database connection error"

        user_id = st.session_state.user.id
        logger.debug(f"User ID: {user_id}, Database connection: {db}")

        # Verify user exists in database
        user_check = db.execute_one("SELECT id FROM users WHERE id = %s", (user_id,))
        if not user_check:
            logger.error(f"User {user_id} not found in database")
            return False, "User not found in database"
        logger.info(f"Verified user {user_id} exists in database")

        # Validate required fields
        required_fields = ['text', 'category', 'year']
        for field in required_fields:
            if field not in actionable_item:
                logger.error(f"Missing required field: {field}")
                return False, f"Missing required field: {field}"

        try:
            # Prepare parameters
            params = (
                user_id,
                actionable_item["text"],
                actionable_item["category"],
                actionable_item["year"],
                actionable_item.get("url"),
                json.dumps({"source": "chat_recommendation"})
            )
            logger.info(f"SQL Parameters: {params}")

            # Insert with detailed error catching
            try:
                result = db.execute_one(
                    """
                    INSERT INTO plan_items 
                    (user_id, activity_text, category, grade_year, url, status, metadata)
                    VALUES (%s, %s, %s, %s, %s, 'pending', %s)
                    RETURNING id, activity_text;
                    """,
                    params
                )

                if not result:
                    logger.error("Insert returned no result")
                    return False, "Failed to add item to plan: No result returned"

                logger.info(f"Insert successful, returned ID: {result.get('id')}")

                # Verify the insert worked
                verification = db.execute_one(
                    "SELECT id FROM plan_items WHERE id = %s",
                    (result['id'],)
                )

                if verification:
                    logger.info("Insert verified successfully")
                    return True, "Added to plan successfully!"
                else:
                    logger.error("Could not verify inserted record")
                    return False, "Failed to verify item was added"

            except Exception as insert_error:
                error_msg = str(insert_error)
                logger.error(f"Insert failed: {error_msg}\n{traceback.format_exc()}")

                if "violates foreign key constraint" in error_msg:
                    logger.error(f"Foreign key constraint violation for user_id: {user_id}")
                    return False, "Database foreign key error - please try logging in again"

                return False, f"Database error: {error_msg}"

        except Exception as db_error:
            logger.error(f"Database operation failed: {str(db_error)}\n{traceback.format_exc()}")
            return False, f"Database error: {str(db_error)}"

    except Exception as e:
        logger.error(f"Error in add_to_plan: {str(e)}\n{traceback.format_exc()}")
        return False, str(e)

def parse_and_render_message(content: str, actionable_items: list):
    """Parse message content and render with inline Add to Plan buttons"""
    try:
        # Create a mapping of item_id to item details
        actionable_map = {str(item['id']): item for item in actionable_items}
        logger.info(f"Processing message with {len(actionable_items)} actionable items")
        logger.debug(f"Actionable items map: {json.dumps(actionable_map, indent=2)}")

        if not isinstance(content, str):
            logger.error(f"Content is not a string: {type(content)}")
            st.error("Invalid content format")
            return

        # Find all actionable items in the content
        actionable_pattern = r'<actionable id="(\d+)">(.*?)</actionable>'
        matches = list(re.finditer(actionable_pattern, content))
        logger.info(f"Found {len(matches)} actionable items in content")

        last_end = 0
        for match in matches:
            # Render text before the actionable item
            if match.start() > last_end:
                pre_text = content[last_end:match.start()]
                if pre_text.strip():
                    st.markdown(pre_text)

            # Process the actionable item
            item_id = match.group(1)
            text = match.group(2)

            if item_id in actionable_map:
                item = actionable_map[item_id]
                logger.debug(f"Rendering actionable item {item_id}")

                cols = st.columns([0.92, 0.08])
                with cols[0]:
                    st.markdown(text)

                with cols[1]:
                    # Generate a unique key using timestamp and item_id
                    timestamp = int(time.time() * 1000)
                    unique_key = f"btn_{timestamp}_{item_id}"

                    if st.button("➕", key=unique_key, help="Add this item to your plan"):
                        logger.info(f"Add button clicked for item {item_id}")
                        success, message = add_to_plan(item)
                        if success:
                            st.toast("✅ Added to plan!", icon="✅")
                            logger.info(f"Successfully added item {item_id}")
                        else:
                            st.warning(message)
                            logger.error(f"Failed to add item {item_id}: {message}")
            else:
                logger.warning(f"Item {item_id} not found in actionable_map")
                st.markdown(text)

            last_end = match.end()

        # Render any remaining text
        if last_end < len(content):
            remaining = content[last_end:]
            if remaining.strip():
                st.markdown(remaining)

    except Exception as e:
        logger.error(f"Error in parse_and_render_message: {str(e)}\n{traceback.format_exc()}")
        st.error("Error displaying message")

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