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

def handle_plan_item_add(item_id: str, item: dict) -> None:
    """Handle adding item to plan with proper state management"""
    state_key = f"plan_item_{item_id}_added"

    # Only process if not already added
    if state_key not in st.session_state:
        st.session_state[state_key] = False

    if not st.session_state[state_key]:
        logger.info(f"Processing plan item add for item {item_id}")
        try:
            if not hasattr(st.session_state, 'user') or not st.session_state.user:
                logger.error("No user in session state")
                st.error("Please log in to add items to your plan")
                return

            user_id = st.session_state.user.id
            db = st.session_state.user.db

            # Insert the plan item
            result = db.execute_one(
                """
                INSERT INTO plan_items 
                (user_id, activity_text, category, grade_year, status)
                VALUES 
                (%s, %s, %s, %s, 'pending')
                RETURNING id;
                """,
                (
                    user_id,
                    item["text"],
                    item["category"],
                    item["year"]
                )
            )

            if result and 'id' in result:
                logger.info(f"Successfully added plan item with ID: {result['id']}")
                st.session_state[state_key] = True
                st.toast("✅ Added to plan!")
            else:
                logger.error("Failed to add item - no ID returned")
                st.error("Failed to add item to plan")

        except Exception as e:
            logger.error(f"Error adding plan item: {str(e)}")
            st.error(f"Error: {str(e)}")

def parse_and_render_message(content: str, actionable_items: list):
    """Parse message content and render with inline Add to Plan buttons"""
    try:
        # Create a mapping of item_id to item details
        actionable_map = {str(item['id']): item for item in actionable_items}
        logger.info(f"Starting to parse message with {len(actionable_items)} actionable items")

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
                logger.info(f"Processing actionable item {item_id}: {item}")

                # Create container for the item
                item_container = st.container()
                with item_container:
                    cols = st.columns([0.9, 0.1])
                    with cols[0]:
                        st.markdown(text)

                    with cols[1]:
                        # Generate unique key using item's UUID if available, otherwise create a stable key
                        button_key = item.get('uuid', f"add_btn_{item_id}_{int(time.time())}")
                        state_key = f"plan_item_{item_id}_added"

                        # Initialize state if needed
                        if state_key not in st.session_state:
                            st.session_state[state_key] = False

                        # Show add button or nothing based on state
                        if not st.session_state[state_key]:
                            if st.button("➕", key=button_key, help="Add to your plan"):
                                handle_plan_item_add(item_id, item)
                                st.rerun()  # Rerun to update UI after adding item

            last_end = match.end()

        # Render any remaining text
        if last_end < len(content):
            remaining = content[last_end:]
            if remaining.strip():
                st.markdown(remaining)

    except Exception as e:
        logger.error(f"Error in parse_and_render_message: {str(e)}")
        st.error("Error displaying message")

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
        logger.info(f"Adding item to plan: {actionable_item}")

        if not hasattr(st.session_state, 'user') or not st.session_state.user:
            logger.error("No user in session state")
            return False, "Please log in to add items to your plan"

        user_id = st.session_state.user.id
        db = st.session_state.user.db

        logger.info(f"Adding plan item for user {user_id}")

        # Insert the plan item
        result = db.execute_one(
            """
            INSERT INTO plan_items 
            (user_id, activity_text, category, grade_year, status)
            VALUES 
            (%s, %s, %s, %s, 'pending')
            RETURNING id;
            """,
            (
                user_id,
                actionable_item["text"],
                actionable_item["category"],
                actionable_item["year"]
            )
        )

        if result and 'id' in result:
            logger.info(f"Successfully added plan item with ID: {result['id']}")
            return True, "Added to plan successfully!"

        logger.error("Failed to add item - no ID returned")
        return False, "Failed to add item"

    except Exception as e:
        logger.error(f"Error in add_to_plan: {str(e)}")
        return False, f"Error: {str(e)}"


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