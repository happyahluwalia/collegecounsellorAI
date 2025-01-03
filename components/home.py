import streamlit as st
from streamlit_lottie import st_lottie
from streamlit_extras.switch_page_button import switch_page
import os

def render_hero_section():
    """Render the hero section with Coco's avatar and main message"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Center the avatar
        image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "coco.webp")
        st.image(image_path, use_container_width=True)

        # Main headline
        st.markdown(
            """
            <h1 style='text-align: center;'>Unlock Your Future with AI-Powered College Guidance</h1>
            <h3 style='text-align: center;'>Your journey to college starts here!</h3>
            """,
            unsafe_allow_html=True
        )

        # Value proposition
        st.markdown(
            """
            <div style='text-align: center;'>
            ✨ Personalized advice tailored to your goals<br>
            🌟 24/7 availability for your convenience<br>
            📚 Access to tailored resources and tools
            </div>
            """,
            unsafe_allow_html=True
        )

        # Chat button
        if st.button(
            "Chat with Coco Now!",
            help="Get personalized college advice instantly",
            use_container_width=True,
        ):
            switch_page("chat")

def render_demo_mode_indicator():
    """Show demo mode banner"""
    if not hasattr(st.session_state, 'user') or st.session_state.user is None:
        st.warning(
            "🚀 Demo Mode: Experience Coco's capabilities! No login required.",
            icon="📝"
        )

def render_navigation():
    """Render the navigation menu"""
    menu_items = {
        "Home": "home",
        "Login": "login",
        "Blog": "blog",
        "Resources": "resources",
        "About": "about"
    }

    with st.sidebar:
        st.markdown("### Navigation")
        for label, page in menu_items.items():
            if st.button(label, use_container_width=True):
                switch_page(page)

def render_home():
    """Main function to render the homepage"""
    # Custom CSS for styling
    st.markdown(
        """
        <style>
        .stButton > button {
            background-color: #FF4B4B;
            color: white;
            font-size: 20px;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .stButton > button:hover {
            background-color: #FF6B6B;
            border-color: #FF4B4B;
        }
        h1 {
            color: #2E4057;
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        h3 {
            color: #4A4A4A;
            font-size: 24px;
            margin-bottom: 30px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Show demo mode indicator if needed
    render_demo_mode_indicator()

    # Render main sections
    render_hero_section()

    # Navigation in sidebar
    render_navigation()

if __name__ == "__main__":
    render_home()