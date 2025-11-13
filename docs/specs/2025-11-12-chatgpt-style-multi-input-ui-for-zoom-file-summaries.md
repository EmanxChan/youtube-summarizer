## Elegant Multi-Input UI with File Upload & Text Paste

### Goal
Transform the Streamlit UI into a ChatGPT-style interface with:
- **URL input** (existing)
- **File upload** (audio/video for Whisper transcription)
- **Text paste** (direct transcript input)
- All elegantly combined in a single, unified input area

---

## UI/UX Design (ChatGPT-Inspired)

### Current Interface:
```
[Text box: "YouTube, Podcast, or Article URL"]
[Number input: "Summary length (words)"]
[Button: "✨ Summarize"]
```

### New Interface (Unified Input):
```
┌─────────────────────────────────────────────────────────┐
│ 📚 Content Summarizer                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Tab: 🔗 URL]  [Tab: 📎 Upload]  [Tab: 📝 Paste]     │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Enter URL or paste text...               📎 [↑] │   │
│  │                                                 │   │
│  │ (Smart input that detects: URL, file, text)    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  💡 Summary length: [slider: 50-3000 words]            │
│                                                         │
│  [            ✨ Summarize             ]                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key Design Principles:**
1. ✨ **Unified experience** - One input area adapts to content type
2. 📎 **Visual attachment icon** - Like ChatGPT's paperclip
3. 🎯 **Smart detection** - Auto-detects URL vs text vs file
4. 🎨 **Clean & minimal** - No clutter, intuitive flow

---

## Implementation Approach

### Option A: Tab-Based Interface (Cleaner, Recommended)

**Layout:**
- **Tab 1: 🔗 URL** - Text input for YouTube/Podcast/Article URLs
- **Tab 2: 📎 Upload** - File uploader for audio/video (MP4, MP3, M4A, WAV)
- **Tab 3: 📝 Paste** - Text area for pasting transcripts

```python
import streamlit as st

# Create tabs
tab1, tab2, tab3 = st.tabs(["🔗 URL", "📎 Upload File", "📝 Paste Text"])

with tab1:
    url = st.text_input(
        "Enter URL",
        placeholder="https://youtube.com/... or podcast URL",
        label_visibility="collapsed"
    )
    input_source = "url"
    content = url

with tab2:
    uploaded_file = st.file_uploader(
        "Upload audio or video file",
        type=['mp4', 'mp3', 'm4a', 'wav', 'mov'],
        label_visibility="collapsed"
    )
    input_source = "file"
    content = uploaded_file

with tab3:
    text_input = st.text_area(
        "Paste transcript or text",
        height=200,
        placeholder="Paste your Zoom transcript, meeting notes, or any text...",
        label_visibility="collapsed"
    )
    input_source = "text"
    content = text_input

# Shared controls (outside tabs)
words = st.slider("Summary length (words)", 50, 3000, 500)
run = st.button("✨ Summarize", type="primary", use_container_width=True)
```

**Pros:**
- ✅ Clean separation of input types
- ✅ Easy to understand
- ✅ Streamlit-native design
- ✅ Mobile-friendly

**Cons:**
- Less "ChatGPT-like" (more traditional)
- Requires tab switching

---

### Option B: Unified Input with Smart Detection (More ChatGPT-like)

**Layout:**
- Single text area that accepts URLs or pasted text
- File upload icon/button integrated into the text area
- Smart detection of input type

```python
import streamlit as st

# Create columns for unified input
col1, col2 = st.columns([9, 1])

with col1:
    # Main input area
    text_input = st.text_area(
        "Enter URL, paste text, or upload file",
        height=100,
        placeholder="Paste YouTube URL, meeting transcript, or text...",
        label_visibility="collapsed",
        key="main_input"
    )

with col2:
    st.write("")  # Spacing
    # File upload button (styled as icon)
    uploaded_file = st.file_uploader(
        "📎",
        type=['mp4', 'mp3', 'm4a', 'wav', 'mov', 'txt'],
        label_visibility="collapsed",
        key="file_upload"
    )

# Smart detection logic
if uploaded_file:
    input_type = "file"
    content = uploaded_file
elif text_input and (text_input.startswith('http') or 'youtube.com' in text_input or 'youtu.be' in text_input):
    input_type = "url"
    content = text_input.strip()
elif text_input and len(text_input) > 100:
    input_type = "text"
    content = text_input
else:
    input_type = None
    content = None
```

**Pros:**
- ✅ Most ChatGPT-like
- ✅ Unified experience
- ✅ No tab switching

**Cons:**
- Less obvious for new users
- Harder to style file uploader as icon
- Streamlit limitations on customization

---

## Recommended Approach: **Tab-Based (Option A)**

**Reasoning:**
1. Streamlit's native tab component is clean and intuitive
2. Clear separation reduces user confusion
3. Easier to implement and maintain
4. Mobile-friendly out of the box
5. Professional appearance
6. Follows Streamlit design patterns

**ChatGPT-like elements we can add:**
- Large, prominent input areas
- Unified "Summarize" button below all tabs
- Smart placeholder text
- File icons and visual indicators
- Responsive feedback

---

## Technical Implementation Plan

### 1. Update `summarizer_ui.py`

**New Structure:**
```python
# Page config (existing)
st.set_page_config(...)

# Title and info (existing)
st.title("📚 Content Summarizer")
st.info("✨ Supports URLs, files, and text")

# === NEW: Tabbed Input Interface ===
tab1, tab2, tab3 = st.tabs(["🔗 URL", "📎 Upload File", "📝 Paste Text"])

input_type = None
content = None

with tab1:
    url_input = st.text_input(
        "Enter URL",
        placeholder="YouTube, Podcast, or Article URL",
        label_visibility="collapsed"
    )
    if url_input:
        input_type = "url"
        content = url_input

with tab2:
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['mp4', 'mp3', 'm4a', 'wav', 'mov', 'avi'],
        help="Upload Zoom recording, audio file, or video",
        label_visibility="collapsed"
    )
    if uploaded_file:
        input_type = "file"
        content = uploaded_file
        st.info(f"📎 {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.1f} MB)")

with tab3:
    text_area = st.text_area(
        "Paste content",
        height=300,
        placeholder="Paste your transcript, meeting notes, article text, or any content...",
        label_visibility="collapsed"
    )
    if text_area and len(text_area.strip()) > 50:
        input_type = "text"
        content = text_area
        word_count = len(text_area.split())
        st.info(f"📝 {word_count:,} words pasted")

# Shared controls
words = st.slider("Summary length (words)", 50, 3000, 500)
run = st.button("✨ Summarize", type="primary", use_container_width=True)

# Process based on input type
if run:
    if not content:
        st.error("Please provide content in one of the tabs above")
    elif input_type == "url":
        # Existing URL processing
        process_url(content, words)
    elif input_type == "file":
        # NEW: File processing
        process_file(content, words)
    elif input_type == "text":
        # NEW: Text processing
        process_text(content, words)
```

---

### 2. Create File Processing Function

**New function in `summarizer_ui.py`:**
```python
def process_file(uploaded_file, words):
    """Process uploaded audio/video file"""
    
    with st.spinner("Processing file..."):
        # Save uploaded file temporarily
        import tempfile
        from pathlib import Path
        
        temp_dir = Path(tempfile.mkdtemp())
        temp_path = temp_dir / uploaded_file.name
        
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        st.info("🎤 Transcribing audio with Whisper...")
        
        # Call transcription function
        env = os.environ.copy()
        env['GROQ_API_KEY'] = GROQ_API_KEY
        
        # Create Python script to transcribe
        transcribe_script = f'''
import sys
sys.path.insert(0, "/Users/e.chan")
from youtube_slash_command import transcribe_audio_whisper
from ai_summarizer import AITranscriptSummarizer

# Transcribe
transcript, mode = transcribe_audio_whisper("{temp_path}", mode='full', max_duration_minutes=60)

# Summarize
summarizer = AITranscriptSummarizer(provider='groq', model='llama-3.1-8b-instant')
takeaways = summarizer.generate_key_takeaways(transcript, "{uploaded_file.name}", count=5)
summary = summarizer.generate_executive_summary(transcript, "{uploaded_file.name}", word_count={words})

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
'''
        
        # Run transcription + summarization
        result = subprocess.run(
            ['python3', '-c', transcribe_script],
            capture_output=True,
            text=True,
            env=env,
            timeout=600  # 10 min timeout
        )
        
        # Cleanup
        temp_path.unlink()
        temp_dir.rmdir()
        
        # Parse and display results
        display_results(result.stdout)
```

---

### 3. Create Text Processing Function

**New function in `summarizer_ui.py`:**
```python
def process_text(text_content, words):
    """Process pasted text directly"""
    
    with st.spinner("Processing text..."):
        env = os.environ.copy()
        env['GROQ_API_KEY'] = GROQ_API_KEY
        
        # Create Python script to summarize
        # Escape text content properly
        escaped_text = text_content.replace('"', '\\"').replace('\n', '\\n')
        
        summarize_script = f'''
import os
os.environ["GROQ_API_KEY"] = "{GROQ_API_KEY}"

from ai_summarizer import AITranscriptSummarizer

transcript = """{text_content}"""
title = "Pasted Content"

summarizer = AITranscriptSummarizer(provider='groq', model='llama-3.1-8b-instant')
takeaways = summarizer.generate_key_takeaways(transcript, title, count=5)
summary = summarizer.generate_executive_summary(transcript, title, word_count={words})

print("TAKEAWAYS_START")
for t in takeaways:
    print(t)
print("TAKEAWAYS_END")
print("SUMMARY_START")
print(summary)
print("SUMMARY_END")
'''
        
        result = subprocess.run(
            ['python3', '-c', summarize_script],
            capture_output=True,
            text=True,
            env=env,
            timeout=60
        )
        
        display_results(result.stdout)
```

---

### 4. Shared Display Function

**Helper function:**
```python
def display_results(output):
    """Parse and display summarization results"""
    
    # Parse takeaways
    if "TAKEAWAYS_START" in output:
        takeaways_section = output.split("TAKEAWAYS_START")[1].split("TAKEAWAYS_END")[0]
        takeaways = [line.strip() for line in takeaways_section.strip().split('\n') if line.strip()]
        
        st.subheader("🎯 Key Insights")
        for i, takeaway in enumerate(takeaways, 1):
            st.markdown(f"{i}. {takeaway}")
    
    # Parse summary
    if "SUMMARY_START" in output:
        summary = output.split("SUMMARY_START")[1].split("SUMMARY_END")[0].strip()
        
        st.subheader("📝 Executive Summary")
        st.markdown(summary)
    
    # Show full output in expander
    with st.expander("📄 Full Output"):
        st.code(output)
```

---

## File Format Support

### Audio/Video Formats:
- ✅ **MP4** - Zoom default recording
- ✅ **MP3** - Audio only
- ✅ **M4A** - Apple/iOS recordings
- ✅ **WAV** - Uncompressed audio
- ✅ **MOV** - Mac/iOS video
- ✅ **AVI** - Windows video

### Text Formats:
- ✅ **Plain text** - Direct paste
- ✅ **VTT** - Zoom transcript format
- ✅ **SRT** - Subtitle format
- ⚠️ **TXT upload** - Can add later if needed

---

## Processing Times & User Feedback

### Expected Processing Times:

**URL (YouTube/Podcast):**
- ⚡ 1-3 seconds (Groq)
- Progress: "Processing..."

**File Upload (Audio/Video):**
- 🎤 Transcription: ~5-10% of file duration (30 min meeting = 2-3 min)
- ⚡ Summarization: 1-3 seconds (Groq)
- Progress: 
  1. "Uploading file..." (instant)
  2. "🎤 Transcribing audio with Whisper..." (2-3 min)
  3. "✨ Generating insights with AI..." (1-3 sec)

**Text Paste:**
- ⚡ 1-3 seconds (Groq)
- Progress: "Processing text..."

### Progress Indicators:
```python
# For file uploads
with st.spinner("Processing..."):
    st.progress(0, text="Uploading file...")
    # upload
    st.progress(0.2, text="🎤 Transcribing audio...")
    # transcribe
    st.progress(0.9, text="✨ Generating insights...")
    # summarize
    st.progress(1.0, text="Done!")
```

---

## Visual Enhancements

### 1. Tab Icons & Labels
```python
st.tabs([
    "🔗 URL",           # Web link icon
    "📎 Upload File",   # Paperclip icon (ChatGPT-style)
    "📝 Paste Text"     # Document icon
])
```

### 2. Input Placeholders
- **URL Tab:** "https://youtube.com/watch?v=... or podcast URL"
- **File Tab:** Shows file name, size, and format after upload
- **Text Tab:** "Paste your Zoom transcript, meeting notes, article, or any text..."

### 3. File Upload Styling
```python
# Show file info after upload
if uploaded_file:
    st.success(f"✅ Ready to process: {uploaded_file.name}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Size", f"{uploaded_file.size / 1024 / 1024:.1f} MB")
    col2.metric("Type", uploaded_file.type)
    col3.metric("Format", uploaded_file.name.split('.')[-1].upper())
```

### 4. Dark Mode Support
Already implemented! Will work with new tabs automatically.

---

## Error Handling & Edge Cases

### 1. No Input Provided
```python
if run and not content:
    st.error("❌ Please provide content in one of the tabs above")
```

### 2. File Too Large
```python
if uploaded_file and uploaded_file.size > 500 * 1024 * 1024:  # 500 MB limit
    st.error("❌ File too large. Maximum size: 500 MB")
```

### 3. Unsupported Format
```python
if uploaded_file and not uploaded_file.name.endswith(('.mp4', '.mp3', '.m4a', '.wav')):
    st.warning("⚠️ Unsupported format. Trying anyway...")
```

### 4. Transcription Failure
```python
try:
    transcript = transcribe_audio_whisper(...)
except Exception as e:
    st.error(f"❌ Transcription failed: {e}")
    st.info("💡 Try using the 'Paste Text' tab with Zoom's built-in transcript instead")
```

### 5. Text Too Short
```python
if input_type == "text" and len(content.strip()) < 50:
    st.warning("⚠️ Text seems too short for meaningful summarization")
```

---

## Mobile Responsiveness

Streamlit's tabs are mobile-friendly by default:
- ✅ Tabs scroll horizontally on small screens
- ✅ File uploader adapts to mobile
- ✅ Text areas resize appropriately
- ✅ Button spans full width (`use_container_width=True`)

---

## Dependencies Check

### Existing (Already Installed):
- ✅ `streamlit` - UI framework
- ✅ `faster-whisper` - Audio transcription
- ✅ `ai_summarizer` - Groq integration
- ✅ `ffmpeg` - Audio processing (already on system)

### New Requirements:
- ✅ **None!** All dependencies already present

---

## Summary of Changes

### Files to Modify:
1. **`summarizer_ui.py`** - Main UI overhaul
   - Add tabs interface
   - Add file upload processing
   - Add text paste processing
   - Update layout

### New Functions:
1. `process_file(uploaded_file, words)` - Handle file uploads
2. `process_text(text_content, words)` - Handle pasted text
3. `display_results(output)` - Unified result display

### No Changes Needed:
- ✅ `ai_summarizer.py` - Already has Groq
- ✅ `youtube_slash_command.py` - Already has Whisper
- ✅ Whisper transcription - Already functional
- ✅ Groq API - Already integrated

---

## Estimated Time

- **Tab interface:** 15 minutes
- **File upload processing:** 20 minutes
- **Text paste processing:** 10 minutes
- **Display formatting:** 10 minutes
- **Error handling & polish:** 15 minutes
- **Testing:** 10 minutes

**Total:** ~70-80 minutes (1.5 hours)

---

## Final UI Flow

```
User opens: http://localhost:8501

┌─────────────────────────────────────────────┐
│ 📚 Content Summarizer                       │
│ ✨ Supports URLs, files, and text           │
├─────────────────────────────────────────────┤
│                                             │
│  [🔗 URL] [📎 Upload File] [📝 Paste Text] │
│  ──────────────────────────────────────────  │
│                                             │
│  Active Tab Content Shows Here:            │
│                                             │
│  • URL: Text input field                   │
│  • Upload: File selector with drag-drop    │
│  • Paste: Large text area (300px)          │
│                                             │
│  Summary length: [━━━━━━○━━━] 500 words    │
│                                             │
│  [     ✨ Summarize (full width)      ]    │
│                                             │
└─────────────────────────────────────────────┘

After clicking "Summarize":

┌─────────────────────────────────────────────┐
│ 🎯 Key Insights                             │
│ 1. [Insight 1...]                           │
│ 2. [Insight 2...]                           │
│ ...                                         │
│                                             │
│ 📝 Executive Summary                        │
│ [Summary paragraph...]                      │
│                                             │
│ 📄 Full Output [expand ▼]                  │
└─────────────────────────────────────────────┘
```

---

## Ready to Implement?

This spec provides:
✅ ChatGPT-inspired unified interface
✅ Tab-based clean design
✅ File upload for Zoom recordings
✅ Text paste for transcripts
✅ Maintains existing URL functionality
✅ Smart error handling
✅ Mobile-responsive
✅ Dark mode compatible
✅ ~1.5 hours implementation time

All using existing Whisper + Groq infrastructure - no new dependencies needed!