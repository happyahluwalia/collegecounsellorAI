import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from models.user import User

def init_auth():
    if 'user' not in st.session_state:
        st.session_state.user = None

def login_page():
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-container">
        <h1>Welcome to College Compass</h1>
        <p>Your AI-powered college admissions guide</p>
    </div>
    """, unsafe_allow_html=True)

    # Add temporary direct access button
    if st.button("🎓 Enter as Demo User"):
        # Create a mock user session
        mock_user = User(
            email="demo@example.com",
            name="Demo User"
        ).create()
        st.session_state.user = mock_user
        st.experimental_rerun()

    # Keep the Google OAuth button for later implementation
    st.button("Sign in with Google", disabled=True)

def handle_oauth_callback():
    query_params = st.query_params
    if 'code' in query_params:
        code = query_params['code']
        flow = Flow.from_client_secrets_file(
            'client_secrets.json',
            scopes=['https://www.googleapis.com/auth/userinfo.email'],
            state=st.session_state.oauth_state
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user info from Google
        user_info = get_user_info(credentials)

        # Create or get user
        user = User.get_by_email(user_info['email'])
        if not user:
            user = User(email=user_info['email'], 
                       name=user_info['name']).create()

        st.session_state.user = user
        st.experimental_rerun()

def get_user_info(credentials):
    # Mock implementation for now
    return {
        'email': 'example@gmail.com',
        'name': 'Example User'
    }