import streamlit as st

def main():
    st.set_page_config(
        page_title="College Application Resources - College Compass",
        page_icon="📚",
        initial_sidebar_state="collapsed"
    )
    
    st.title("College Application Resources")
    st.markdown("""
    ## Coming Soon
    We're preparing comprehensive resources to help you with your college application journey.
    
    Stay tuned for:
    - Application guides
    - Essay writing tips
    - Test preparation materials
    - Scholarship information
    - And much more!
    """)

if __name__ == "__main__":
    main()
