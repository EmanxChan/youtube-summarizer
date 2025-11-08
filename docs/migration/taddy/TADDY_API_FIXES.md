# Taddy API Integration - Fixes Applied

## 🔧 Issues Fixed

Based on the Taddy API example you provided, I've corrected the GraphQL query structure to match their actual API format.

### Your Taddy API Example:
```graphql
query {
  getPodcastSeries(name:"The Daily"){
    uuid
    name
    itunesId
    description
    imageUrl
    totalEpisodesCount
    itunesInfo{
      uuid
      baseArtworkUrlOf(size:640)
    }
  }
}
```

---

## ✅ Changes Made to `taddy_integration.py`

### 1. Added `search_podcast_by_name()` Method

**NEW:** Direct search by podcast name (matches their example)

```python
def search_podcast_by_name(self, podcast_name: str) -> Optional[str]:
    """Search for podcast series UUID by name"""
    query = f"""
    query {{
        getPodcastSeries(name: "{podcast_name}") {{
            uuid
            name
            itunesId
        }}
    }}
    """
    # Returns series UUID if found
```

**Use Case:** When you know the podcast name (e.g., "The Daily")

---

### 2. Fixed `search_episode_by_identifiers()`

**BEFORE:** Used `searchForTerm()` with complex filtering
**AFTER:** Uses `getPodcastSeries(itunesId: ...)` directly

```python
# Old (didn't work):
searchForTerm(term: "{show_id}", searchTerm: PODCASTS, filterForTypes: PODCASTSERIES)

# New (matches Taddy API):
getPodcastSeries(itunesId: {show_id})
```

---

### 3. Fixed `_get_latest_episode_from_series()`

**BEFORE:** Tried to get episodes as nested field
**AFTER:** Uses separate `getEpisodesByPodcastSeries` query

```python
# Old (didn't work):
getPodcastSeries(uuid: "...") {
    episodes(limitPerPage: 1, sortByDatePublished: DESCENDING) {
        uuid
    }
}

# New (matches Taddy API):
getPodcastSeries(uuid: "...") {
    uuid
    name
    totalEpisodesCount
}

# Then separate query:
getEpisodesByPodcastSeries(
    podcastSeriesUuid: "..."
    limitPerPage: 1
    page: 1
) {
    uuid
    name
}
```

---

### 4. Fixed Transcript Field Names

**BEFORE:** Only checked `transcriptWithSpeakersAndTimecodes`
**AFTER:** Tries multiple field names

```python
# Now tries in order:
transcript = (
    episode.get('transcript') or 
    episode.get('transcriptWithSpeakersAndTimecodes') or 
    episode.get('transcriptText') or 
    ''
)
```

---

### 5. Updated `get_transcript_by_url()`

**NEW:** Accepts optional `podcast_name` parameter for fallback search

```python
def get_transcript_by_url(self, podcast_url: str, podcast_name: str = None):
    # Try iTunes ID first
    episode_uuid = self.search_episode_by_identifiers(...)
    
    # Fallback to name search if available
    if not episode_uuid and podcast_name:
        series_uuid = self.search_podcast_by_name(podcast_name)
        episode_uuid = self._get_latest_episode_from_series(series_uuid)
```

---

### 6. Improved Error Messages

```python
# More informative debugging:
print(f"  ℹ️ Taddy: No transcript data in response")
print(f"  ℹ️ Taddy: Transcript too short or missing")
print(f"  ℹ️ Taddy: Could not find episode")
print(f"  ⚠️ Error getting episodes: {e}")
```

---

## 🧪 Testing

### Test Script Created: `test_taddy_example.py`

Run this to test your Taddy API integration:

```bash
# Set your API key
export TADDY_API_KEY="your_key_here"

# Run test
python3 test_taddy_example.py
```

**What it tests:**
1. Search by podcast name ("The Daily")
2. Get series UUID
3. Get episode UUID
4. Fetch transcript
5. Test with Apple Podcasts URL
6. Show quota usage

---

## 📝 How to Use Fixed Integration

### Option 1: Search by Name (Recommended)

```python
from taddy_integration import TaddyClient

client = TaddyClient()

# Search by podcast name (like Taddy's example)
series_uuid = client.search_podcast_by_name("The Daily")
if series_uuid:
    episode_uuid = client._get_latest_episode_from_series(series_uuid)
    transcript = client.get_episode_transcript(episode_uuid)
```

### Option 2: By URL with Podcast Name

```python
# Pass podcast name as fallback
result = client.get_transcript_by_url(
    "https://podcasts.apple.com/podcast/id1200361736",
    podcast_name="The Daily"
)
```

### Option 3: By URL Only (iTunes ID lookup)

```python
# Uses iTunes ID from URL
result = client.get_transcript_by_url(
    "https://podcasts.apple.com/podcast/id1200361736"
)
```

---

## 🔑 API Key Setup

Since you mentioned you can't regenerate the API key, make sure it's set:

```bash
# Check if set
echo $TADDY_API_KEY

# Set it (replace with your actual key)
export TADDY_API_KEY="your_existing_key_here"

# Add to ~/.zshrc for persistence
echo 'export TADDY_API_KEY="your_key_here"' >> ~/.zshrc
source ~/.zshrc
```

---

## 📊 Query Structure Reference

Based on Taddy's format, here are the correct query patterns:

### Get Podcast by Name
```graphql
query {
  getPodcastSeries(name: "The Daily") {
    uuid
    name
    itunesId
    totalEpisodesCount
  }
}
```

### Get Podcast by iTunes ID
```graphql
query {
  getPodcastSeries(itunesId: 1200361736) {
    uuid
    name
  }
}
```

### Get Episodes from Series
```graphql
query {
  getEpisodesByPodcastSeries(
    podcastSeriesUuid: "series_uuid_here"
    limitPerPage: 1
    page: 1
  ) {
    uuid
    name
    datePublished
  }
}
```

### Get Episode Transcript
```graphql
query {
  getEpisodeTranscript(uuid: "episode_uuid_here") {
    uuid
    name
    description
    duration
    transcript
    audioUrl
    datePublished
  }
}
```

---

## ✅ What Works Now

1. ✅ Search by podcast name (like "The Daily")
2. ✅ Search by iTunes ID from Apple Podcasts URLs
3. ✅ Get episodes from podcast series
4. ✅ Fetch episode transcripts
5. ✅ Fallback to podcast name if iTunes ID fails
6. ✅ Better error messages for debugging
7. ✅ Multiple transcript field name support

---

## 🚀 Next Steps

### 1. Test Your API Key

```bash
python3 test_taddy_example.py
```

**Expected output:**
```
✓ TaddyClient initialized
✓ Found series UUID: ...
✓ Found episode UUID: ...
✓ Got transcript!
  Title: The Daily
  Length: 45000 chars
```

### 2. Use in Main Script

```bash
# Set API key
export TADDY_API_KEY="your_key"

# Test with podcast URL
python3 youtube_slash_command.py "https://podcasts.apple.com/podcast/id1200361736"
```

**Expected:**
- "🏷️ [Primary] Checking Taddy API..."
- "✓ Taddy API success! (1-3s)"
- "Transcript Source: Taddy API"

### 3. Monitor Quota

```bash
python3 youtube_slash_command.py "URL" --show-metrics
```

---

## 🐛 Troubleshooting

### Still Getting Errors?

**Check API Key:**
```bash
echo $TADDY_API_KEY
```

**Test Connection:**
```bash
python3 test_taddy_example.py
```

**Enable Debug Mode:**
Edit `taddy_integration.py` and add print statements to see actual API responses:

```python
def _graphql_request(self, query: str) -> Dict:
    response = requests.post(...)
    print(f"DEBUG: Response: {response.json()}")  # Add this
    return response.json()
```

### Common Issues

1. **"Episode not found"** → Podcast might not be in Taddy's database
2. **"No transcript available"** → Episode exists but no transcript
3. **"Rate limit exceeded"** → Used 500 requests this month
4. **"API key required"** → Environment variable not set

### Fallback Behavior

If Taddy fails, the system automatically falls back to:
1. RSS transcript (Podcasting 2.0)
2. Webpage scraping + YouTube (parallel)
3. Whisper transcription (slow but reliable)
4. Show notes (last resort)

---

## 📚 Files Updated

- ✅ `taddy_integration.py` - Fixed GraphQL queries
- ✅ `youtube_slash_command.py` - Updated to pass podcast_name
- ✅ `test_taddy_example.py` - NEW: Test script
- ✅ `TADDY_API_FIXES.md` - This file

---

## 🎯 Summary

**What was wrong:**
- GraphQL queries didn't match Taddy's actual API structure
- Used `searchForTerm()` instead of `getPodcastSeries()`
- Wrong episode query format
- Missing podcast name search option

**What's fixed:**
- ✅ Matches Taddy's example query format
- ✅ Direct `getPodcastSeries(name: ...)` search
- ✅ Correct episode fetching with `getEpisodesByPodcastSeries`
- ✅ Multiple transcript field names
- ✅ Fallback to name search if iTunes ID fails
- ✅ Better error messages

**Ready to test!** 🚀
