# 📚 Content Summarizer

AI-powered content summarizer that supports YouTube videos, podcasts, articles, audio/video files, and text using Groq AI.

## Features

- 🎥 **YouTube Videos** - Automatic transcript extraction and summarization
- 🎙️ **Podcasts** - Support for various podcast platforms
- 📄 **Articles** - Web article summarization
- 📎 **File Upload** - Process MP4, MP3, M4A, WAV, MOV, AVI, PDF files
- 📝 **Text Paste** - Direct text input for meeting notes, transcripts, etc.
- 🌙 **Dark Mode** - Toggle between light and dark themes
- 📥 **Export** - Download summaries as Markdown files

## Setup

### Prerequisites

- Python 3.9+
- Groq API key (get one at [groq.com](https://groq.com))

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-directory>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

4. Run the Streamlit app:
```bash
export GROQ_API_KEY="your_key_here"
streamlit run summarizer_ui.py
```

Or with python module:
```bash
export GROQ_API_KEY="your_key_here"
python3 -m streamlit run summarizer_ui.py
```

## Usage

1. Choose your input method:
   - **URL Tab**: Paste YouTube, podcast, or article URLs
   - **Upload File Tab**: Upload audio, video, or PDF files
   - **Paste Text Tab**: Paste transcripts or text content

2. Adjust summary length (50-3000 words)

3. Click "✨ Summarize"

4. Download your summary as Markdown

## Requirements

See `requirements.txt` for full list of dependencies.

## License

MIT
