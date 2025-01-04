import streamlit as st

def main():
    st.set_page_config(
        page_title="About College Compass - AI-Powered College Guidance",
        page_icon="ℹ️",
        initial_sidebar_state="collapsed"
    )
    
    st.title("About College Compass")
    st.markdown("""
    ## Our Mission
    College Compass aims to make college guidance accessible to all students through 
    AI-powered personalized support and expert counseling.
    
    ## Meet Coco
    Your AI college counselor, available 24/7 to help you navigate your 
    college application journey.
    
    ## Our Approach
    We combine cutting-edge AI technology with proven college counseling 
    methodologies to provide:
    - Personalized guidance tailored to your goals
    - Comprehensive application support
    - Real-time feedback and assistance
    - Data-driven college recommendations
    """)

if __name__ == "__main__":
    main()
