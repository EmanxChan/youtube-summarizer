# Listen Notes API - Quick Reference

## What Works on Free Tier ✅

### 1. Search by Name
```python
results = client.search_podcast("Huberman Lab")
# Returns: Podcast ID, title, publisher, episode count
```
**Cost**: FREE ✅  
**Quota Impact**: 1 request  
**Use Case**: Find podcast by name

---

### 2. Get Episodes by ID
```python
episodes = client.get_podcast_episodes(podcast_id, limit=10)
# Returns: Audio URLs, titles, descriptions
```
**Cost**: FREE ✅  
**Quota Impact**: 1 request  
**Use Case**: Get recent episodes with audio URLs

---

## What Doesn't Work on Free Tier ❌

### 1. Direct URL Lookup
```python
result = client.get_episode_by_url("https://podcasts.apple.com/...")
# Returns: 405 Error - Not Allowed
```
**Cost**: Requires PAID plan ❌  
**Why**: `just_listen` endpoint is premium feature

---

## Comparison: Listen Notes vs RSS

| Feature | Listen Notes Free | RSS Extraction |
|---------|------------------|----------------|
| **Apple Podcasts URLs** | ❌ No | ✅ Yes |
| **Spotify URLs** | ❌ No | ✅ Yes (most) |
| **Search by name** | ✅ Yes | ❌ No |
| **Audio URLs** | ✅ Yes | ✅ Yes |
| **Transcripts** | ❌ No | ⚠️ Rare |
| **Cost** | FREE (300/mo) | FREE (unlimited) |
| **Best For** | Search/Discovery | URL processing |

---

## Your Current System (Optimal!) ✅

### For URL Input:
```
User: https://podcasts.apple.com/...
  ↓
Skip Listen Notes (URL lookup not supported)
  ↓
Extract RSS feed (✅ free, always works)
  ↓
Match episode by title (✅ accurate)
  ↓
Get audio URL (✅ from RSS)
  ↓
Whisper transcription (✅ free)
```

**Verdict**: Perfect! Don't change.

---

## Potential Enhancement: Search Feature

### For Name/Topic Input:
```
User: "Latest Huberman Lab about sleep"
  ↓
Listen Notes search (✅ excellent for this!)
  ↓
Get episode with audio URL (✅ direct)
  ↓
Whisper transcription (✅ free)
```

**Verdict**: This would be a great use of Listen Notes!

---

## What You Get from Listen Notes

### Episode Data:
```json
{
  "audio_url": "https://audio.listennotes.com/...", // ← Direct MP3!
  "title": "Episode Title",
  "description": "Full description",
  "duration": 2385,
  "podcast_title": "Show Name",
  "episode_id": "xyz123..."
}
```

### What's Missing:
- ❌ No transcripts (use Whisper)
- ❌ No URL lookup on free tier
- ❌ No RSS feed in response

---

## API Quota

**Free Tier**:
- 300 requests/month
- Currently: 296 remaining
- Resets: Monthly

**Your Usage**:
- URL processing: 0 requests (uses RSS instead)
- Would use for: Search queries (if implemented)

---

## Recommendation

### ✅ Keep Current Approach for URLs
Your RSS-based system is perfect for:
- Apple Podcasts URLs
- Spotify URLs
- Direct RSS feeds
- Specific episode URLs

### 💡 Consider Adding Listen Notes For:
New feature - search by name:
```bash
# New command format:
python3 youtube_slash_command.py --search "Huberman Lab" --topic "sleep"
```

This would:
- Use Listen Notes search (excellent!)
- Stay within free tier quota
- Provide new functionality
- Complement existing URL support

---

## Bottom Line

**For your current use case (URL input)**:
- ✅ Current system is OPTIMAL
- ✅ RSS extraction is better than Listen Notes for URLs
- ✅ No API quota wasted
- ✅ Free and unlimited

**For potential new feature (search input)**:
- 💡 Listen Notes would be PERFECT
- ✅ Within free tier quota (300/month)
- ✅ Excellent search functionality
- ✅ Returns audio URLs directly

**Don't change what works!** Your RSS-based approach is ideal for URL processing. 🎯
