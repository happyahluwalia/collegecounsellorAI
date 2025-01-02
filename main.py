import streamlit as st
from components.auth import init_auth, login_page, handle_oauth_callback
import components.dashboard as dashboard
from utils.styles import apply_custom_styles
from utils.constants import APP_CONFIG

# Configure the app
st.set_page_config(
    page_title=APP_CONFIG['title'],
    page_icon=APP_CONFIG['icon'],
    layout=APP_CONFIG['layout']
)

# Apply custom styles
apply_custom_styles()

# Initialize authentication
init_auth()

def main():
    # Handle OAuth callback if present
    if 'code' in st.query_params:
        handle_oauth_callback()

    # Show login page or dashboard based on authentication status
    if not st.session_state.user:
        login_page()
    else:
        dashboard.render_dashboard()

if __name__ == "__main__":
    main()