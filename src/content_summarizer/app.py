#!/usr/bin/env python3
import sys
import os
import re
import subprocess
import streamlit as st
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import json

# Add src directory to Python path for module imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from content_summarizer.style import apply_dark_mode
from content_summarizer.history_manager import get_history_manager, record_history


# ============================================================================
# Token Usage Tracking
# ============================================================================

GROQ_DAILY_TOKEN_LIMITS = {
    "llama-3.3-70b-versatile": 100_000,
    "llama-3.1-70b-versatile": 100_000,
    "llama-3.1-8b-instant": 500_000,
    "llama-3.2-3b-preview": 500_000,
}

def get_token_usage_path():
    """Get path to token usage tracking file."""
    usage_dir = Path.home() / '.youtube_summarizer'
    usage_dir.mkdir(parents=True, exist_ok=True)
    return usage_dir / 'token_usage.json'

def load_token_usage():
    """Load token usage from file."""
    path = get_token_usage_path()
    if path.exists():
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                # Reset if different day
                if data.get('date') != datetime.now().strftime('%Y-%m-%d'):
                    return {'date': datetime.now().strftime('%Y-%m-%d'), 'tokens_used': 0, 'requests': 0}
                return data
        except:
            pass
    return {'date': datetime.now().strftime('%Y-%m-%d'), 'tokens_used': 0, 'requests': 0}

def save_token_usage(tokens_used, requests=1):
    """Save token usage to file."""
    data = load_token_usage()
    data['tokens_used'] = data.get('tokens_used', 0) + tokens_used
    data['requests'] = data.get('requests', 0) + requests
    data['date'] = datetime.now().strftime('%Y-%m-%d')
    data['last_updated'] = datetime.now().isoformat()

    with open(get_token_usage_path(), 'w') as f:
        json.dump(data, f, indent=2)

def estimate_tokens(text):
    """Estimate tokens for text (rough estimate: ~4 chars per token)."""
    if not text:
        return 0
    return len(text) // 4

def estimate_processing_tokens(content_type, word_count):
    """Estimate tokens needed for a processing request."""
    # Base estimates for different content types
    base_estimates = {
        'url': 4000,      # Transcript fetch + processing
        'file': 5000,     # Transcription + processing
        'text': 2000,     # Direct text processing
    }

    # Adjust based on word count
    output_tokens = word_count * 2  # Summary output estimate
    input_estimate = base_estimates.get(content_type, 3000)

    return input_estimate + output_tokens


# ============================================================================
# Custom Prompt Templates
# ============================================================================

FOCUS_AREAS = {
    "General": "Provide a balanced overview covering all key points.",
    "Technical": "Focus on technical details, methodologies, tools, and implementation specifics.",
    "Business": "Emphasize business implications, ROI, market insights, and strategic value.",
    "Learning": "Highlight educational takeaways, concepts to remember, and actionable learning points.",
    "Quick Overview": "Provide a very concise summary hitting only the most essential points.",
}

TONE_OPTIONS = {
    "Professional": "Use clear, professional language suitable for business contexts.",
    "Casual": "Use conversational, approachable language that's easy to digest.",
    "Academic": "Use formal, detailed language with emphasis on accuracy and depth.",
    "Bullet Points": "Prioritize bullet points and lists over prose for easy scanning.",
}

# Load environment variables from .env file (project root)
load_dotenv(ROOT / ".env")

st.set_page_config(page_title="Content Summarizer", page_icon="📚", layout="wide")

# Constants
DEFAULT_WORDS = 500

# Load API keys from Streamlit secrets (cloud) or environment variables (local)
def get_secret(key_name):
    """Get a secret from Streamlit secrets or environment variables."""
    # Try Streamlit secrets first (for Streamlit Cloud deployment)
    try:
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    # Fallback to environment variable
    return os.environ.get(key_name, "")

# Load required and optional API keys
GROQ_API_KEY = get_secret('GROQ_API_KEY')

# Load optional API keys and set them as environment variables for subprocesses
for optional_key in ['LISTEN_NOTES_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'HF_TOKEN', 'HUGGINGFACE_TOKEN']:
    value = get_secret(optional_key)
    if value:
        os.environ[optional_key] = value

# Check if API key is set
if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY not configured. Set it via environment variable or Streamlit secrets.")
    st.info("💡 **For local development:** Create a `.env` file with `GROQ_API_KEY=your_key`\n\n💡 **For Streamlit Cloud:** Add the key in the app's Secrets settings")
    st.stop()

# Initialize dark mode in session state
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Dark mode toggle in top right
col1, col2 = st.columns([6, 1])
with col1:
    st.title("📚 Content Summarizer")
    st.caption("Summarize videos, podcasts, articles, and meetings with AI")
with col2:
    st.write("")  # Spacing
    if st.button("🌙" if not st.session_state.dark_mode else "☀️", 
                 help="Toggle dark/light mode",
                 key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# Apply dark mode theme
apply_dark_mode()

# Add info box
st.info("✨ **Supports YouTube videos, podcasts, articles, files, and text** • AI-powered summaries with key takeaways")

# === Tabbed Input Interface with Dedicated Content Types ===
tab_yt, tab_podcast, tab_article, tab_upload, tab_text, tab_history = st.tabs([
    "🎬 YouTube",
    "🎙️ Podcast",
    "📰 Article",
    "📎 Upload",
    "📝 Text",
    "📜 History"
])

input_type = None
content = None

# Use dynamic keys for inputs so they clear when "Process Another" is clicked
input_counter = st.session_state.get('input_cleared', 0)

with tab_yt:
    st.markdown("### YouTube Video")
    st.caption("Enter a YouTube URL or video ID to summarize")
    yt_input = st.text_input(
        "YouTube URL",
        placeholder="https://youtube.com/watch?v=... or https://youtu.be/...",
        label_visibility="collapsed",
        key=f"youtube_input_{input_counter}"
    )
    if yt_input:
        input_type = "url"
        content = yt_input
        # Show detected video info
        if "youtube.com" in yt_input or "youtu.be" in yt_input:
            st.success("✓ YouTube video detected")

with tab_podcast:
    st.markdown("### Podcast Episode")
    st.caption("Enter a podcast URL, direct audio link, or search by name")

    podcast_mode = st.radio(
        "Input method",
        ["🔗 Podcast URL", "🎵 Direct Audio URL", "🔍 Search by Name"],
        horizontal=True,
        label_visibility="collapsed",
        key=f"podcast_mode_{input_counter}"
    )

    if podcast_mode == "🔗 Podcast URL":
        podcast_url = st.text_input(
            "Podcast URL",
            placeholder="Apple Podcasts, Spotify, Neuecast.app, or RSS feed URL",
            label_visibility="collapsed",
            key=f"podcast_url_input_{input_counter}"
        )
        if podcast_url:
            input_type = "url"
            content = podcast_url
            # Detect platform
            if "apple.com" in podcast_url:
                st.success("✓ Apple Podcasts detected")
            elif "spotify.com" in podcast_url:
                st.success("✓ Spotify detected")
            elif "neuecast.app" in podcast_url:
                st.success("✓ Neuecast detected")
            elif any(x in podcast_url.lower() for x in ['.rss', '/rss', '/feed', 'feeds.']):
                st.success("✓ RSS feed detected")
            else:
                st.info("ℹ️ Will attempt to process as podcast URL")

    elif podcast_mode == "🎵 Direct Audio URL":
        audio_url = st.text_input(
            "Direct Audio URL",
            placeholder="https://example.com/episode.mp3",
            label_visibility="collapsed",
            key=f"audio_url_input_{input_counter}"
        )
        st.caption("💡 Tip: Many podcast apps let you 'Copy Episode Link' to get a direct MP3 URL")
        if audio_url:
            input_type = "url"
            content = audio_url
            if any(ext in audio_url.lower() for ext in ['.mp3', '.m4a', '.wav', '.ogg']):
                st.success("✓ Direct audio file detected")
            else:
                st.info("ℹ️ Will attempt to download and transcribe")

    else:  # Search by Name
        search_query = st.text_input(
            "Search Query",
            placeholder="Podcast Name - topic (e.g., 'All-In - latest' or 'Huberman Lab - sleep')",
            label_visibility="collapsed",
            key=f"podcast_search_input_{input_counter}"
        )
        st.caption("💡 Format: 'Podcast Name - topic' or 'Podcast Name - latest'")
        if search_query:
            input_type = "url"
            content = search_query
            st.info(f"🔍 Will search for: {search_query}")

with tab_article:
    st.markdown("### Article or Webpage")
    st.caption("Enter any article, blog post, or webpage URL")
    article_url = st.text_input(
        "Article URL",
        placeholder="https://example.com/article",
        label_visibility="collapsed",
        key=f"article_input_{input_counter}"
    )
    if article_url:
        input_type = "url"
        content = article_url
        st.success("✓ Article URL detected")

with tab_upload:
    st.markdown("### Upload Audio, Video, or PDF")
    st.caption("📁 Supported: MP4, MP3, M4A, WAV, MOV, AVI, PDF (Zoom recordings, audio files, documents)")

    # Clear file uploader when Process Another is clicked
    file_uploader_key = "file_upload" if 'file_cleared' not in st.session_state else f"file_upload_{st.session_state.file_cleared}"

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['mp4', 'mp3', 'm4a', 'wav', 'mov', 'avi', 'pdf'],
        help="Upload Zoom recording, audio file, video, or PDF document",
        label_visibility="collapsed",
        key=file_uploader_key
    )
    if uploaded_file:
        input_type = "file"
        content = uploaded_file
        # Show file info
        col1, col2, col3 = st.columns(3)
        col1.metric("📎 File", uploaded_file.name.split('.')[-1].upper())
        col2.metric("💾 Size", f"{uploaded_file.size / 1024 / 1024:.1f} MB")
        col3.metric("📊 Status", "✅ Ready")

with tab_text:
    st.markdown("### Paste Text Content")
    st.caption("📝 Paste transcripts from Zoom, meeting notes, articles, or any text")

    # Clear text area when Process Another is clicked
    text_value = "" if 'text_cleared' in st.session_state and st.session_state.text_cleared else None
    text_key = "text_input" if 'text_cleared' not in st.session_state else f"text_input_{st.session_state.text_cleared}"

    text_area = st.text_area(
        "Paste content",
        value=text_value if text_value is not None else "",
        height=300,
        placeholder="Paste your Zoom transcript, meeting notes, article text, or any content here...\n\nExample:\n- Zoom meeting transcript\n- Podcast transcript\n- Article text\n- Research notes\n- Any text you want summarized",
        label_visibility="collapsed",
        key=text_key
    )
    if text_area and len(text_area.strip()) > 50:
        input_type = "text"
        content = text_area.strip()
        word_count = len(content.split())
        st.info(f"📝 {word_count:,} words pasted • Ready to summarize")
    elif text_area:
        st.warning("⚠️ Text seems too short (need at least 50 characters)")

with tab_history:
    st.markdown("### Summarization History")
    st.caption("View and re-process your past summaries")

    # Search and filter row
    hist_col1, hist_col2 = st.columns([3, 1])
    with hist_col1:
        history_search = st.text_input(
            "Search history",
            placeholder="Search by title or URL...",
            label_visibility="collapsed",
            key="history_search"
        )
    with hist_col2:
        history_filter = st.selectbox(
            "Filter",
            ["All", "Video", "Podcast", "Article"],
            label_visibility="collapsed",
            key="history_filter"
        )

    # Get history entries
    history_manager = get_history_manager()
    filter_type = None if history_filter == "All" else history_filter.lower()
    history_entries = history_manager.get_entries(
        limit=50,
        content_type=filter_type,
        search_query=history_search if history_search else None
    )

    # Handle delete action
    if 'delete_entry_id' in st.session_state and st.session_state.delete_entry_id:
        entry_to_delete = st.session_state.delete_entry_id
        st.session_state.delete_entry_id = None
        if history_manager.delete_entry(entry_to_delete):
            st.success("✓ Entry deleted from history")
            st.rerun()

    if history_entries:
        # Stats header
        stats = history_manager.get_stats()
        st.caption(f"📊 Showing {len(history_entries)} of {stats['total_entries']} total summaries")

        st.markdown("---")

        for entry in history_entries:
            formatted = history_manager.format_entry_for_display(entry)
            entry_id = entry.get('id', '')
            entry_url = entry.get('url', '')
            entry_title = formatted.get('title', 'Untitled')

            # History entry card
            with st.container():
                col_icon, col_info, col_actions = st.columns([1, 5, 3])

                with col_icon:
                    st.markdown(f"## {formatted['icon']}")

                with col_info:
                    title = entry_title
                    if len(title) > 50:
                        title = title[:50] + "..."
                    st.markdown(f"**{title}**")

                    # Show URL domain and time
                    domain = formatted.get('domain', '')
                    time_ago = formatted.get('time_ago', '')
                    st.caption(f"{domain} • {time_ago}")

                    # Show summary preview if available
                    preview = entry.get('summary_preview', '')
                    if preview:
                        st.caption(f"_{preview[:80]}..._" if len(preview) > 80 else f"_{preview}_")

                with col_actions:
                    # Quick action buttons in a row
                    btn_col1, btn_col2, btn_col3 = st.columns(3)

                    with btn_col1:
                        # Copy URL button
                        if entry_url and not entry_url.startswith(('text://', 'file://')):
                            # Use a text input trick for copy functionality
                            if st.button("📋", key=f"copy_{entry_id}", help="Copy URL"):
                                st.session_state[f"copied_url_{entry_id}"] = entry_url
                                st.toast(f"URL copied!", icon="✅")

                    with btn_col2:
                        # Export to notetaker
                        if st.button("📤", key=f"export_{entry_id}", help="Export for Notetaker"):
                            # Generate Notion/Obsidian formatted export
                            export_text = f"""# {entry_title}

**Source:** {entry_url}
**Type:** {entry.get('content_type', 'Unknown').title()}
**Date:** {entry.get('created_at', '')[:10]}

---

## Summary Preview
{entry.get('summary_preview', 'No preview available')}

---

> Exported from Content Summarizer
"""
                            st.session_state[f"export_{entry_id}"] = export_text

                    with btn_col3:
                        # Delete button
                        if st.button("🗑️", key=f"delete_{entry_id}", help="Delete from history"):
                            st.session_state.delete_entry_id = entry_id
                            st.rerun()

                    # Re-process button (full width below)
                    if entry_url and not entry_url.startswith(('text://', 'file://')):
                        if st.button("🔄 Re-process", key=f"reprocess_{entry_id}", use_container_width=True):
                            st.session_state.trigger_reprocess = entry_url
                            st.rerun()

                # Show copied URL if just copied
                if st.session_state.get(f"copied_url_{entry_id}"):
                    st.code(st.session_state[f"copied_url_{entry_id}"], language=None)
                    st.caption("👆 Select and copy the URL above")
                    if st.button("Hide", key=f"hide_copy_{entry_id}"):
                        del st.session_state[f"copied_url_{entry_id}"]
                        st.rerun()

                # Show export content if requested
                if st.session_state.get(f"export_{entry_id}"):
                    st.text_area(
                        "📋 Copy this to your notetaker:",
                        value=st.session_state[f"export_{entry_id}"],
                        height=200,
                        key=f"export_text_{entry_id}"
                    )
                    if st.button("Hide Export", key=f"hide_export_{entry_id}"):
                        del st.session_state[f"export_{entry_id}"]
                        st.rerun()

                st.markdown("---")
    else:
        st.info("📭 No history yet. Your summarized content will appear here.")
        st.caption("Process a YouTube video, podcast, or article to get started.")

# Handle re-process trigger (must be outside tabs to work)
if 'trigger_reprocess' in st.session_state and st.session_state.trigger_reprocess:
    reprocess_url = st.session_state.trigger_reprocess
    st.session_state.trigger_reprocess = None
    # Set flag to auto-process after displaying controls
    st.session_state.auto_process_url = reprocess_url

# Shared controls (only show when not in history tab or when auto-processing)
st.markdown("---")
words = st.slider("📊 Summary length (words)", 50, 3000, DEFAULT_WORDS, step=50)

# === Token Usage Status Bar ===
usage = load_token_usage()
tokens_used = usage.get('tokens_used', 0)
requests_today = usage.get('requests', 0)
daily_limit = GROQ_DAILY_TOKEN_LIMITS.get("llama-3.3-70b-versatile", 100_000)
tokens_remaining = max(0, daily_limit - tokens_used)
usage_percent = min((tokens_used / daily_limit) * 100, 100)

# Status indicator based on usage
if usage_percent < 50:
    status_color = "🟢"
elif usage_percent < 80:
    status_color = "🟡"
else:
    status_color = "🔴"

# Compact status bar with progress
token_cols = st.columns([1, 3, 1])
with token_cols[0]:
    st.caption(f"{status_color} **{usage_percent:.0f}%** used")
with token_cols[1]:
    st.progress(usage_percent / 100)
with token_cols[2]:
    st.caption(f"**{tokens_remaining:,}** left")

# Show warning if approaching limit
if usage_percent >= 80:
    st.warning("⚠️ Approaching daily limit. May fallback to smaller models.", icon="⚠️")

# === Advanced Options Expander ===
with st.expander("⚙️ Advanced Options", expanded=False):
    adv_col1, adv_col2 = st.columns(2)

    with adv_col1:
        focus_area = st.selectbox(
            "🎯 Focus Area",
            options=list(FOCUS_AREAS.keys()),
            index=0,
            help="Adjust what aspects the summary emphasizes"
        )
        st.caption(f"_{FOCUS_AREAS[focus_area]}_")

    with adv_col2:
        tone = st.selectbox(
            "✍️ Tone",
            options=list(TONE_OPTIONS.keys()),
            index=0,
            help="Adjust the writing style of the summary"
        )
        st.caption(f"_{TONE_OPTIONS[tone]}_")

    # Detailed token info
    st.markdown("---")
    st.caption("**Token Details**")
    detail_cols = st.columns(3)
    with detail_cols[0]:
        st.metric("Used Today", f"{tokens_used:,}")
    with detail_cols[1]:
        st.metric("Remaining", f"{tokens_remaining:,}")
    with detail_cols[2]:
        st.metric("Requests", f"{requests_today}")
    st.caption("💡 Groq free tier resets daily at midnight UTC")

# Store advanced options in session state for processing
st.session_state.focus_area = focus_area if 'focus_area' in dir() else "General"
st.session_state.tone = tone if 'tone' in dir() else "Professional"

# Add session state for tracking if processing is complete
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# Show Summarize button (only show once, clean state)
run = st.button("✨ Summarize", type="primary", use_container_width=True)

# Check for auto-process from history re-process
auto_process_url = st.session_state.pop('auto_process_url', None)
if auto_process_url:
    st.info(f"🔄 Re-processing: {auto_process_url[:60]}...")
    input_type = "url"
    content = auto_process_url
    run = True  # Trigger processing


# ============================================================================
# Processing Functions
# ============================================================================

def clean_pdf_text(raw_text):
    """Clean and format PDF extracted text into proper paragraphs"""
    import re
    
    # Remove excessive whitespace while preserving intentional breaks
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', raw_text)
    
    # Remove spaces around newlines
    text = re.sub(r' *\n *', '\n', text)
    
    # Replace multiple newlines with double newline (paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Split into lines
    lines = text.split('\n')
    
    # Rebuild paragraphs
    paragraphs = []
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            if current_paragraph:
                # End current paragraph
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
            continue
        
        # Check if line ends with sentence-ending punctuation
        ends_sentence = line.endswith(('.', '!', '?', ':', ';'))
        
        # Add line to current paragraph
        current_paragraph.append(line)
        
        # If line ends with punctuation and is reasonably long, might be paragraph end
        if ends_sentence and len(line) > 40:
            # Check if next context suggests new paragraph (optional)
            paragraphs.append(' '.join(current_paragraph))
            current_paragraph = []
    
    # Add any remaining paragraph
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))
    
    # Join paragraphs with double newline
    cleaned_text = '\n\n'.join(paragraphs)
    
    return cleaned_text


def create_markdown_from_results(output, filename="summary.md"):
    """Create markdown content from parsed results"""
    try:
        from datetime import datetime
        
        md_content = f"# AI Generated Summary\n\n"
        md_content += f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
        md_content += "────────────────────────────────────────────────────────────────────────────────\n\n"
        
        # Parse takeaways
        if "TAKEAWAYS_START" in output and "TAKEAWAYS_END" in output:
            takeaways_section = output.split("TAKEAWAYS_START")[1].split("TAKEAWAYS_END")[0]
            takeaways = [line.strip() for line in takeaways_section.strip().split('\n') if line.strip()]
            
            if takeaways:
                md_content += "## 🎯 Key Insights\n\n"
                for i, takeaway in enumerate(takeaways, 1):
                    md_content += f"{i}. {takeaway}\n\n"
                md_content += "────────────────────────────────────────────────────────────────────────────────\n\n"
        
        # Parse summary
        if "SUMMARY_START" in output and "SUMMARY_END" in output:
            summary = output.split("SUMMARY_START")[1].split("SUMMARY_END")[0].strip()
            
            if summary:
                md_content += "## 📝 Executive Summary\n\n"
                md_content += summary + "\n\n"
        
        return md_content
    except:
        return output


def display_results(output, show_logs=False):
    """Parse and display summarization results"""
    
    try:
        # Parse takeaways
        if "TAKEAWAYS_START" in output and "TAKEAWAYS_END" in output:
            takeaways_section = output.split("TAKEAWAYS_START")[1].split("TAKEAWAYS_END")[0]
            takeaways = [line.strip() for line in takeaways_section.strip().split('\n') if line.strip()]
            
            if takeaways:
                st.markdown("---")
                st.subheader("🎯 Key Insights")
                for i, takeaway in enumerate(takeaways, 1):
                    st.markdown(f"**{i}.** {takeaway}")
        
        # Parse summary
        if "SUMMARY_START" in output and "SUMMARY_END" in output:
            summary = output.split("SUMMARY_START")[1].split("SUMMARY_END")[0].strip()
            
            if summary:
                st.markdown("---")
                st.subheader("📝 Executive Summary")
                st.markdown(summary)
        
        # Parse transcript if available
        if "TRANSCRIPT_START" in output and "TRANSCRIPT_END" in output:
            transcript = output.split("TRANSCRIPT_START")[1].split("TRANSCRIPT_END")[0].strip()
            word_count = len(transcript.split())
            
            with st.expander(f"📄 Full Transcript ({word_count:,} words)"):
                st.text_area("Transcript", transcript, height=400, label_visibility="collapsed")
        
        # Show logs if requested
        if show_logs:
            with st.expander("🔍 Processing Logs"):
                st.code(output)
                
    except Exception as e:
        st.error(f"Error parsing results: {e}")
        with st.expander("🔍 Raw Output"):
            st.code(output)


def process_url(url, words):
    """Process URL (existing functionality)"""
    
    # Show pipeline stages
    status_placeholder = st.empty()
    
    with st.spinner("Processing..."):
        status_placeholder.info("🔍 Analyzing URL...")
        
        env = os.environ.copy()
        env['GROQ_API_KEY'] = GROQ_API_KEY
        
        # Add src directory to PYTHONPATH so subprocess can import content_summarizer module
        src_path = str(ROOT / "src")
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = src_path
        
        # Use direct script path instead of -m flag to avoid module import issues
        script_path = ROOT / "src" / "content_summarizer" / "youtube_slash_command.py"
        
        # Use sys.executable to ensure subprocess uses same Python interpreter with installed packages
        # Get custom prompt settings from session state
        focus = st.session_state.get('focus_area', 'General')
        tone_setting = st.session_state.get('tone', 'Professional')

        cmd = [
            sys.executable, str(script_path), url,
            "--format", "md",
            "--words", str(words),
            "--ai-provider", os.getenv("AI_PROVIDER", "groq"),
            "--ai-model", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "--focus-area", focus,
            "--tone", tone_setting
        ]
        
        status_placeholder.info("📥 Fetching content...")
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)
        status_placeholder.empty()
        
        # Check for AI provider confirmation
        out = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
        
        mm = re.search(r"Using\s+(\w+)\s+AI\s*\(model:\s*([^)]+)\)", out)
        if mm:
            provider, model = mm.group(1), mm.group(2)
            st.success(f"✅ AI Provider: {provider} • Model: {model}")
        
        # Check for warnings
        warnings = []
        if "Music video detected" in out:
            warnings.append("⚠️ Music video - transcript is mostly lyrics")
        if "Very short content" in out:
            warnings.append("⚠️ Content is very short")
        
        if warnings:
            st.warning("**Content Quality Notes:**\n\n" + "\n".join(f"- {w}" for w in warnings))
        
        # Try to parse markdown file output
        m = re.search(r"Markdown document saved:\s*(.+)", out)
        if res.returncode == 0 and m:
            path = m.group(1).strip()
            st.success(f"✅ Summary generated successfully")

            # Track token usage (estimate based on output + typical input)
            estimated_tokens = estimate_processing_tokens('url', words)
            save_token_usage(estimated_tokens)
            
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Save to session state so it persists across reruns
                    st.session_state.last_result = {
                        'content': content,
                        'filename': os.path.basename(path),
                        'url': url  # Store URL for history
                    }

                    # Extract title from markdown content
                    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    title = title_match.group(1) if title_match else os.path.basename(path)

                    # Determine content type from URL
                    if 'youtube.com' in url or 'youtu.be' in url:
                        content_type = 'video'
                    elif any(x in url for x in ['spotify.com', 'apple.com/podcast', 'podcasts.apple.com', '.rss', '/rss', '/feed']):
                        content_type = 'podcast'
                    else:
                        content_type = 'article'

                    # Extract summary preview
                    summary_match = re.search(r'## 📝 Executive Summary\s+(.+?)(?=\n##|\n---|\Z)', content, re.DOTALL)
                    summary_preview = summary_match.group(1).strip()[:300] if summary_match else ""

                    # Record in history
                    record_history(
                        url=url,
                        title=title,
                        content_type=content_type,
                        source_label="URL",
                        summary=summary_preview
                    )

                except Exception as e:
                    st.warning(f"Could not read saved file: {e}")
                    with st.expander("🔍 Processing Output"):
                        st.code(out)
            else:
                with st.expander("🔍 Processing Output"):
                    st.code(out)
        else:
            st.error("❌ Failed to generate summary. Check output below.")
            with st.expander("🔍 Error Details"):
                st.code(out)


def display_url_results():
    """Display saved URL processing results with download and process another buttons"""
    if 'last_result' in st.session_state and st.session_state.last_result:
        content = st.session_state.last_result['content']
        filename = st.session_state.last_result['filename']
        
        # Download button (blue) - primary style
        st.download_button(
            "📥 Download Markdown",
            content,
            file_name=filename,
            mime="text/markdown",
            use_container_width=True,
            type="primary",  # Blue button
            key="download_btn"
        )
        
        # Green Process Another button below download
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
        if st.button("📝 Process Another", type="secondary", use_container_width=True, key="process_another_url"):
            # Clear ALL session state for inputs
            st.session_state.last_result = None
            st.session_state.input_cleared = st.session_state.get('input_cleared', 0) + 1
            st.session_state.file_cleared = st.session_state.get('file_cleared', 0) + 1
            st.session_state.text_cleared = st.session_state.get('text_cleared', 0) + 1
            st.rerun()
        
        st.markdown("---")
        st.markdown(content)


def process_file(uploaded_file, words):
    """Process uploaded audio/video/PDF file"""

    # Check if PDF
    is_pdf = uploaded_file.name.lower().endswith('.pdf')

    # Get custom prompt settings from session state
    focus = st.session_state.get('focus_area', 'General')
    tone_setting = st.session_state.get('tone', 'Professional')
    
    # Create progress placeholder
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    try:
        # Step 1: Save file
        progress_text.text("📤 Stage 1/3: Uploading file...")
        progress_bar.progress(0.1)
        
        temp_dir = Path(tempfile.mkdtemp())
        temp_path = temp_dir / uploaded_file.name
        
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Step 2: Extract/Transcribe
        if is_pdf:
            progress_text.text("📄 Stage 2/3: Extracting text from PDF...")
            progress_bar.progress(0.3)
        else:
            progress_text.text("🎤 Stage 2/3: Transcribing audio with Whisper (this may take a few minutes)...")
            progress_bar.progress(0.3)
        
        env = os.environ.copy()
        env['GROQ_API_KEY'] = GROQ_API_KEY
        
        # Add src directory to PYTHONPATH for module imports
        src_path = str(ROOT / "src")
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = src_path
        
        # Escape filename for script
        safe_filename = uploaded_file.name.replace('"', '\\"')
        
        if is_pdf:
            # PDF processing
            # Note: GROQ_API_KEY is passed via subprocess env parameter, not embedded in script
            transcribe_script = f'''
import sys
import os

from content_summarizer.ai_summarizer import AITranscriptSummarizer

try:
    # Extract text from PDF
    print("Extracting text from PDF...", file=sys.stderr)
    
    # Helper function to clean PDF text into paragraphs
    def clean_pdf_text(text):
        import re
        
        # Remove excessive spaces
        text = re.sub(r' +', ' ', text)
        
        # Split into lines
        lines = [line.strip() for line in text.split('\\n')]
        
        # Merge lines into paragraphs
        paragraphs = []
        current_para = []
        
        for i, line in enumerate(lines):
            if not line:
                # Empty line = paragraph break
                if current_para:
                    paragraphs.append(' '.join(current_para))
                    current_para = []
                continue
            
            # Add line to current paragraph
            current_para.append(line)
            
            # Determine if this line ends a paragraph
            # Check if line ends with sentence punctuation
            ends_sentence = line and line[-1] in '.!?:;'
            
            # If ends with punctuation and line is substantial, end paragraph
            if ends_sentence and len(line) > 50:
                paragraphs.append(' '.join(current_para))
                current_para = []
        
        # Add any remaining text
        if current_para:
            paragraphs.append(' '.join(current_para))
        
        # Join paragraphs with double newline
        return '\\n\\n'.join(paragraphs)
    
    try:
        # Try pdfplumber first (better text extraction)
        import pdfplumber
        
        with pdfplumber.open("{temp_path}") as pdf:
            raw_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\\n\\n"
        
        transcript = clean_pdf_text(raw_text)
        
    except (ImportError, Exception) as e:
        # Fallback: use PyPDF2
        print(f"pdfplumber failed, trying PyPDF2: {{e}}", file=sys.stderr)
        import PyPDF2
        
        with open("{temp_path}", 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            raw_text = ""
            for page in reader.pages:
                raw_text += page.extract_text() + "\\n"
        
        transcript = clean_pdf_text(raw_text)
    
    print(f"Text extraction complete: {{len(transcript)}} characters", file=sys.stderr)

    # Summarize
    print("Starting summarization...", file=sys.stderr)
    summarizer = AITranscriptSummarizer(provider='groq', model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'))
    takeaways = summarizer.generate_key_takeaways(transcript, "{safe_filename}", count=5, focus_area="{focus}", tone="{tone_setting}")
    summary = summarizer.generate_executive_summary(transcript, "{safe_filename}", word_count={words}, focus_area="{focus}", tone="{tone_setting}")

    # Save to correct folder (PDFs go to article folder)
    from pathlib import Path
    from datetime import datetime
    
    # Create folder structure
    base_dir = Path.home() / "Documents" / "zz. AI Content Summaries" / "article"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in "{safe_filename}" if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
    output_file = base_dir / f"{{safe_name}}_{{timestamp}}.md"
    
    # Save markdown
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {{safe_name}}\\n\\n")
        f.write(f"**Source:** PDF Document\\n")
        f.write(f"**Generated:** {{datetime.now().strftime('%B %d, %Y at %I:%M %p')}}\\n\\n")
        f.write("────────────────────────────────────────────────────────────────────────────────\\n\\n")
        f.write("## 🎯 Key Insights\\n\\n")
        for i, t in enumerate(takeaways, 1):
            f.write(f"{{i}}. {{t}}\\n\\n")
        f.write("────────────────────────────────────────────────────────────────────────────────\\n\\n")
        f.write("## 📝 Executive Summary\\n\\n")
        f.write(summary + "\\n\\n")
    
    print(f"SAVED_TO:{{output_file}}")
    
    # Output
    print("TRANSCRIPT_START")
    print(transcript)
    print("TRANSCRIPT_END")
    print("TAKEAWAYS_START")
    for t in takeaways:
        print(t)
    print("TAKEAWAYS_END")
    print("SUMMARY_START")
    print(summary)
    print("SUMMARY_END")
    
except Exception as e:
    print(f"ERROR: {{e}}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
'''
        else:
            # Audio/Video processing
            # Note: GROQ_API_KEY is passed via subprocess env parameter, not embedded in script
            transcribe_script = f'''
import sys
import os

from content_summarizer.youtube_slash_command import transcribe_audio_whisper
from content_summarizer.ai_summarizer import AITranscriptSummarizer

try:
    # Transcribe (allow up to 2 hours)
    print("Starting transcription...", file=sys.stderr)
    transcript, mode = transcribe_audio_whisper("{temp_path}", mode='full', max_duration_minutes=120)
    print(f"Transcription complete: {{len(transcript)}} characters", file=sys.stderr)

    # Summarize
    print("Starting summarization...", file=sys.stderr)
    summarizer = AITranscriptSummarizer(provider='groq', model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'))
    takeaways = summarizer.generate_key_takeaways(transcript, "{safe_filename}", count=5, focus_area="{focus}", tone="{tone_setting}")
    summary = summarizer.generate_executive_summary(transcript, "{safe_filename}", word_count={words}, focus_area="{focus}", tone="{tone_setting}")

    # Save to correct folder (Zoom files go to youtube folder)
    import os
    from pathlib import Path
    from datetime import datetime
    
    # Create folder structure
    base_dir = Path.home() / "Documents" / "zz. AI Content Summaries" / "youtube"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in "{safe_filename}" if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
    output_file = base_dir / f"{{safe_name}}_{{timestamp}}.md"
    
    # Save markdown
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {{safe_name}}\\n\\n")
        f.write(f"**Source:** Uploaded File\\n")
        f.write(f"**Generated:** {{datetime.now().strftime('%B %d, %Y at %I:%M %p')}}\\n\\n")
        f.write("────────────────────────────────────────────────────────────────────────────────\\n\\n")
        f.write("## 🎯 Key Insights\\n\\n")
        for i, t in enumerate(takeaways, 1):
            f.write(f"{{i}}. {{t}}\\n\\n")
        f.write("────────────────────────────────────────────────────────────────────────────────\\n\\n")
        f.write("## 📝 Executive Summary\\n\\n")
        f.write(summary + "\\n\\n")
    
    print(f"SAVED_TO:{{output_file}}")
    
    # Output
    print("TRANSCRIPT_START")
    print(transcript)
    print("TRANSCRIPT_END")
    print("TAKEAWAYS_START")
    for t in takeaways:
        print(t)
    print("TAKEAWAYS_END")
    print("SUMMARY_START")
    print(summary)
    print("SUMMARY_END")
    
except Exception as e:
    print(f"ERROR: {{e}}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
'''
        
        result = subprocess.run(
            [sys.executable, '-c', transcribe_script],
            capture_output=True,
            text=True,
            env=env,
            timeout=600  # 10 min timeout
        )
        
        # Cleanup
        try:
            temp_path.unlink()
            temp_dir.rmdir()
        except:
            pass
        
        progress_text.text("✨ Stage 3/3: Generating insights with AI...")
        progress_bar.progress(0.9)
        
        if result.returncode == 0:
            progress_bar.progress(1.0)
            progress_text.empty()
            progress_bar.empty()

            # Track token usage (estimate based on file processing)
            estimated_tokens = estimate_processing_tokens('file', words)
            save_token_usage(estimated_tokens)

            # Check if file was saved
            saved_match = re.search(r"SAVED_TO:(.+)", result.stdout)
            if saved_match:
                saved_path = saved_match.group(1).strip()
                st.success(f"✅ Processing complete! Saved to: {saved_path}")
            else:
                st.success("✅ Processing complete!")
            
            # Parse the markdown file that was saved
            saved_match = re.search(r"SAVED_TO:(.+)", result.stdout)
            if saved_match:
                saved_path = saved_match.group(1).strip()
                if os.path.exists(saved_path):
                    with open(saved_path, 'r', encoding='utf-8') as f:
                        md_content = f.read()

                    # Save to session state for persistent display
                    st.session_state.file_result = {
                        'content': md_content,
                        'filename': uploaded_file.name
                    }

                    # Determine content type
                    if is_pdf:
                        content_type = 'article'
                    else:
                        content_type = 'video'  # Audio/video files

                    # Extract summary preview
                    summary_match = re.search(r'## 📝 Executive Summary\s+(.+?)(?=\n##|\n---|\Z)', md_content, re.DOTALL)
                    summary_preview = summary_match.group(1).strip()[:300] if summary_match else ""

                    # Record in history
                    record_history(
                        url=f"file://{uploaded_file.name}",
                        title=uploaded_file.name,
                        content_type=content_type,
                        source_label="Uploaded File",
                        summary=summary_preview
                    )

            # Results will be displayed below
        else:
            progress_bar.empty()
            progress_text.empty()
            
            # Determine which stage failed based on stderr
            stderr = result.stderr or ""
            if "Extracting text from PDF" in stderr or "extract_text" in stderr:
                st.error("❌ Failed at Stage 2: PDF text extraction")
                st.info("💡 **Tip:** Ensure the PDF has extractable text (not scanned images)")
            elif "Starting transcription" in stderr or "Whisper" in stderr or "transcribe" in stderr:
                st.error("❌ Failed at Stage 2: Audio transcription")
                st.info("💡 **Tip:** Ensure the file has clear audio. Try using 'Paste Text' tab instead.")
            elif "Starting summarization" in stderr:
                st.error("❌ Failed at Stage 3: AI summarization")
                st.info("💡 **Tip:** Check your internet connection (Groq API required)")
            else:
                st.error("❌ Processing failed")
            
            with st.expander("🔍 Error Details"):
                st.code("STDOUT:\n" + (result.stdout or "(empty)"))
                st.code("STDERR:\n" + (result.stderr or "(empty)"))
            
    except subprocess.TimeoutExpired:
        progress_bar.empty()
        progress_text.empty()
        st.error("❌ Failed at Stage 2: Processing timed out (>10 minutes)")
        st.info("💡 **Tip:** Try a shorter file or use the 'Paste Text' tab for pre-transcribed content")
        
    except Exception as e:
        progress_bar.empty()
        progress_text.empty()
        st.error(f"❌ Failed at Stage 1: File upload - {e}")
        
        import traceback
        with st.expander("🔍 Technical Details"):
            st.code(traceback.format_exc())


def process_text(text_content, words):
    """Process pasted text directly"""

    # Get custom prompt settings from session state
    focus = st.session_state.get('focus_area', 'General')
    tone_setting = st.session_state.get('tone', 'Professional')

    status_placeholder = st.empty()
    status_placeholder.info("✨ Generating AI summary...")
    
    with st.spinner("Processing text..."):
        env = os.environ.copy()
        env['GROQ_API_KEY'] = GROQ_API_KEY
        
        # Add src directory to PYTHONPATH for module imports
        src_path = str(ROOT / "src")
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = src_path
        
        # Escape text content for Python script
        escaped_text = text_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
        
        # Note: GROQ_API_KEY is passed via subprocess env parameter, not embedded in script
        # Safely encode text content to avoid injection via triple quotes
        import base64
        encoded_text = base64.b64encode(text_content.encode('utf-8')).decode('ascii')

        summarize_script = f'''
import os
import base64

from content_summarizer.ai_summarizer import AITranscriptSummarizer

# Decode text safely to avoid code injection from user content
transcript = base64.b64decode("{encoded_text}").decode('utf-8')
title = "Pasted Content"

try:
    summarizer = AITranscriptSummarizer(provider='groq', model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'))
    takeaways = summarizer.generate_key_takeaways(transcript, title, count=5, focus_area="{focus}", tone="{tone_setting}")
    summary = summarizer.generate_executive_summary(transcript, title, word_count={words}, focus_area="{focus}", tone="{tone_setting}")

    # Save to correct folder (pasted text goes to article folder)
    from pathlib import Path
    from datetime import datetime
    
    # Create folder structure
    base_dir = Path.home() / "Documents" / "zz. AI Content Summaries" / "article"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Try to create a meaningful name from first few words
    first_words = " ".join(transcript.split()[:5])
    safe_name = "".join(c for c in first_words if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
    if not safe_name:
        safe_name = "pasted_content"
    output_file = base_dir / f"{{safe_name}}_{{timestamp}}.md"
    
    # Save markdown
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {{safe_name}}\\n\\n")
        f.write(f"**Source:** Pasted Text\\n")
        f.write(f"**Generated:** {{datetime.now().strftime('%B %d, %Y at %I:%M %p')}}\\n\\n")
        f.write("────────────────────────────────────────────────────────────────────────────────\\n\\n")
        f.write("## 🎯 Key Insights\\n\\n")
        for i, t in enumerate(takeaways, 1):
            f.write(f"{{i}}. {{t}}\\n\\n")
        f.write("────────────────────────────────────────────────────────────────────────────────\\n\\n")
        f.write("## 📝 Executive Summary\\n\\n")
        f.write(summary + "\\n\\n")
    
    print(f"SAVED_TO:{{output_file}}")
    
    print("TAKEAWAYS_START")
    for t in takeaways:
        print(t)
    print("TAKEAWAYS_END")
    print("SUMMARY_START")
    print(summary)
    print("SUMMARY_END")
    
except Exception as e:
    print(f"ERROR: {{e}}")
    import traceback
    traceback.print_exc()
'''
        
        result = subprocess.run(
            [sys.executable, '-c', summarize_script],
            capture_output=True,
            text=True,
            env=env,
            timeout=120
        )
        
        status_placeholder.empty()
        
        if result.returncode == 0:
            # Track token usage (estimate based on text processing)
            estimated_tokens = estimate_processing_tokens('text', words)
            save_token_usage(estimated_tokens)

            # Check if file was saved
            saved_match = re.search(r"SAVED_TO:(.+)", result.stdout)
            if saved_match:
                saved_path = saved_match.group(1).strip()
                st.success(f"✅ Summary generated! Saved to: {saved_path}")
            else:
                st.success("✅ Summary generated successfully!")
            
            # Parse the markdown file that was saved
            saved_match = re.search(r"SAVED_TO:(.+)", result.stdout)
            if saved_match:
                saved_path = saved_match.group(1).strip()
                if os.path.exists(saved_path):
                    with open(saved_path, 'r', encoding='utf-8') as f:
                        md_content = f.read()

                    # Save to session state for persistent display
                    st.session_state.text_result = {
                        'content': md_content,
                        'filename': 'pasted_content.md'
                    }

                    # Extract title from markdown content
                    title_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
                    title = title_match.group(1) if title_match else "Pasted Content"

                    # Extract summary preview
                    summary_match = re.search(r'## 📝 Executive Summary\s+(.+?)(?=\n##|\n---|\Z)', md_content, re.DOTALL)
                    summary_preview = summary_match.group(1).strip()[:300] if summary_match else ""

                    # Record in history
                    record_history(
                        url="text://pasted-content",
                        title=title,
                        content_type="article",
                        source_label="Pasted Text",
                        summary=summary_preview
                    )

            # Results will be displayed below
        else:
            st.error("❌ Failed to generate summary")
            stderr = result.stderr or ""
            if "summarization" in stderr.lower():
                st.info("💡 **Tip:** Check your internet connection (Groq API required)")
            with st.expander("🔍 Error Details"):
                st.code("STDOUT:\n" + (result.stdout or "(empty)"))
                st.code("STDERR:\n" + (result.stderr or "(empty)"))


# ============================================================================
# Main Processing Logic
# ============================================================================

if run:
    if not content:
        st.error("❌ Please provide content in one of the tabs above")
    elif input_type == "url":
        process_url(content, words)
        # Results will be displayed below after session state is set
    elif input_type == "file":
        # Check file size (200 MB limit for cloud deployments)
        if content.size > 200 * 1024 * 1024:
            st.error("❌ File too large. Maximum size: 200 MB")
        else:
            process_file(content, words)
    elif input_type == "text":
        process_text(content, words)

# Display results if available (persists across download button clicks)
if 'last_result' in st.session_state and st.session_state.last_result:
    display_url_results()

# Display file upload results
if 'file_result' in st.session_state and st.session_state.file_result:
    content = st.session_state.file_result['content']
    filename = st.session_state.file_result['filename']
    
    # Blue download button
    st.download_button(
        "📥 Download Markdown",
        content,
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
        # Clear ALL session state for inputs
        st.session_state.file_result = None
        st.session_state.input_cleared = st.session_state.get('input_cleared', 0) + 1
        st.session_state.file_cleared = st.session_state.get('file_cleared', 0) + 1
        st.session_state.text_cleared = st.session_state.get('text_cleared', 0) + 1
        st.rerun()
    
    st.markdown("---")
    st.markdown(content)

# Display text paste results
if 'text_result' in st.session_state and st.session_state.text_result:
    content = st.session_state.text_result['content']
    filename = st.session_state.text_result['filename']
    
    # Blue download button
    st.download_button(
        "📥 Download Markdown",
        content,
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
        # Clear ALL session state for inputs
        st.session_state.text_result = None
        st.session_state.input_cleared = st.session_state.get('input_cleared', 0) + 1
        st.session_state.file_cleared = st.session_state.get('file_cleared', 0) + 1
        st.session_state.text_cleared = st.session_state.get('text_cleared', 0) + 1
        st.rerun()
    
    st.markdown("---")
    st.markdown(content)
