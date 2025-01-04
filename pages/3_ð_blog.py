import streamlit as st

def main():
    st.set_page_config(
        page_title="College Compass Blog - Latest College Admissions Tips",
        page_icon="📝",
        initial_sidebar_state="collapsed"
    )
    
    st.title("College Compass Blog")
    st.markdown("""
    ## Coming Soon
    Our blog will feature insights and advice about:
    - College application strategies
    - Student success stories
    - Latest trends in college admissions
    - Expert advice from counselors
    - Tips for standardized tests
    """)

if __name__ == "__main__":
    main()
