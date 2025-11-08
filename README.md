# 📚 Content Summarizer

AI-powered summarization tool for YouTube videos, podcasts, and web articles. Get intelligent summaries with key insights and actionable takeaways.

## ✨ Features

- **YouTube Videos**: Automatic transcript extraction + AI summarization
- **Podcasts**: Support for Apple Podcasts, Spotify, RSS feeds, and **search by name**
- **Web Articles**: Extract and summarize article content
- **AI-Powered**: Uses Ollama (local, free) or OpenAI for intelligent summaries
- **Web UI**: Beautiful Streamlit interface for easy use
- **CLI**: Command-line interface for automation
- **Search**: Find podcast episodes by name + topic (e.g., "Huberman Lab - sleep")

## 🚀 Quick Start

### 1. Installation

```bash
# Install Python dependencies
cd ~/content-summarizer
pip3 install -r config/requirements.txt
pip3 install -r config/requirements_ai.txt

# Install Ollama (for free local AI)
./scripts/install_ollama_mac.sh

# Setup AI models
./scripts/setup_ai.sh
```

### 2. Configuration

```bash
# Copy environment template
cp config/.env.example config/.env

# Edit with your Listen Notes API key (free tier: 300/month)
# Get key at: https://www.listennotes.com/api/
nano config/.env
```

### 3. Run the Web UI

```bash
./scripts/restart_streamlit.sh
# Visit: http://localhost:8501
```

### 4. Or Use Command Line

```bash
# YouTube video
./bin/youtube "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --words 200

# Podcast search (NEW!)
./bin/youtube "Huberman Lab - sleep" --words 150

# Podcast URL
./bin/youtube "https://podcasts.apple.com/us/podcast/..." --words 150

# Article
./bin/youtube "https://example.com/article" --words 300
```

## 📖 Documentation

### For Users
- **[Start Here](docs/user-guide/START_HERE.md)** - Complete getting started guide
- **[Streamlit Usage](docs/user-guide/STREAMLIT_USAGE_GUIDE.md)** - How to use the web UI
- **[Search Feature](docs/user-guide/NEW_SEARCH_FEATURE_GUIDE.md)** - Find podcasts by name + topic
- **[Podcast IDs](docs/user-guide/HOW_TO_GET_PODCAST_ID.md)** - How to find podcast IDs

### Setup & Installation
- **[Free AI Setup](docs/setup/FREE_AI_SETUP.md)** - Install Ollama for free AI
- **[Ollama Guide](docs/setup/OLLAMA_QUICK_GUIDE.md)** - Quick Ollama reference
- **[DeepSeek Setup](docs/setup/DEEPSEEK_SETUP.md)** - Alternative AI model
- **[FFmpeg Install](docs/setup/FFMPEG_INSTALL.md)** - Audio processing setup
- **[Slash Command](docs/setup/SETUP_SLASH_COMMAND.md)** - CLI setup

### Features
- **[AI Summarization](docs/features/AI_SUMMARIZATION_README.md)** - How AI summaries work
- **[Podcast Support](docs/features/PODCAST_SUPPORT.md)** - Podcast features overview
- **[YouTube Transcripts](docs/features/YOUTUBE_TRANSCRIPT_README.md)** - YouTube integration
- **[Listen Notes](docs/features/LISTEN_NOTES_USAGE_GUIDE.md)** - Podcast API guide
- **[Listen Notes Quick Ref](docs/features/LISTEN_NOTES_QUICK_REF.md)** - Quick reference

### Troubleshooting
- **[Bug Fix Summary](docs/troubleshooting/BUG_FIX_SUMMARY.md)** - Common issues & solutions
- **[Quick Reference](docs/troubleshooting/FIXES_QUICK_REFERENCE.md)** - Quick fixes
- **[RSS Episode Matching](docs/troubleshooting/RSS_EPISODE_MATCHING_FIX.md)** - Podcast episode issues
- **[YouTube Fallback](docs/troubleshooting/YOUTUBE_FALLBACK_FIX.md)** - YouTube transcript issues

## 🎯 Usage Examples

### Web UI (Streamlit)

1. **Open**: http://localhost:8501
2. **Enter URL or Search**: 
   - YouTube: `https://www.youtube.com/watch?v=...`
   - Podcast Search: `Huberman Lab - sleep`
   - Podcast URL: `https://podcasts.apple.com/...`
   - Article: `https://example.com/article`
3. **Set Word Count**: Choose summary length (50-3000 words)
4. **Click "Summarize"**
5. **Get Results**: AI summary + 5 key insights + 3 next steps

### Command Line

```bash
# YouTube video by URL
./bin/youtube "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --format md --words 200

# YouTube video by ID
./bin/youtube "dQw4w9WgXcQ" --format md --words 200

# YouTube search query
./bin/youtube "Python tutorial for beginners" --format md --words 300

# Podcast search (NEW!)
./bin/youtube "Huberman Lab latest" --format md --words 150
./bin/youtube "The Daily: Trump" --format md --words 150
./bin/youtube "How I Built This - Airbnb" --format md --words 200

# Podcast by URL
./bin/youtube "https://podcasts.apple.com/us/podcast/..." --format md --words 150

# Article URL
./bin/youtube "https://nytimes.com/article" --format md --words 250
```

## 📁 Project Structure

```
content-summarizer/
├── src/                    # Core application code
│   ├── youtube_slash_command.py    # Main CLI (99KB)
│   ├── summarizer_ui.py            # Streamlit web UI
│   ├── ai_summarizer.py            # AI integration
│   ├── listen_notes_client.py      # Listen Notes API
│   ├── podcast_cache.py            # Podcast caching
│   ├── transcript_metrics.py       # Metrics tracking
│   └── extractors/                 # Content extractors
│       ├── enhanced_extractor.py
│       ├── ytdlp_transcript_extractor.py
│       ├── working_transcript_fetcher.py
│       └── video_validator.py
├── docs/                   # Documentation
│   ├── user-guide/         # End-user guides
│   ├── setup/              # Installation guides
│   ├── features/           # Feature documentation
│   ├── troubleshooting/    # Bug fixes & solutions
│   ├── development/        # Dev logs & technical docs
│   └── migration/          # Migration guides
├── scripts/                # Utility scripts
├── tests/                  # Test files
├── legacy/                 # Deprecated code (preserved)
├── config/                 # Configuration files
├── data/                   # Runtime data (NLTK)
├── bin/                    # Executables (ffmpeg, youtube command)
└── output/                 # Generated summaries
```

## 🎨 Features in Detail

### 1. YouTube Videos
- Automatic transcript extraction
- Fallback to multiple transcript sources
- Support for auto-generated captions
- Video metadata extraction
- Quality assessment (music videos, short content, etc.)

### 2. Podcast Search (NEW!)
- **Search by name + topic**: `"Huberman Lab - sleep"`
- **Get latest episode**: `"The Daily latest"`
- **Natural language**: `"Huberman Lab episode about exercise"`
- Uses Listen Notes API (300 free requests/month)
- Fast episode discovery
- No URL needed!

### 3. Podcast URLs
- Apple Podcasts support
- Spotify podcast support
- RSS feed support
- Episode metadata extraction
- Audio transcription with Whisper
- Description fallback if audio unavailable

### 4. Web Articles
- Clean HTML extraction
- Smart content detection
- Quality assessment
- Metadata extraction

### 5. AI Summarization
- **Free**: Ollama (local, unlimited)
- **Paid**: OpenAI (optional)
- Multiple model support (Mistral, Llama, DeepSeek, etc.)
- Configurable summary length
- 5 key insights extraction
- 3 actionable next steps
- Quality warnings

## 💰 Costs

### Free Tier
- **Ollama**: 100% free, unlimited local AI
- **YouTube**: Free (uses public API)
- **Listen Notes**: 300 requests/month (free tier)
- **Articles**: Free (web scraping)

### Paid Options
- **OpenAI**: $0.002/request (optional alternative to Ollama)
- **Listen Notes Pro**: More requests if needed

**Total Cost**: $0/month for typical use! 🎉

## 🛠️ Technical Details

### Dependencies
- Python 3.9+
- Streamlit (web UI)
- Ollama (local AI) or OpenAI
- youtube-transcript-api (YouTube)
- Listen Notes API (podcasts)
- BeautifulSoup4 (articles)
- NLTK (text processing)
- FFmpeg (audio processing)

### Performance
- YouTube summaries: 10-30 seconds
- Podcast search: 3-5 seconds
- Podcast transcription: 1-5 minutes (depending on length)
- Article summaries: 5-15 seconds

### Storage
- Transcripts cached locally
- Podcast episodes cached
- Summaries saved as Markdown files
- Output: `~/Documents/YouTube videos/`

## 🔧 Advanced Usage

### Custom Output Directory
```bash
export OUTPUT_DIR="/path/to/summaries"
./bin/youtube "URL" --words 200
```

### Different AI Models
```bash
# Use different Ollama model
export OLLAMA_MODEL="llama3:8b"
./bin/youtube "URL" --words 200

# List available models
ollama list
```

### Batch Processing
```bash
# Process multiple URLs
cat urls.txt | while read url; do
  ./bin/youtube "$url" --words 200
done
```

## 📊 Output Format

Each summary includes:
1. **Metadata**: Title, source, date, duration
2. **AI Summary**: Concise overview (customizable length)
3. **Key Insights**: 5 most important points
4. **Next Steps**: 3 actionable recommendations
5. **Statistics**: Word count, reduction percentage

Example output:
```markdown
# Title of Content

**Source**: YouTube/Podcast/Article
**Published**: 2024-11-07
**Duration**: 45 minutes

## Summary
[AI-generated summary here...]

## Key Insights
1. 🎯 [First key insight]
2. 💡 [Second key insight]
3. 🚀 [Third key insight]
4. 🔧 [Fourth key insight]
5. ✨ [Fifth key insight]

## Next Steps
1. [First action item]
2. [Second action item]
3. [Third action item]

## Statistics
- Original: 10,000 words
- Summary: 200 words
- Reduction: 98%
```

## 🤝 Contributing

This is a personal project, but suggestions are welcome! Feel free to:
- Report bugs
- Suggest features
- Share feedback

## 📝 License

Personal use project. All rights reserved.

## 🆘 Support

- **Start Here**: [docs/user-guide/START_HERE.md](docs/user-guide/START_HERE.md)
- **Troubleshooting**: [docs/troubleshooting/](docs/troubleshooting/)
- **Bug Fixes**: [docs/troubleshooting/FIXES_QUICK_REFERENCE.md](docs/troubleshooting/FIXES_QUICK_REFERENCE.md)

## 🎉 What's New

### Latest Features
- ✨ **Podcast Search**: Find episodes by podcast name + topic
- 🚀 **Natural Language**: Use queries like "Huberman Lab latest"
- 📊 **Listen Notes Integration**: 300 free podcast searches/month
- 🎯 **Improved Organization**: Clean project structure
- 📝 **Better Documentation**: Organized docs by purpose

## 🙏 Credits

Built with:
- [Ollama](https://ollama.ai/) - Free local AI
- [Streamlit](https://streamlit.io/) - Web UI framework
- [Listen Notes](https://www.listennotes.com/api/) - Podcast API
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api) - YouTube transcripts
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing

---

**Made with ❤️ for efficient content consumption**
