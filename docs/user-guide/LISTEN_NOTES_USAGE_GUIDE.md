# Listen Notes API - Free Tier Usage Guide

## What Listen Notes Free Tier SUPPORTS ✅

### 1. Search by Podcast Name
**Endpoint**: `/search`  
**Cost**: Free ✅  
**What You Provide**: Podcast name (text query)

```python
from listen_notes_client import ListenNotesClient

client = ListenNotesClient()

# Search for podcasts
results = client.search_podcast("Huberman Lab", limit=5)

# Results include:
for podcast in results:
    print(f"Title: {podcast['title']}")
    print(f"ID: {podcast['id']}")  # ← Important! Use this ID
    print(f"Publisher: {podcast['publisher']}")
    print(f"Total Episodes: {podcast['total_episodes']}")
    print(f"RSS URL: {podcast['rss_url']}")
```

**Example Output**:
```
Title: Huberman Lab
ID: aad0a6234cfa422d99661240da26273c
Publisher: Scicomm Media
Total Episodes: 356
RSS URL: https://feeds.megaphone.fm/hubermanlab
```

---

### 2. Get Episodes by Podcast ID
**Endpoint**: `/podcasts/{id}`  
**Cost**: Free ✅  
**What You Provide**: Podcast ID (from search results)

```python
# Use the ID from search
podcast_id = "aad0a6234cfa422d99661240da26273c"

# Get recent episodes
episodes = client.get_podcast_episodes(podcast_id, limit=10)

# Results include:
for episode in episodes:
    print(f"Title: {episode['title']}")
    print(f"Episode ID: {episode['episode_id']}")
    print(f"Duration: {episode['duration']} seconds")
    print(f"Audio URL: {episode['audio_url']}")  # ← Direct MP3 link!
    print(f"Description: {episode['description']}")
```

**Example Output**:
```
Title: Essentials: How to Exercise for Strength Gains...
Episode ID: e587a5280374461d84cbfcfcbdd17562
Duration: 2385 seconds
Audio URL: https://audio.listennotes.com/e/p/e587a528...
Description: In this Huberman Lab Essentials episode...
```

---

## What Listen Notes Free Tier DOES NOT SUPPORT ❌

### 1. Direct URL Lookup
**Endpoint**: `/just_listen` (POST)  
**Cost**: Requires paid plan ❌  
**What You'd Provide**: Apple Podcasts URL, Spotify URL, RSS feed URL

```python
# This DOES NOT work on free tier:
url = "https://podcasts.apple.com/us/podcast/.../id123?i=456"
result = client.get_episode_by_url(url)
# Returns: 405 Error (Method Not Allowed)
```

**Workaround**: Use search + episode matching instead (see below)

---

## How to Use Listen Notes Effectively on Free Tier

### Strategy 1: Search by Podcast Name

**When to Use**: You know the podcast name but not the ID

**Steps**:
1. Search for podcast by name
2. Get podcast ID from results
3. Fetch episodes using ID
4. Find episode you want by title matching

**Example**:
```python
# Step 1: Search
results = client.search_podcast("Huberman Lab", limit=1)
podcast_id = results[0]['id']

# Step 2: Get episodes
episodes = client.get_podcast_episodes(podcast_id, limit=20)

# Step 3: Find specific episode by title
target_title = "exercise for strength"
for episode in episodes:
    if target_title.lower() in episode['title'].lower():
        print(f"Found: {episode['title']}")
        print(f"Audio: {episode['audio_url']}")
        break
```

---

### Strategy 2: Cache Podcast IDs

**When to Use**: Processing same podcast multiple times

**Implementation**:
```python
# Create a mapping of podcast names to IDs
PODCAST_ID_CACHE = {
    "Huberman Lab": "aad0a6234cfa422d99661240da26273c",
    "The Daily": "f2eb196b20884b0490cc60a58b05bbb6",
    "How I Built This": "xyz123..."
}

# Use cached ID directly
podcast_id = PODCAST_ID_CACHE.get("Huberman Lab")
if podcast_id:
    episodes = client.get_podcast_episodes(podcast_id)
```

**Benefits**:
- Saves API quota
- Faster (no search needed)
- More reliable

---

### Strategy 3: Combine with RSS Fallback (Current Approach)

**Our Current System**:
```
User provides Apple Podcasts URL
    ↓
Listen Notes: Try to help (but URL lookup fails on free tier)
    ↓
RSS Extraction: Get RSS feed from Apple Podcasts ✅
    ↓
RSS Episode Matching: Find specific episode ✅
    ↓
Get audio URL from RSS ✅
```

**Why This Works**:
- ✅ No Listen Notes API calls wasted
- ✅ Works for any podcast platform
- ✅ RSS provides audio URLs directly
- ✅ Free and reliable

---

## Optimal Use Case for Listen Notes Free Tier

### Scenario: User Provides Podcast Name (Not URL)

**Example**: "Summarize the latest Huberman Lab episode about sleep"

**Flow**:
```python
# 1. Search for podcast
podcasts = client.search_podcast("Huberman Lab", limit=1)
podcast_id = podcasts[0]['id']

# 2. Get recent episodes
episodes = client.get_podcast_episodes(podcast_id, limit=10)

# 3. Find episode about "sleep"
for episode in episodes:
    if 'sleep' in episode['title'].lower():
        # Found it!
        audio_url = episode['audio_url']
        title = episode['title']
        description = episode['description']
        
        # 4. Download and transcribe with Whisper
        # ... (existing code)
        break
```

**Benefits**:
- ✅ Uses Listen Notes API effectively
- ✅ Gets audio URLs directly
- ✅ Works within free tier quota
- ✅ No RSS parsing needed

---

## What You Get from Listen Notes

### Episode Data Structure:
```json
{
  "episode_id": "e587a5280374461d84cbfcfcbdd17562",
  "title": "Essentials: How to Exercise for Strength Gains...",
  "description": "Full episode description with timestamps...",
  "audio_url": "https://audio.listennotes.com/e/p/...",
  "duration": 2385,
  "podcast_title": "Huberman Lab",
  "podcast_id": "aad0a6234cfa422d99661240da26273c",
  "pub_date": 1726642800000,
  "thumbnail": "https://..."
}
```

### What's Included:
- ✅ **Audio URL** - Direct MP3 link (can feed to Whisper!)
- ✅ **Episode metadata** - Title, description, duration
- ✅ **Podcast info** - Show name, publisher
- ✅ **Timestamps** - Publication date
- ❌ **Transcript** - Not provided (use Whisper)

---

## API Quota Management

### Free Tier Limits:
- **300 requests per month**
- **Current usage**: 4 requests used, 300 remaining
- **Resets**: Monthly

### Best Practices:

1. **Cache Results**:
   ```python
   # Our system already does this
   cache = PodcastCache(provider='listen_notes')
   cached = cache.get(podcast_url)
   if cached:
       return cached  # No API call!
   ```

2. **Batch Lookups**:
   ```python
   # Get multiple episodes at once
   episodes = client.get_podcast_episodes(podcast_id, limit=50)
   # Instead of 50 individual calls
   ```

3. **Use RSS When Possible**:
   - Apple Podcasts URLs → Extract RSS (free!)
   - Spotify URLs → Extract RSS (free!)
   - Direct RSS URLs → Parse directly (free!)

---

## Recommended Integration Strategy

### For URLs (Your Current Use Case):

**Keep Current Approach** ✅:
```
1. Try Listen Notes URL lookup (will fail on free tier)
2. Fall back to RSS extraction (always works)
3. Use RSS for episode matching (free, reliable)
4. Get audio URL from RSS (free)
5. Transcribe with Whisper (free)
```

**Why**: 
- RSS is more reliable for URL-based queries
- Listen Notes free tier doesn't support URL lookup anyway
- Saves API quota for other uses

### For Search Queries (New Feature Idea):

**Use Listen Notes** ✅:
```
User: "Summarize latest Huberman Lab episode"
1. Search Listen Notes: "Huberman Lab"
2. Get latest episodes
3. Download audio from Listen Notes URL
4. Transcribe with Whisper
```

**Why**:
- Listen Notes search is excellent
- Gets audio URLs directly
- Perfect use case for free tier
- Within quota limits

---

## Example: Building a Search Feature

### New Feature: Search by Podcast + Topic

```python
def search_and_summarize(podcast_name, topic_keyword):
    """
    Search for podcast episode by name and topic.
    Uses Listen Notes free tier effectively.
    """
    client = ListenNotesClient()
    
    # 1. Search for podcast
    podcasts = client.search_podcast(podcast_name, limit=1)
    if not podcasts:
        return None
    
    podcast_id = podcasts[0]['id']
    
    # 2. Get recent episodes
    episodes = client.get_podcast_episodes(podcast_id, limit=20)
    
    # 3. Find episode matching topic
    for episode in episodes:
        if topic_keyword.lower() in episode['title'].lower() or \
           topic_keyword.lower() in episode['description'].lower():
            
            # 4. Process episode
            audio_url = episode['audio_url']
            return {
                'title': episode['title'],
                'audio_url': audio_url,
                'description': episode['description']
            }
    
    return None

# Usage:
result = search_and_summarize("Huberman Lab", "sleep")
if result:
    print(f"Found: {result['title']}")
    print(f"Audio: {result['audio_url']}")
    # Download and transcribe...
```

---

## Summary: How to Use Listen Notes Effectively

### ✅ DO Use For:
1. **Search by podcast name** - Excellent search functionality
2. **Get episodes by podcast ID** - Returns audio URLs
3. **Discovery** - Find podcasts by topic/keyword
4. **Metadata** - Episode details, descriptions, thumbnails

### ❌ DON'T Use For:
1. **Direct URL lookup** - Not available on free tier
2. **Transcripts** - Not provided (use Whisper instead)
3. **URL-based queries** - RSS is better and free

### 💡 Best Use Case:
**User provides podcast NAME + topic/episode description**
- "Latest Huberman Lab episode"
- "The Daily episode about elections"
- "How I Built This with specific guest"

Use Listen Notes to search and find, then Whisper to transcribe!

---

## Current System Assessment

### Your Current Implementation: ✅ OPTIMAL

**For Apple Podcasts URLs**:
```
✅ Skip Listen Notes (URL lookup doesn't work on free tier)
✅ Extract RSS (reliable and free)
✅ Match episode by title (accurate)
✅ Get audio URL from RSS (free)
✅ Transcribe with Whisper (free)
```

**Verdict**: Don't change! Current approach is perfect for URL-based queries.

### Potential Enhancement: Search Feature

**Add new command format**:
```bash
# Current (URL-based):
python3 youtube_slash_command.py "https://podcasts.apple.com/..."

# New (search-based):
python3 youtube_slash_command.py --podcast "Huberman Lab" --episode "sleep"
```

This would make excellent use of Listen Notes free tier!

---

## Conclusion

**Listen Notes Free Tier**:
- ✅ Great for search and discovery
- ✅ Provides audio URLs
- ✅ 300 requests/month
- ❌ No direct URL lookup
- ❌ No transcripts

**Your Current System**:
- ✅ Already optimal for URL-based queries
- ✅ RSS extraction works better than Listen Notes for URLs
- ✅ No API quota wasted
- 💡 Could add Listen Notes for search-based queries (new feature)

**Recommendation**: Keep current RSS-based approach for URLs, consider adding Listen Notes for search queries as new feature!
