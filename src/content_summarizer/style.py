"""Streamlit UI styling for Content Summarizer."""

import streamlit as st


def apply_dark_mode():
    """Apply dark mode CSS styling if enabled in session state."""
    if st.session_state.get('dark_mode', False):
        st.markdown("""
        <style>
            /* Dark mode styles */
            .stApp {
                background-color: #0e1117 !important;
                color: #fafafa !important;
            }
            
            header, header * {
                color: inherit !important;
            }
            [data-testid="stHeader"] {
                background-color: transparent !important;
            }
            [data-testid="stHeader"] * {
                color: inherit !important;
            }
            
            /* Main content area text - force white */
            main p, main span, main div, main h1, main h2, main h3, main h4, main h5, main h6, main label, main li {
                color: #fafafa !important;
            }
            
            /* Caption text under header */
            main .element-container p, main [data-testid="stMarkdownContainer"] p {
                color: #fafafa !important;
            }
            
            /* Ensure caption/info text is white */
            .stCaption, [data-testid="stCaption"] {
                color: #fafafa !important;
            }
            
            /* Slider label */
            .stSlider label, [data-testid="stSlider"] label, .stSlider > label {
                color: #fafafa !important;
            }
            
            /* Input fields */
            .stTextInput > div > div > input, .stTextArea textarea, .stNumberInput > div > div > input {
                background-color: #262730 !important;
                color: #ffffff !important;
                border-color: #4a4a4a !important;
            }
            
            input::placeholder, textarea::placeholder {
                color: #999999 !important;
                opacity: 1 !important;
            }
            
            /* Markdown content */
            .stMarkdown, .stMarkdown p, .stMarkdown span {
                color: #fafafa !important;
            }
            
            /* Alert boxes */
            .stAlert {
                background-color: #1e1e1e !important;
                border-color: #4a4a4a !important;
                color: #fafafa !important;
            }
            
            /* Button text */
            .stButton > button {
                color: #ffffff !important;
            }
            
            /* Tab labels */
            .stTabs [data-baseweb="tab-list"] button {
                color: #fafafa !important;
            }
            
            /* Expander text */
            .streamlit-expanderHeader {
                color: #fafafa !important;
            }
            
            /* Success/Error/Warning/Info messages text */
            .stSuccess, .stError, .stWarning, .stInfo {
                color: #fafafa !important;
            }
            
            /* Download button */
            .stDownloadButton > button {
                color: #ffffff !important;
            }
        </style>
        """, unsafe_allow_html=True)
