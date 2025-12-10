#!/usr/bin/env python3
import sys
import os
import re
import subprocess
import streamlit as st
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path for module imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from content_summarizer.style import apply_dark_mode

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
for optional_key in ['LISTEN_NOTES_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
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

# === NEW: Tabbed Input Interface ===
tab1, tab2, tab3 = st.tabs(["🔗 URL", "📎 Upload File", "📝 Paste Text"])

input_type = None
content = None

with tab1:
    st.markdown("### Enter a URL")
    url_input = st.text_input(
        "Enter URL",
        placeholder="https://youtube.com/watch?v=... or podcast/article URL",
        label_visibility="collapsed",
        key="url_input"
    )
    if url_input:
        input_type = "url"
        content = url_input

with tab2:
    st.markdown("### Upload Audio, Video, or PDF File")
    st.caption("📁 Supported: MP4, MP3, M4A, WAV, MOV, AVI, PDF (Zoom recordings, audio files, documents, etc.)")
    
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

with tab3:
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

# Shared controls
st.markdown("---")
words = st.slider("📊 Summary length (words)", 50, 3000, DEFAULT_WORDS, step=50)

# Add session state for tracking if processing is complete
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# Show Summarize button (only show once, clean state)
run = st.button("✨ Summarize", type="primary", use_container_width=True)


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
        cmd = [
            sys.executable, str(script_path), url,
            "--format", "md",
            "--words", str(words),
            "--ai-provider", os.getenv("AI_PROVIDER", "groq"),
            "--ai-model", os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
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
            
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Save to session state so it persists across reruns
                    st.session_state.last_result = {
                        'content': content,
                        'filename': os.path.basename(path)
                    }
                    
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
            # Clear session state
            st.session_state.last_result = None
            st.rerun()
        
        st.markdown("---")
        st.markdown(content)


def process_file(uploaded_file, words):
    """Process uploaded audio/video/PDF file"""
    
    # Check if PDF
    is_pdf = uploaded_file.name.lower().endswith('.pdf')
    
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
    summarizer = AITranscriptSummarizer(provider='groq', model='llama-3.1-8b-instant')
    takeaways = summarizer.generate_key_takeaways(transcript, "{safe_filename}", count=5)
    summary = summarizer.generate_executive_summary(transcript, "{safe_filename}", word_count={words})
    
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
    summarizer = AITranscriptSummarizer(provider='groq', model='llama-3.1-8b-instant')
    takeaways = summarizer.generate_key_takeaways(transcript, "{safe_filename}", count=5)
    summary = summarizer.generate_executive_summary(transcript, "{safe_filename}", word_count={words})
    
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
    summarizer = AITranscriptSummarizer(provider='groq', model='llama-3.1-8b-instant')
    takeaways = summarizer.generate_key_takeaways(transcript, title, count=5)
    summary = summarizer.generate_executive_summary(transcript, title, word_count={words})
    
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
        # Clear session state and increment file cleared counter
        st.session_state.file_result = None
        st.session_state.file_cleared = st.session_state.get('file_cleared', 0) + 1
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
        # Clear session state and set text cleared flag
        st.session_state.text_result = None
        st.session_state.text_cleared = st.session_state.get('text_cleared', 0) + 1
        st.rerun()
    
    st.markdown("---")
    st.markdown(content)
