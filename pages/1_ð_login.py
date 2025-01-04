import streamlit as st
from components.auth import login_page

def main():
    st.set_page_config(
        page_title="Login - College Compass",
        page_icon="🔑",
        initial_sidebar_state="collapsed"
    )
    
    login_page()

if __name__ == "__main__":
    main()
