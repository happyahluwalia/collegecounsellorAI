import streamlit as st
from agents.counselor import CounselorAgent
from agents.validator import ValidatorAgent

def init_chat():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'counselor' not in st.session_state:
        st.session_state.counselor = CounselorAgent()
    if 'validator' not in st.session_state:
        st.session_state.validator = ValidatorAgent()

def render_chat():
    init_chat()
    st.subheader("Chat with your AI Counselor")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask your college admissions question..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            response = st.session_state.counselor.get_response(prompt)
            
            # Validate response
            validated_response = st.session_state.validator.validate_response(response)
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def new_chat_session():
    st.session_state.messages = []
