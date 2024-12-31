import streamlit as st
from utils.constants import COLORS, GRADIENTS

def apply_custom_styles():
    st.markdown("""
        <style>
        /* Main container */
        .main {
            background-color: #FFFFFF;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #262730;
            font-family: 'Segoe UI', sans-serif;
        }
        
        /* Custom button styles */
        .stButton>button {
            background: linear-gradient(120deg, #f6d365 0%, #fda085 100%);
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Chat container */
        .chat-container {
            background: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        /* Progress bars */
        .stProgress > div > div {
            background: linear-gradient(120deg, #4ECDC4 0%, #556270 100%);
        }
        
        /* Custom card style */
        .css-1r6slb0 {
            background: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        /* Mobile responsive adjustments */
        @media (max-width: 768px) {
            .row-widget {
                flex-direction: column;
            }
            
            .stButton>button {
                width: 100%;
            }
        }
        </style>
    """, unsafe_allow_html=True)
