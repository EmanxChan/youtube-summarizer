#!/bin/bash
# Restart Streamlit Content Summarizer

echo "🛑 Stopping existing Streamlit..."
pkill -f "streamlit run"
sleep 1

echo "🚀 Starting Streamlit..."
cd /Users/e.chan

# Set Listen Notes API credentials
export LISTEN_NOTES_API_KEY="4e8b3079caaf4cd28bb70df528bc652c"

nohup python3 -m streamlit run /Users/e.chan/summarizer_ui.py --server.headless true > /Users/e.chan/nohup.out 2>&1 &

sleep 2

echo "✅ Streamlit restarted!"
echo "📱 Visit: http://localhost:8501"
