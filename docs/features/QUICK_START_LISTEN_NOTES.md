# Quick Start: Listen Notes Integration

## ✅ Migration Complete!

The system has been successfully migrated from Taddy API to Listen Notes API.

## 🚀 Quick Setup (3 Steps)

### Step 1: Set Your API Key
```bash
export LISTEN_NOTES_API_KEY="your_listen_notes_api_key_here"
```

**Don't have an API key?**
1. Visit https://www.listennotes.com/api/
2. Sign up for free account
3. Copy your API key from dashboard

### Step 2: Test the Integration
```bash
python3 test_listen_notes_example.py
```

This will verify:
- ✓ API key is set correctly
- ✓ Client can connect
- ✓ Search functionality works
- ✓ Cache is functioning

### Step 3: Try a Podcast!
```bash
python3 youtube_slash_command.py "https://podcasts.apple.com/us/podcast/the-daily/id1200361736"
```

## 🎯 What's New?

### Before (Taddy):
- Required Taddy User ID + API Key
- Free tier blocked transcripts
- Pro tier: $49/month for transcripts
- Limited podcast database

### After (Listen Notes):
- Single API key (simpler!)
- Free tier provides audio URLs
- Local Whisper transcription (100% free!)
- Larger podcast database

## 📊 Complete System Flow

```
Podcast URL → Listen Notes API → Get audio_url
                    ↓
          Download audio file
                    ↓
     Whisper (base model) → Transcription
                    ↓
        Ollama AI → Summary
```

**Total Cost: $0/month** 🎉

## 🔧 Configuration Options

### Use Smaller Whisper Model (Already Set!)
The system uses `base` model by default:
- Fast transcription (~3-5x faster than larger models)
- Good accuracy for podcasts
- Low resource usage

### Gist Mode for Long Episodes
Automatic for episodes > 60 minutes:
- Transcribes first 10 minutes only
- Perfect for getting the main idea
- Can be adjusted in `youtube_slash_command.py`

## 📁 New Files Created

1. **`listen_notes_client.py`** - Main API client
2. **`podcast_cache.py`** - Smart caching (30-day TTL)
3. **`test_listen_notes_example.py`** - Test script
4. **`LISTEN_NOTES_MIGRATION.md`** - Full documentation
5. **`QUICK_START_LISTEN_NOTES.md`** - This file!

## 🎪 Example Commands

### Test with Apple Podcasts URL:
```bash
python3 youtube_slash_command.py "https://podcasts.apple.com/us/podcast/the-daily/id1200361736"
```

### Test with Spotify URL:
```bash
python3 youtube_slash_command.py "https://open.spotify.com/show/7Fht7tyxuZ4BrqHF9xc6vu"
```

### Show metrics after processing:
```bash
python3 youtube_slash_command.py "podcast_url" --show-metrics
```

## 🐛 Troubleshooting

### Issue: "LISTEN_NOTES_API_KEY not set"
**Solution:**
```bash
export LISTEN_NOTES_API_KEY="your_key_here"
```

To make it permanent, add to `~/.zshrc`:
```bash
echo 'export LISTEN_NOTES_API_KEY="your_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### Issue: "No audio URL found"
**Possible causes:**
1. Podcast not in Listen Notes database
2. Episode-specific URLs not supported (try podcast homepage instead)
3. API quota exceeded

**Solution:**
- System will automatically fall back to RSS feed extraction
- Check API quota with test script

### Issue: Whisper transcription slow
**Current setup (already optimized):**
- Using `base` model (fastest reasonable model)
- CPU with int8 quantization
- Gist mode for long episodes

**To speed up further:**
- Use GPU if available (requires CUDA setup)
- Reduce gist mode duration limit

## 💾 Cache Management

Caches are stored in: `~/.cache/podcast_transcripts/`

**View cache stats:**
```python
from podcast_cache import PodcastCache
cache = PodcastCache(provider='listen_notes')
print(cache.get_stats())
```

**Clear cache:**
```python
cache.clear_all()
```

## 📈 Monitor Usage

Track API usage and success rates:
```bash
python3 youtube_slash_command.py "podcast_url" --show-metrics
```

Metrics tracked:
- `listen_notes_api`: Fresh API calls
- `listen_notes_api_cached`: Cache hits
- `whisper`: Transcription attempts
- Success rates and timings

## 🎓 Key Benefits

✅ **100% Free**: No subscription required  
✅ **Faster Setup**: Single API key vs multiple credentials  
✅ **Larger Database**: More podcasts available  
✅ **Full Transcripts**: Whisper provides complete transcription  
✅ **Smart Caching**: 30-day cache reduces API calls  
✅ **Offline Capable**: Cached podcasts work without internet  

## 🔄 Compatibility Note

Old Taddy files are preserved for reference:
- `taddy_integration.py` - Can be removed after testing
- `taddy_cache.py` - Replaced by `podcast_cache.py`
- `test_taddy_example.py` - No longer needed

Existing cached data is safe - uses different cache directories.

## ✨ Ready to Use!

Once you set `LISTEN_NOTES_API_KEY`, the system is ready to process podcasts!

```bash
export LISTEN_NOTES_API_KEY="your_key"
python3 test_listen_notes_example.py  # Test it
python3 youtube_slash_command.py "podcast_url"  # Use it!
```

---

**Need help?** See `LISTEN_NOTES_MIGRATION.md` for detailed documentation.
