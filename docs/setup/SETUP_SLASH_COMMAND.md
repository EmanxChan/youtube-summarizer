# Setup /youtube Command

Quick guide to set up the `/youtube` slash command for easy transcript extraction.

## 🚀 Quick Setup (Automatic)

Run the setup script:
```bash
bash setup_youtube_command.sh
```

Then activate the alias:
```bash
source ~/.zshrc  # for zsh (default on macOS)
# or
source ~/.bashrc  # for bash
```

Done! You can now use `/youtube` directly.

## 📝 Manual Setup (Alternative)

If you prefer manual setup, add this to your shell config (`~/.zshrc` or `~/.bashrc`):

```bash
# YouTube transcript extractor
alias /youtube='/Users/e.chan/youtube'
```

Then reload your config:
```bash
source ~/.zshrc  # or ~/.bashrc
```

## 💡 Usage

Once set up, use it like this:

### Extract and view summary (default 150 words):
```bash
/youtube "https://youtu.be/VIDEO_ID"
```

### Extract with custom word count:
```bash
/youtube "https://youtu.be/VIDEO_ID" --words 200
```

### Search and extract:
```bash
/youtube "Python programming tutorial"
```

### Get help:
```bash
/youtube --help
```

## 📁 Output Location

Files are saved to: `~/Documents/YouTube videos/`

Two files are created for each video:
- `video-title.transcript.txt` - Full transcript
- `video-title.summary.txt` - Summarized version

## 🔍 Features

- **Multi-method extraction**: Tries youtube-transcript-api → yt-dlp
- **Intelligent retry**: Automatically retries on rate limits with backoff
- **Smart summarization**: Uses NLTK for extractive summarization
- **Search support**: Can search YouTube and extract from results
- **Clean output**: Removes timestamps and caption artifacts

## 🚨 Rate Limiting

If you see "429 Too Many Requests" errors:

1. **Wait**: Rate limits typically clear after 24-48 hours
2. **Check status**: `python3 rate_limit_check.py`
3. **Use VPN**: Change your IP address
4. **Different network**: Try mobile hotspot or different WiFi

## 🧪 Test It

Check if rate limiting has cleared:
```bash
python3 rate_limit_check.py
```

If clear, test with your video:
```bash
/youtube "https://youtu.be/qSess5R1MHU" --words 150
```

## 🛠️ Advanced Usage

The underlying tools can still be used directly:

### Enhanced extractor (full control):
```bash
python3 enhanced_extractor.py "VIDEO_URL" --summarize 150 --retries 10
```

### Validate video first:
```bash
python3 video_validator.py "VIDEO_URL"
```

### Direct slash command system:
```bash
python3 droid_slash_cli.py /youtube "VIDEO_URL" --words 200
```

## 📊 Example Output

```
Processing: https://youtu.be/VIDEO_ID

Video ID: VIDEO_ID
Fetching transcript...
✓ Transcript fetched (2547 characters, 456 words)
Generating summary (target: 150 words)...
✓ Summary generated (148 words)
✓ Transcript saved: ~/Documents/YouTube videos/video-title.transcript.txt
✓ Summary saved: ~/Documents/YouTube videos/video-title.summary.txt

===========================================================================
SUMMARY
===========================================================================
[Your summarized content here...]
===========================================================================

Statistics:
  Original: 456 words
  Summary: 148 words
  Reduction: 67.5%
```

## 🆘 Troubleshooting

### Alias not working
```bash
# Check if alias exists
alias | grep youtube

# Reload shell config
source ~/.zshrc
```

### Command not found
```bash
# Verify script exists and is executable
ls -la ~/youtube
chmod +x ~/youtube
```

### Permission denied
```bash
chmod +x /Users/e.chan/youtube
chmod +x /Users/e.chan/setup_youtube_command.sh
```

### Python module errors
```bash
pip3 install -r requirements.txt
```

## 🎯 Your Video

Once rate limits clear, extract your video:
```bash
/youtube "https://youtu.be/qSess5R1MHU" --words 150
```

Happy transcript extracting! 🎬
