import streamlit as st
from components.home import render_home
from components.auth import init_auth, login_page, handle_oauth_callback
from components import render_dashboard
from utils.styles import apply_custom_styles
from utils.constants import APP_CONFIG

# Configure the app
st.set_page_config(
    page_title=APP_CONFIG['title'],
    page_icon=APP_CONFIG['icon'],
    layout="wide",  # Changed to wide layout for better hero section display
    initial_sidebar_state="collapsed"  # Start with collapsed sidebar for cleaner look
)

# Apply custom styles
apply_custom_styles()

# Initialize authentication
init_auth()

def main():
    # Handle OAuth callback if present
    if 'code' in st.query_params:
        handle_oauth_callback()

    # Show login page, homepage, or dashboard based on state and path
    if not hasattr(st.session_state, 'user'):
        render_home()  # Show homepage for non-logged in users
    elif st.session_state.user is None:
        if st.session_state.get('show_login', False):
            login_page()
        else:
            render_home()  # Show homepage for demo mode
    else:
        render_dashboard()  # Show dashboard for logged in users

if __name__ == "__main__":
    main()