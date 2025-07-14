"""
Configuration and application setup for the Dark Souls Knowledge Graph Explorer.

This module handles Streamlit configuration, custom styling, and session state initialization.
"""

import streamlit as st


def initialize_app():
    """Initialize the Streamlit application with configuration and styling."""
    # load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # page configuration
    st.set_page_config(
        page_title="Dark Souls Knowledge Graph Explorer",
        page_icon="⚔️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # apply custom CSS styling
    apply_custom_styling()
    
    # initialize session state
    initialize_session_state()


def apply_custom_styling():
    """Apply custom CSS styling for better UI appearance."""
    st.markdown(
        """
        <style>
            .main-header {
                text-align: center;
                color: #2E4053;
                font-size: 2.5rem;
                margin-bottom: 2rem;
            }
            .query-box {
                background-color: #F8F9FA;
                padding: 1rem;
                border-radius: 0.5rem;
                border: 1px solid #DEE2E6;
            }
            .results-container {
                margin-top: 2rem;
            }
            .stats-box {
                background-color: #E8F4FD;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #3498DB;
            }
            .button-row {
                display: flex;
                gap: 8px;
                align-items: center;
                margin-bottom: 1rem;
            }
            .button-row .stButton {
                margin: 0 !important;
                flex: 0 0 auto;
            }
            .button-row .stButton > button {
                margin: 0 !important;
                white-space: nowrap !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


def initialize_session_state():
    """Initialize session state variables."""
    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    if "current_results" not in st.session_state:
        st.session_state.current_results = None
    if "query_text" not in st.session_state:
        st.session_state.query_text = "MATCH (n) RETURN n LIMIT 10"
