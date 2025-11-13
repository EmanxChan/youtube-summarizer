# Content Summarizer Documentation

Welcome to the Content Summarizer documentation! This guide helps you install, configure, and use the AI-powered content summarization tool.

---

## 🚀 Quick Start

**New to Content Summarizer?** Start here:
1. [Setup & Installation](./setup/README.md) - Get up and running in 5 minutes
2. [User Guide](./user-guide/STREAMLIT_USAGE_GUIDE.md) - Learn how to use the web UI
3. [Quick Start: Podcasts](./user-guide/QUICK_START_LISTEN_NOTES.md) - Summarize podcasts

---

## 📚 Documentation Sections

### 🛠️ [Setup & Installation](./setup/)
Get Content Summarizer installed and configured on your system.

**Key Documents:**
- [START HERE](./setup/README.md) - Main installation guide
- [Ollama Setup](./setup/OLLAMA_QUICK_GUIDE.md) - Install local AI models
- [Free AI Setup](./setup/FREE_AI_SETUP.md) - Use free AI providers
- [FFmpeg Installation](./setup/FFMPEG_INSTALL.md) - For audio processing
- [DeepSeek Setup](./setup/DEEPSEEK_SETUP.md) - Alternative AI provider

---

### ✨ [Features](./features/)
Learn about all the features and capabilities.

**Key Documents:**
- [Dark Mode](./features/DARK_MODE_ADDED.md) - UI dark mode theming
- [Podcast Support](./features/PODCAST_SUPPORT.md) - Process podcast episodes
- [Search Feature](./features/SEARCH_FEATURE_COMPLETE.md) - Search for content
- [AI Summarization](./features/AI_SUMMARIZATION_README.md) - How AI summaries work
- [YouTube Transcripts](./features/YOUTUBE_TRANSCRIPT_README.md) - Video processing

---

### 📖 [User Guide](./user-guide/)
Step-by-step guides for using Content Summarizer.

**Key Documents:**
- [Streamlit UI Guide](./user-guide/STREAMLIT_USAGE_GUIDE.md) - Using the web interface
- [Quick Start: Listen Notes](./user-guide/QUICK_START_LISTEN_NOTES.md) - Podcast summaries
- [Quick Start: Taddy](./user-guide/QUICK_START_TADDY.md) - Alternative podcast API
- [Listen Notes Usage](./user-guide/LISTEN_NOTES_USAGE_GUIDE.md) - Detailed podcast guide
- [Get Podcast ID](./user-guide/HOW_TO_GET_PODCAST_ID.md) - Find podcast identifiers

---

### 🔌 [API Integration](./api-integration/)
Configure and use external APIs for enhanced functionality.

**Key Documents:**
- [Listen Notes API](./api-integration/LISTEN_NOTES_API_FIX.md) - Setup podcast API
- [Listen Notes Migration](./api-integration/LISTEN_NOTES_MIGRATION.md) - Migration guide
- [Taddy Integration](./api-integration/TADDY_INTEGRATION.md) - Alternative podcast API
- [Taddy vs Alternatives](./api-integration/TADDY_VS_ALTERNATIVES.md) - API comparison
- [API Fixes](./api-integration/TADDY_API_FIXES.md) - Common API issues

---

### 🔧 [Development](./development/)
Information for developers and contributors.

**Key Documents:**
- [Ollama Upgrade](./development/OLLAMA_UPGRADE_SUMMARY.md) - Recent AI model updates
- [Implementation Summary](./development/IMPLEMENTATION_SUMMARY.md) - Architecture overview
- [Deployment Guide](./development/DEPLOYMENT_COMPLETE.md) - Production deployment
- [Data Flow](./development/DATA_FLOW_VISUAL.md) - How data moves through the system
- [Session Summary](./development/SESSION_SUMMARY.md) - Recent development sessions

---

### 🐛 [Troubleshooting](./troubleshooting/)
Solutions to common problems and error messages.

**Key Documents:**
- [Quick Reference](./troubleshooting/FIXES_QUICK_REFERENCE.md) - Common fixes
- [Podcast Fixes](./troubleshooting/PODCAST_FIXES_COMPLETE.md) - Podcast issues
- [Performance Guide](./troubleshooting/PERFORMANCE_OPTIMIZATION.md) - Speed improvements
- [YouTube Fallback](./troubleshooting/YOUTUBE_FALLBACK_FIX.md) - Video transcript issues
- [RSS Matching](./troubleshooting/RSS_EPISODE_MATCHING_FIX.md) - Episode matching problems

---

### 🔄 [Migration](./migration/)
Guides for migrating between different versions or configurations.

**Key Documents:**
- [Migration Checklist](./migration/MIGRATION_CHECKLIST.md) - Version upgrade guide

---

### 📦 [Archive](./archive/)
Deprecated or outdated documentation kept for reference.

---

## 🎯 Common Tasks

### How do I...

**...get started?**
→ [Setup Guide](./setup/README.md)

**...use the web interface?**
→ [Streamlit Usage Guide](./user-guide/STREAMLIT_USAGE_GUIDE.md)

**...summarize a YouTube video?**
→ [Streamlit UI](./user-guide/STREAMLIT_USAGE_GUIDE.md) - Paste the URL and click Summarize

**...summarize a podcast?**
→ [Quick Start: Podcasts](./user-guide/QUICK_START_LISTEN_NOTES.md)

**...fix "API key required" errors?**
→ [Listen Notes API Fix](./api-integration/LISTEN_NOTES_API_FIX.md)

**...install Ollama models?**
→ [Ollama Setup](./setup/OLLAMA_QUICK_GUIDE.md)

**...improve performance?**
→ [Performance Guide](./troubleshooting/PERFORMANCE_OPTIMIZATION.md)

**...enable dark mode?**
→ [Dark Mode Feature](./features/DARK_MODE_ADDED.md)

---

## 🆘 Getting Help

### If You're Stuck:

1. **Check Troubleshooting** → [troubleshooting/](./troubleshooting/)
2. **Review Quick Reference** → [FIXES_QUICK_REFERENCE.md](./troubleshooting/FIXES_QUICK_REFERENCE.md)
3. **Check API Setup** → [api-integration/](./api-integration/)
4. **Review Logs** → `tail -f ~/nohup.out`

### Common Error Messages:

| Error | Solution |
|-------|----------|
| "API key required" | [Listen Notes API Fix](./api-integration/LISTEN_NOTES_API_FIX.md) |
| "Ollama not running" | [Ollama Setup](./setup/OLLAMA_QUICK_GUIDE.md) |
| "No transcript found" | [YouTube Fallback](./troubleshooting/YOUTUBE_FALLBACK_FIX.md) |
| "Podcast not found" | [Podcast Fixes](./troubleshooting/PODCAST_FIXES_COMPLETE.md) |
| "Performance issues" | [Performance Guide](./troubleshooting/PERFORMANCE_OPTIMIZATION.md) |

---

## 📋 Documentation Structure

```
docs/
├── README.md (you are here)
├── setup/                    # Installation & configuration
├── features/                 # Feature documentation
├── user-guide/              # How-to guides & usage
├── api-integration/         # API & integration docs
├── development/             # Development & updates
├── troubleshooting/         # Fixes & debugging
├── migration/               # Migration guides
└── archive/                 # Deprecated docs
```

---

## 🔄 Recently Updated

- **Nov 12, 2025** - Documentation reorganized into structured folders
- **Nov 10, 2025** - Ollama models upgraded (Llama 3.1, Qwen 2.5)
- **Nov 10, 2025** - Enhanced key insights with deeper conceptual analysis
- **Nov 10, 2025** - Dark mode added to Streamlit UI
- **Nov 10, 2025** - Listen Notes API key configuration fixed

---

## 🤝 Contributing

Found an error or want to improve the docs?

1. Check [Development Guide](./development/IMPLEMENTATION_SUMMARY.md)
2. Review [Data Flow](./development/DATA_FLOW_VISUAL.md)
3. Make your changes
4. Document your updates

---

## 📝 Document Index

### By Topic:

**AI Models:**
- [Ollama Setup](./setup/OLLAMA_QUICK_GUIDE.md)
- [Free AI Setup](./setup/FREE_AI_SETUP.md)
- [DeepSeek Setup](./setup/DEEPSEEK_SETUP.md)
- [AI Summarization](./features/AI_SUMMARIZATION_README.md)
- [Ollama Upgrade](./development/OLLAMA_UPGRADE_SUMMARY.md)

**Podcasts:**
- [Podcast Support](./features/PODCAST_SUPPORT.md)
- [Quick Start: Listen Notes](./user-guide/QUICK_START_LISTEN_NOTES.md)
- [Quick Start: Taddy](./user-guide/QUICK_START_TADDY.md)
- [Listen Notes API](./api-integration/LISTEN_NOTES_API_FIX.md)
- [Podcast Fixes](./troubleshooting/PODCAST_FIXES_COMPLETE.md)

**YouTube:**
- [YouTube Transcripts](./features/YOUTUBE_TRANSCRIPT_README.md)
- [YouTube Fallback](./troubleshooting/YOUTUBE_FALLBACK_FIX.md)

**UI & Features:**
- [Streamlit Guide](./user-guide/STREAMLIT_USAGE_GUIDE.md)
- [Dark Mode](./features/DARK_MODE_ADDED.md)
- [Search Feature](./features/SEARCH_FEATURE_COMPLETE.md)

**Performance:**
- [Performance Optimization](./troubleshooting/PERFORMANCE_OPTIMIZATION.md)
- [Performance Improvements](./troubleshooting/PERFORMANCE_IMPROVEMENTS_COMPLETE.md)

---

## 🎓 Learning Path

### Beginner Path:
1. [Setup Guide](./setup/README.md) - Install everything
2. [Streamlit Guide](./user-guide/STREAMLIT_USAGE_GUIDE.md) - Learn the UI
3. [Quick Start: Podcasts](./user-guide/QUICK_START_LISTEN_NOTES.md) - Try a podcast

### Advanced Path:
1. [Data Flow](./development/DATA_FLOW_VISUAL.md) - Understand the architecture
2. [API Integration](./api-integration/) - Configure external APIs
3. [Performance](./troubleshooting/PERFORMANCE_OPTIMIZATION.md) - Optimize your setup

### Power User Path:
1. [All Features](./features/) - Learn every feature
2. [Development Guide](./development/IMPLEMENTATION_SUMMARY.md) - Deep dive
3. [Troubleshooting](./troubleshooting/FIXES_QUICK_REFERENCE.md) - Master debugging

---

**Ready to get started?** → [Setup Guide](./setup/README.md)

**Questions?** → [Troubleshooting](./troubleshooting/)

**Want to contribute?** → [Development](./development/)
