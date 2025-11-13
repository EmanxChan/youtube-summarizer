# Listen Notes Migration Complete

## Overview

Successfully migrated from Taddy API to Listen Notes API for podcast metadata retrieval. The system now uses:
- **Listen Notes API**: Podcast metadata + audio URLs
- **Local Whisper (base model)**: Free audio transcription

## What Changed

### 1. New Client: `listen_notes_client.py`
- REST API client for Listen Notes
- Supports Apple Podcasts, Spotify, and RSS URLs
- Returns podcast metadata including `audio_url` for Whisper transcription
- Includes caching support and quota tracking

### 2. Cache Renamed: `podcast_cache.py`
- Previously `taddy_cache.py`
- Now provider-agnostic with configurable provider names
- Supports both Listen Notes and legacy data

### 3. Updated: `youtube_slash_command.py`
- Replaced `TaddyClient` with `ListenNotesClient`
- Replaced `TaddyCache` with `PodcastCache`
- Updated metrics tracking from `taddy_api` to `listen_notes_api`
- Listen Notes provides `audio_url` → feeds directly to Whisper
- Whisper uses `base` model with CPU/int8 for optimal performance

### 4. Updated: `transcript_metrics.py`
- Changed source labels to `listen_notes_api` and `listen_notes_api_cached`
- Maintains backward compatibility with existing metrics

### 5. Updated Scripts:
- `restart_streamlit.sh`: Now exports `LISTEN_NOTES_API_KEY` instead of Taddy credentials
- `test_streamlit_env.py`: Tests Listen Notes client and credentials
- `test_listen_notes_example.py`: New comprehensive test script

## Setup Instructions

### 1. Get Listen Notes API Key
1. Sign up at https://www.listennotes.com/api/
2. Get your API key from the dashboard
3. Free tier includes sufficient quota for testing

### 2. Set Environment Variable
```bash
export LISTEN_NOTES_API_KEY="your_api_key_here"
```

Or add to your `~/.zshrc` or `~/.bashrc`:
```bash
echo 'export LISTEN_NOTES_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Update restart_streamlit.sh
Edit `/Users/e.chan/restart_streamlit.sh` and replace `YOUR_LISTEN_NOTES_API_KEY_HERE` with your actual API key.

## Testing

### Test Listen Notes Client
```bash
python3 test_listen_notes_example.py
```

This will test:
- ✓ Client initialization
- ✓ Podcast search
- ✓ Episode lookup
- ✓ URL parsing (Apple Podcasts, Spotify)
- ✓ Cache functionality
- ✓ API quota tracking

### Test Streamlit Integration
```bash
streamlit run test_streamlit_env.py
```

Visit http://localhost:8501 to:
- Check environment variables
- Test client initialization
- Run sample searches

### Test Full Flow
Test with a podcast URL:
```bash
python3 youtube_slash_command.py "https://podcasts.apple.com/us/podcast/the-daily/id1200361736"
```

## New Workflow

```
User provides podcast URL
    ↓
[1] Listen Notes API (1-3 sec)
    ├─ Returns: title, description, audio_url, duration
    ├─ Cached for 30 days
    └─ Falls back to RSS if needed
    ↓
[2] Check RSS for existing transcript (instant)
    ↓
[3] Try webpage + YouTube mirror (parallel, 10-15 sec)
    ↓
[4] Whisper Transcription with audio_url
    ├─ Downloads audio from Listen Notes audio_url (or RSS)
    ├─ Uses faster-whisper with base model
    ├─ CPU + int8 for optimal performance
    ├─ Gist mode for episodes > 60 minutes (first 10 min)
    └─ Full mode for episodes < 60 minutes
    ↓
AI Summarization (Ollama mistral:instruct)
    ↓
Output with source badge + metrics
```

## Performance Improvements

### Whisper Base Model
- **Model**: `base` (faster-whisper)
- **Device**: CPU with int8 quantization
- **Speed**: ~3-5x faster than small/medium models
- **Quality**: Sufficient for podcast transcription
- **Resource usage**: Lower memory footprint

### Intelligent Mode Selection
- **Full mode**: Episodes < 60 minutes → complete transcription
- **Gist mode**: Episodes > 60 minutes → first 10 minutes only
- Automatic mode switching based on duration

### Caching Strategy
- Listen Notes metadata: 30-day cache
- Whisper transcripts: Permanent cache (keyed by audio URL)
- Metrics tracking for optimization

## Cost Analysis

| Service | Taddy (Old) | Listen Notes (New) |
|---------|-------------|---------------------|
| Metadata | Free tier (no transcripts) | Free tier |
| Transcripts | $49/month (Pro required) | $0 (Local Whisper) |
| Audio URLs | Not provided | ✓ Provided |
| Total Cost | $49/month or $0 (no transcripts) | $0/month |

**Result**: 100% free system with full transcription capability!

## Files Modified

### Created:
- `listen_notes_client.py` - Listen Notes API client
- `podcast_cache.py` - Provider-agnostic cache (renamed from taddy_cache.py)
- `test_listen_notes_example.py` - Comprehensive test script
- `LISTEN_NOTES_MIGRATION.md` - This documentation

### Modified:
- `youtube_slash_command.py` - Replaced Taddy with Listen Notes
- `transcript_metrics.py` - Updated metric labels
- `restart_streamlit.sh` - Updated environment variables
- `test_streamlit_env.py` - Updated for Listen Notes testing

### Deprecated (Keep for Reference):
- `taddy_integration.py` - Original Taddy client
- `taddy_cache.py` - Original cache (replaced by podcast_cache.py)
- `test_taddy_example.py` - Taddy test script

## Troubleshooting

### "LISTEN_NOTES_API_KEY not set"
```bash
export LISTEN_NOTES_API_KEY="your_key_here"
```

### "No audio URL found"
- Check if podcast is available on Listen Notes
- Verify URL format is correct
- Try RSS fallback method

### Whisper transcription slow
- Already using base model (optimal for speed)
- Gist mode activates automatically for long episodes
- Consider GPU if available (modify device="cpu" to device="cuda")

### Cache issues
Clear cache:
```python
from podcast_cache import PodcastCache
cache = PodcastCache(provider='listen_notes')
cache.clear_all()
```

## API Quota Management

Listen Notes free tier:
- Monitor usage with metrics
- Cache is automatic (30-day TTL)
- Quota resets monthly

Check quota:
```python
from listen_notes_client import ListenNotesClient
client = ListenNotesClient()
metrics = client.get_metrics()
print(f"Quota remaining: {metrics['quota_remaining']}")
```

## Next Steps

1. ✅ Migration complete
2. ✅ All components updated
3. 🔄 Testing with real podcast URLs
4. 📊 Monitor metrics and performance
5. 🎯 Optimize based on usage patterns

## Support

For issues or questions:
1. Check this documentation first
2. Review error messages in metrics
3. Test with `test_listen_notes_example.py`
4. Verify environment variables are set correctly

## Success Metrics

Track with `--show-metrics` flag:
```bash
python3 youtube_slash_command.py "podcast_url" --show-metrics
```

Metrics include:
- `listen_notes_api`: API calls
- `listen_notes_api_cached`: Cache hits
- `whisper`: Transcription attempts
- Success rates and average durations
