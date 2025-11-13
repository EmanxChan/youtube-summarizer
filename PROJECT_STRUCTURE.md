# Project Structure - Content Summarizer

## 🎯 Main Application Code

**The primary, production-ready code is located in:**
```
/src/content_summarizer/          # Python package (proper structure)
  ├── __init__.py                 # Package initialization
  ├── app.py                      # Main Streamlit UI (entry point)
  ├── youtube_slash_command.py    # Core backend processor (CLI tool)
  ├── ai_summarizer.py            # AI integration (Groq, OpenAI, Anthropic)
  ├── listen_notes_client.py      # Podcast metadata API
  ├── podcast_cache.py            # Podcast caching utilities
  ├── transcript_metrics.py       # Transcript analysis
  ├── style.py                    # Streamlit CSS styling
  ├── processing.py               # Unified content processing
  ├── pdf_utils.py                # PDF extraction and cleaning
  └── extractors/                 # Video/transcript extraction modules
```

### Main Features:
- ✅ PDF upload and text extraction
- ✅ Twitter/X video download and summarization
- ✅ YouTube videos, podcasts, articles
- ✅ Audio/video file uploads (MP4, MP3, M4A, WAV, MOV, AVI)
- ✅ Text paste functionality
- ✅ Dark mode UI
- ✅ Tabbed interface for multiple input methods

## 📦 Directory Organization

### `/src/content_summarizer/` - **MAIN APPLICATION CODE**
Proper Python package structure. All imports use `content_summarizer.*` pattern.
No absolute paths - everything is project-relative.

### `/legacy/`
Contains older versions and experimental code:
- `old_simple_version/` - Previous simplified version (URL-only input)
- Other legacy files - Older iterations kept for reference

### `/tests/`
Test files and test data

### `/docs/`
Documentation and guides

### `/config/`
Configuration files (mostly deprecated)

### `/bin/`
FFmpeg binaries for audio/video processing

### `/output/`
Generated summaries and reports

### `/scripts/`
Helper scripts:
- `run.sh` - Start Streamlit locally

## 🚀 How to Run

### Web UI (Local Development)
```bash
cd src
streamlit run content_summarizer/app.py
```

Or use the helper script:
```bash
./scripts/run.sh
```

### CLI Tool
```bash
cd src
python3 -m content_summarizer.youtube_slash_command <url> --format md --words 500
```

### Environment Setup
1. Copy `.env.example` to `.env`
2. Add your API key: `GROQ_API_KEY=your_key_here`
3. Install dependencies: `pip install -r requirements.txt`

## 📝 For AI Agents & LLMs

**Important:** Always reference and modify code in `/src/content_summarizer/` directory.
- This is a proper Python package with correct import structure
- All imports use `content_summarizer.*` (e.g., `from content_summarizer.ai_summarizer import ...`)
- No absolute paths - everything is relative to project root
- Do NOT use code from `/legacy/` unless specifically asked
- Entry point for UI: `src/content_summarizer/app.py`
- Entry point for CLI: `src/content_summarizer/youtube_slash_command.py`

## 🚢 Deployment

The `Procfile` is configured for Heroku/Render deployment:
```
web: cd src && streamlit run content_summarizer/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

## 📦 Dependencies

Single source of truth: `requirements.txt` at project root (no duplicate requirements files).
