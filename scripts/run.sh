#!/bin/bash
# Local development script for Content Summarizer

cd "$(dirname "$0")/../src"
streamlit run content_summarizer/app.py
