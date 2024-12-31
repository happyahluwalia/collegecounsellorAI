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

    # Add Google OAuth button here
    if st.button("Sign in with Google"):
        flow = Flow.from_client_secrets_file(
            'client_secrets.json',
            scopes=['https://www.googleapis.com/auth/userinfo.email', 
                   'https://www.googleapis.com/auth/userinfo.profile'],
            redirect_uri='http://localhost:5000/oauth2callback'
        )
        authorization_url, state = flow.authorization_url()
        st.session_state.oauth_state = state
        st.markdown(f'<a href="{authorization_url}">Click here to complete sign in</a>', 
                   unsafe_allow_html=True)

def handle_oauth_callback():
    if 'code' in st.experimental_get_query_params():
        code = st.experimental_get_query_params()['code'][0]
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
    # Implement Google user info API call
    return {
        'email': 'example@gmail.com',
        'name': 'Example User'
    }
