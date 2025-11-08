#!/usr/bin/env python3
import os
import re
import subprocess
import streamlit as st


st.set_page_config(page_title="Content Summarizer", page_icon="📚", layout="wide")
st.title("📚 Content Summarizer")
st.caption("Summarize YouTube videos, podcasts, and web articles with AI")

DEFAULT_WORDS = 500
SCRIPT_PATH = "/Users/e.chan/content-summarizer/src/youtube_slash_command.py"

# Add info box
st.info("✨ **Supports YouTube videos, podcasts, and article URLs** • AI-powered summaries with key takeaways")

url = st.text_input(
    "YouTube, Podcast, or Article URL", 
    placeholder="https://www.youtube.com/... or https://podcasts.apple.com/... or https://example.com/article",
    help="Paste a YouTube video, podcast (Apple/Spotify/RSS), or web article URL"
)
words = st.number_input("Summary length (words)", min_value=50, max_value=3000, value=DEFAULT_WORDS, step=50)

run = st.button("✨ Summarize", type="primary")

if run and url:
    with st.spinner("Processing… this may take a minute for long content"):
        cmd = [
            "python3", SCRIPT_PATH, url,
            "--format", "md",
            "--words", str(words),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        out = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")

    # Show AI provider/model confirmation if present
    mm = re.search(r"Using\s+(\w+)\s+AI\s*\(model:\s*([^)]+)\)", out)
    if mm:
        provider, model = mm.group(1), mm.group(2)
        st.success(f"AI Provider: {provider} • Model: {model}")
    
    # Check for quality warnings in output
    warnings = []
    if "Music video detected" in out:
        warnings.append("⚠️ Music video - transcript is mostly lyrics")
    if "Very short content" in out:
        warnings.append("⚠️ Content is very short")
    if "Highly conversational" in out:
        warnings.append("💬 Conversational content")
    
    if warnings:
        st.warning("**Content Quality Notes:**\n\n" + "\n".join(f"- {w}" for w in warnings))

    st.subheader("Logs")
    st.text_area("Command output", out, height=220)

    m = re.search(r"Markdown document saved:\s*(.+)", out)
    if res.returncode == 0 and m:
        path = m.group(1).strip()
        st.success(f"Saved: {path}")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                st.download_button("Download Markdown", content, file_name=os.path.basename(path))
                st.divider()
                st.subheader("Report Preview")
                st.markdown(content)
            except Exception as e:
                st.warning(f"Could not read saved file: {e}")
        else:
            st.warning("Saved file path not found on disk. Check permissions/path in logs above.")
    else:
        st.error("Failed to generate summary. Check logs above for details.")
