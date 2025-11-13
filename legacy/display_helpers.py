# Helper functions for displaying results - temporary file for reference
# This will be integrated into summarizer_ui.py

def display_file_results():
    """Display file upload results with download and process another buttons"""
    if 'file_result' in st.session_state and st.session_state.file_result:
        output = st.session_state.file_result['output']
        filename = st.session_state.file_result['filename']
        
        # Create markdown from output
        md_content = create_markdown_from_results(output, filename)
        
        # Blue download button
        st.download_button(
            "📥 Download Markdown",
            md_content,
            file_name=f"{filename.rsplit('.', 1)[0]}_summary.md",
            mime="text/markdown",
            use_container_width=True,
            type="primary",
            key="download_file_btn"
        )
        
        # Green Process Another button
        st.markdown("""
        <style>
        .stButton > button[kind="secondary"] {
            background-color: #28a745 !important;
            color: white !important;
            border: 1px solid #28a745 !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background-color: #218838 !important;
            border-color: #1e7e34 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        if st.button("📝 Process Another", type="secondary", use_container_width=True, key="process_another_file"):
            # Clear session state and increment file cleared counter
            st.session_state.file_result = None
            st.session_state.file_cleared = st.session_state.get('file_cleared', 0) + 1
            st.rerun()
        
        # Display results
        display_results(output, show_logs=True)


def display_text_results():
    """Display text paste results with download and process another buttons"""
    if 'text_result' in st.session_state and st.session_state.text_result:
        output = st.session_state.text_result['output']
        filename = st.session_state.text_result['filename']
        
        # Create markdown from output
        md_content = create_markdown_from_results(output, filename)
        
        # Blue download button
        st.download_button(
            "📥 Download Markdown",
            md_content,
            file_name=filename,
            mime="text/markdown",
            use_container_width=True,
            type="primary",
            key="download_text_btn"
        )
        
        # Green Process Another button
        st.markdown("""
        <style>
        .stButton > button[kind="secondary"] {
            background-color: #28a745 !important;
            color: white !important;
            border: 1px solid #28a745 !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background-color: #218838 !important;
            border-color: #1e7e34 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        if st.button("📝 Process Another", type="secondary", use_container_width=True, key="process_another_text"):
            # Clear session state and set text cleared flag
            st.session_state.text_result = None
            st.session_state.text_cleared = st.session_state.get('text_cleared', 0) + 1
            st.rerun()
        
        # Display results
        display_results(output, show_logs=False)
