import streamlit as st
from streamlit_lottie import st_lottie
from streamlit_extras.switch_page_button import switch_page
import os

def render_hero_section():
    """Render the hero section with Coco's avatar and main message"""
    # Set up grid layout
    st.markdown(
        """
        <div class="hero-section">
            <div class="hero-content">
                <h1>Your Personal AI College Counselor</h1>
                <h2>Navigate Your College Journey with Confidence</h2>
                <p class="hero-description">
                    Get personalized guidance, essay feedback, and application support 
                    from Coco, your AI college counselor available 24/7.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Center the avatar and CTA
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "coco.webp")
        st.image(image_path, use_container_width=True)

        # Call to action button
        if st.button(
            "Start Your Journey with Coco",
            key="hero-cta",
            help="Begin your personalized college guidance experience",
            use_container_width=True
        ):
            switch_page("chat")

def render_key_features():
    """Render the key features section"""
    st.markdown("## How Coco Helps You Succeed", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            ### 🎯 Personalized Planning
            Get a customized roadmap based on your unique goals, interests, and academic profile.
            """
        )

    with col2:
        st.markdown(
            """
            ### 🔍 College Matching
            Find your perfect college match with AI-powered recommendations and insights.
            """
        )

    with col3:
        st.markdown(
            """
            ### 📝 Application Support
            Receive guidance on essays, deadlines, and application requirements.
            """
        )

def render_navigation():
    """Render the navigation menu"""
    menu_items = {
        "Home": "home",
        "Login": "login",
        "Resources": "resources",
        "Blog": "blog",
        "About": "about"
    }

    # Create a horizontal navigation bar
    st.markdown(
        """
        <nav class="navigation-bar">
            <div class="nav-content">
                <div class="nav-logo">College Compass</div>
                <div class="nav-links">
        """,
        unsafe_allow_html=True
    )

    # Add navigation links
    cols = st.columns(len(menu_items))
    for i, (label, page) in enumerate(menu_items.items()):
        with cols[i]:
            if st.button(label, key=f"nav-{page}", use_container_width=True):
                switch_page(page)

def render_demo_mode_indicator():
    """Show demo mode banner"""
    if not hasattr(st.session_state, 'user') or st.session_state.user is None:
        st.warning(
            "🚀 Demo Mode: Experience Coco's capabilities! No login required.",
            icon="📝"
        )

def render_home():
    """Main function to render the homepage"""
    # Custom CSS for styling
    st.markdown(
        """
        <style>
        /* Global Styles */
        [data-testid="stAppViewContainer"] {
            background-color: #FFFFFF;
        }

        /* Navigation Styles */
        .navigation-bar {
            background-color: #FFFFFF;
            padding: 1rem 0;
            border-bottom: 1px solid #EAEAEA;
            margin-bottom: 2rem;
        }

        .nav-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto;
        }

        .nav-logo {
            font-size: 24px;
            font-weight: bold;
            color: #2E4057;
        }

        /* Hero Section Styles */
        .hero-section {
            text-align: center;
            padding: 2rem 0;
            max-width: 800px;
            margin: 0 auto;
        }

        .hero-content h1 {
            font-size: 48px;
            font-weight: bold;
            color: #2E4057;
            margin-bottom: 1rem;
            line-height: 1.2;
        }

        .hero-content h2 {
            font-size: 24px;
            color: #4A4A4A;
            margin-bottom: 2rem;
        }

        .hero-description {
            font-size: 18px;
            color: #666666;
            margin-bottom: 2rem;
            line-height: 1.6;
        }

        /* Button Styles */
        .stButton > button {
            background-color: #FF4B4B;
            color: white;
            font-size: 18px;
            padding: 1rem 2rem;
            border-radius: 8px;
            border: none;
            transition: background-color 0.3s ease;
        }

        .stButton > button:hover {
            background-color: #FF6B6B;
            border-color: #FF4B4B;
        }

        /* Features Section Styles */
        h2 {
            color: #2E4057;
            font-size: 36px;
            text-align: center;
            margin: 3rem 0;
        }

        h3 {
            color: #2E4057;
            font-size: 24px;
            margin-bottom: 1rem;
        }

        /* Warning Banner Styles */
        .stAlert {
            background-color: #FFF3CD;
            color: #856404;
            border-color: #FFEEBA;
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Show demo mode indicator if needed
    render_demo_mode_indicator()

    # Render navigation
    render_navigation()

    # Render main sections
    render_hero_section()
    render_key_features()

if __name__ == "__main__":
    render_home()