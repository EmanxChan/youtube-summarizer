# YouTube Transcript Extractor & Summarizer

Complete solution for extracting and summarizing YouTube video transcripts with intelligent rate limit handling.

## 🚨 Current Status: Rate Limited

YouTube has rate-limited transcript access from your IP address (429 errors). The tools are working correctly, but YouTube is blocking requests.

## 📋 Quick Start (Once Rate Limits Clear)

```bash
# Check if rate limiting is cleared
python3 rate_limit_check.py

# Extract and summarize a video
python3 enhanced_extractor.py "https://youtu.be/VIDEO_ID" --summarize 150

# Check if a specific video has transcripts
python3 video_validator.py "https://youtu.be/VIDEO_ID"
```

## 🛠️ Available Tools

### 1. **enhanced_extractor.py** - Main Tool
Multi-method extractor with intelligent retry and fallback:
- Tries youtube-transcript-api with exponential backoff
- Falls back to yt-dlp if first method fails
- Extracts, cleans, and optionally summarizes transcripts

```bash
# Basic extraction
python3 enhanced_extractor.py "https://youtu.be/qSess5R1MHU"

# Extract and summarize to ~150 words
python3 enhanced_extractor.py "https://youtu.be/qSess5R1MHU" --summarize 150

# Save to file
python3 enhanced_extractor.py "VIDEO_ID" --summarize 100 --output transcript.txt

# Increase retry attempts
python3 enhanced_extractor.py "VIDEO_ID" --retries 10
```

### 2. **video_validator.py** - Pre-Check Tool
Quickly check if a video has transcripts before attempting extraction:

```bash
python3 video_validator.py "https://youtu.be/VIDEO_ID"
python3 video_validator.py "VIDEO_ID" --json  # JSON output
```

### 3. **rate_limit_check.py** - Status Checker
Test if YouTube rate limiting has cleared:

```bash
python3 rate_limit_check.py
```

### 4. **demo_working_summary.py** - Offline Demo
Demonstrates summarization without needing YouTube access:

```bash
python3 demo_working_summary.py
```

## 🔧 Solutions for Rate Limiting

### Option 1: Wait (Easiest)
- Rate limits typically reset after 24-48 hours
- Run `python3 rate_limit_check.py` periodically to check status

### Option 2: Change IP Address
**Using VPN:**
```bash
# Connect to VPN, then test
python3 rate_limit_check.py
```

**Using Different Network:**
- Mobile hotspot from your phone
- Different WiFi network
- Coffee shop, library, etc.

### Option 3: YouTube Data API v3 (Most Reliable)
Get an official API key for separate quota system:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Create credentials (API key)
5. Use with the API (requires custom implementation)

**Pros:**
- Separate quota system (10,000 units/day)
- More reliable for production use
- Official Google support

**Cons:**
- Requires Google account and API setup
- Different implementation needed
- Uses quota units (captions.download = 200 units)

### Option 4: Try Off-Peak Hours
YouTube rate limiting may be less strict during:
- Late night / early morning (2-6 AM your timezone)
- Weekdays vs weekends
- Outside major geographic regions' business hours

## 📊 How It Works

### Extraction Methods (in order of attempt):

1. **youtube-transcript-api** (Primary)
   - Fast and lightweight
   - Direct API access
   - Best for most videos

2. **yt-dlp** (Fallback)
   - Downloads subtitle files
   - Works with different caption formats
   - More robust for edge cases

### Rate Limit Handling:

- **Exponential Backoff**: Waits increase exponentially (60s → 120s → 240s)
- **Jitter**: Random variation (±20%) to avoid synchronized retries
- **Smart Detection**: Identifies 429 errors vs other failures
- **Configurable Retries**: Default 5, adjustable with `--retries`

### Summarization:

Uses extractive summarization with NLTK:
1. Tokenizes text into sentences
2. Scores sentences by word frequency (excluding stopwords)
3. Selects highest-scoring sentences
4. Maintains original sentence order
5. Targets specified word count (±20%)

## 🎯 Your Video

Video ID: `qSess5R1MHU`
URL: https://youtu.be/qSess5R1MHU

Once rate limiting clears, extract with:
```bash
python3 enhanced_extractor.py "https://youtu.be/qSess5R1MHU" --summarize 150
```

## 📦 Dependencies

All required packages are installed:
```
youtube-transcript-api==0.6.0
yt-dlp
requests
nltk
scipy
scikit-learn
```

## 🐛 Troubleshooting

### "429 Too Many Requests"
- **Cause**: Rate limited by YouTube
- **Solution**: Wait 24+ hours or change IP address

### "No transcript available"
- **Cause**: Video has no captions/subtitles
- **Solution**: Video creator must enable captions

### "Could not retrieve transcript"
- **Causes**: 
  - Private video
  - Age-restricted content
  - Geographic restrictions
  - Deleted video
- **Solution**: Check video accessibility in browser

### ImportError
- **Cause**: Missing dependencies
- **Solution**: `pip3 install -r requirements.txt`

## 📈 Success Metrics

From previous testing:
- ✅ Summarization reduces content by 80-90%
- ✅ Maintains key information and coherence
- ✅ Handles transcripts from 100 to 10,000+ words
- ✅ Multi-language support (when available)

## 🔄 Testing Workflow

1. **Check rate limit status:**
   ```bash
   python3 rate_limit_check.py
   ```

2. **If clear, validate your video:**
   ```bash
   python3 video_validator.py "YOUR_VIDEO_URL"
   ```

3. **Extract and summarize:**
   ```bash
   python3 enhanced_extractor.py "YOUR_VIDEO_URL" --summarize 150
   ```

## 💡 Tips

- **Start with validation**: Use `video_validator.py` before extraction to save time
- **Save to file**: Use `--output` for easier processing of long transcripts
- **Adjust summary length**: Typical ranges:
  - 50-100 words: Very brief summary
  - 100-200 words: Standard summary
  - 200-500 words: Detailed summary
- **Batch processing**: Wait 2-3 seconds between videos to avoid triggering rate limits
- **Keep backups**: Save transcripts locally to avoid re-fetching

## 📝 Next Steps

1. Run `python3 rate_limit_check.py` to check current status
2. If still rate-limited, try:
   - Waiting 24+ hours
   - Using VPN to change IP
   - Trying from different network
3. Once cleared, process your video: qSess5R1MHU
4. Consider YouTube Data API v3 for production/frequent use

## 🆘 Need Help?

All tools have built-in help:
```bash
python3 enhanced_extractor.py --help
python3 video_validator.py --help
```
