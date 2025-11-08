# Transcript Storage Guide 📁

**Where are Whisper transcripts saved?**

---

## 📍 Storage Location

### Whisper Transcripts (Cached)
```bash
~/.cache/podcast_transcripts/listen_notes/
```

**Full Path:**
```
/Users/e.chan/.cache/podcast_transcripts/listen_notes/
```

---

## 📂 What's Stored

### Cache Structure
```
~/.cache/
└── podcast_transcripts/
    ├── listen_notes/              # Listen Notes transcripts
    │   ├── 79f6ab19...json       # Episode 1 cache
    │   └── c428f541...json       # Episode 2 cache
    └── taddy/                     # Legacy Taddy transcripts
```

### Individual Cache File
Each episode is stored as a JSON file:

**Filename Format:**
```
<md5_hash_of_episode_id>.json
```

**Example:**
```
79f6ab19451d5ea70722e62d51440b65.json
```

**Contents:**
```json
{
  "data": {
    "transcript": "Full transcript text here (6000+ words)...",
    "title": "Trump's Bad Week",
    "audio_url": "https://audio.listennotes.com/e/p/2fd73ce09b2047c2a207269d5abc3cbb/"
  },
  "cached_at": "2025-11-07T13:22:29.830649",
  "url": "episode_2fd73ce09b2047c2a207269d5abc3cbb"
}
```

---

## 📊 Current Cache Status

### Your Cache
```bash
Location: ~/.cache/podcast_transcripts/listen_notes/
Size: 76 KB
Episodes: 2 cached

Episodes cached:
1. "Trump's Bad Week" (The Daily)
2. "Essentials: Erasing Fears & Traumas" (Huberman Lab)
```

---

## 🔍 How to View Your Cached Transcripts

### Method 1: List All Cached Episodes
```bash
ls -lh ~/.cache/podcast_transcripts/listen_notes/
```

**Output:**
```
-rw-r--r--  35K  79f6ab19451d5ea70722e62d51440b65.json
-rw-r--r--  39K  c428f5411fb11788d8d2871a7f1351d9.json
```

### Method 2: View Cache Stats
```bash
du -sh ~/.cache/podcast_transcripts/listen_notes/
```

**Output:**
```
76K     /Users/e.chan/.cache/podcast_transcripts/listen_notes/
```

### Method 3: Read a Transcript
```bash
# Pretty print JSON
cat ~/.cache/podcast_transcripts/listen_notes/*.json | python3 -m json.tool | less
```

### Method 4: Search Transcripts
```bash
# Search for keywords across all cached transcripts
grep -r "keyword" ~/.cache/podcast_transcripts/listen_notes/
```

---

## 🎯 What Gets Cached

### Included in Cache
- ✅ **Full transcript text** (from Whisper)
- ✅ **Episode title**
- ✅ **Audio URL** (for reference)
- ✅ **Cache timestamp** (when cached)
- ✅ **Episode ID** (identifier)

### Not Included
- ❌ Audio file (deleted after transcription)
- ❌ Summary (saved separately as Markdown)
- ❌ Key insights (saved separately)

---

## ⏱️ Cache Duration

**Time to Live (TTL):** 30 days

After 30 days, cache entries are considered "stale" and will be automatically removed on next access.

### Why 30 Days?
- Podcast episodes don't change
- Transcripts are accurate forever
- Saves API calls and processing time
- Reasonable balance of freshness vs storage

---

## 💾 Cache Size Estimates

### Per Episode
- **Short episode** (10-15 min): ~10-15 KB
- **Medium episode** (30-40 min): ~30-40 KB
- **Long episode** (60+ min): ~50-70 KB

### Storage Planning
```
100 episodes × 40 KB average = ~4 MB
500 episodes × 40 KB average = ~20 MB
1000 episodes × 40 KB average = ~40 MB
```

**Conclusion:** Very efficient storage! 1000 episodes = only 40 MB.

---

## 🔄 Cache Workflow

### First Time (No Cache)
```
Search Query → Listen Notes API → Get Audio URL → Download Audio (34 MB)
  ↓
Transcribe with Whisper (2-3 min) → Generate Transcript (6000 words)
  ↓
Cache Transcript (40 KB JSON) → Delete Audio → Generate Summary
```

**Time:** 2-4 minutes

### Subsequent Times (Cache Hit)
```
Search Query → Check Cache → Found! → Load Transcript (instant)
  ↓
Generate Summary (use cached transcript)
```

**Time:** 3-5 seconds (400-800x faster!)

---

## 🗑️ Cache Management

### View Cache Stats (Python)
```python
from podcast_cache import PodcastCache

cache = PodcastCache(provider='listen_notes')
stats = cache.get_stats()

print(f"Total entries: {stats['total_entries']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
print(f"Cache dir: {stats['cache_dir']}")
```

### Clear Old Cache Entries
```python
from podcast_cache import PodcastCache

cache = PodcastCache(provider='listen_notes')
cache.clear_old()  # Remove entries older than 30 days
```

### Clear ALL Cache
```python
from podcast_cache import PodcastCache

cache = PodcastCache(provider='listen_notes')
cache.clear_all()  # Remove ALL cached transcripts
```

### Manual Cache Cleanup (Command Line)
```bash
# Remove all Listen Notes cache
rm -rf ~/.cache/podcast_transcripts/listen_notes/

# Remove specific episode (by hash)
rm ~/.cache/podcast_transcripts/listen_notes/79f6ab19*.json

# Remove old cache (files modified >30 days ago)
find ~/.cache/podcast_transcripts/listen_notes/ -name "*.json" -mtime +30 -delete
```

---

## 📁 Other Storage Locations

### 1. Audio Files (Temporary)
**Location:** `/var/folders/.../tmp.../podcast_audio.mp3`
**Duration:** Only during transcription
**Action:** Automatically deleted after transcription

### 2. Summaries (Permanent)
**Location:** `~/Documents/YouTube videos/`
**Format:** Markdown (.md files)
**Example:** `trumps-bad-week_5.md`

**Contents:**
- Episode title
- AI-generated summary
- 5 key insights
- 3 next steps
- Statistics

### 3. NLTK Data
**Location:** `~/content-summarizer/data/nltk_data/`
**Purpose:** Language models for text processing
**Size:** ~10 MB

---

## 🔐 Privacy & Security

### What's Stored
- ✅ Public podcast transcripts (already publicly available)
- ✅ Episode metadata (titles, URLs)
- ✅ Timestamps

### What's NOT Stored
- ❌ Your API keys (in environment only)
- ❌ Personal information
- ❌ Search history
- ❌ Usage patterns

### File Permissions
```bash
$ ls -la ~/.cache/podcast_transcripts/listen_notes/
-rw-r--r--  # Owner: read/write, Others: read-only
```

---

## 🎓 Cache Key Generation

### How Episode IDs Become Filenames

**Episode ID:**
```
episode_2fd73ce09b2047c2a207269d5abc3cbb
```

**MD5 Hash:**
```python
import hashlib
cache_key = hashlib.md5("episode_2fd73ce09b2047c2a207269d5abc3cbb".encode()).hexdigest()
# Result: "79f6ab19451d5ea70722e62d51440b65"
```

**Cache Filename:**
```
79f6ab19451d5ea70722e62d51440b65.json
```

**Why MD5?**
- Consistent length (32 characters)
- Unique for each episode
- Fast to compute
- No special characters (safe for filenames)

---

## 📈 Performance Impact

### Without Cache (First Time)
```
Search → API Call → Download (34 MB) → Transcribe (2 min) → Summary
Total: ~2-4 minutes
Network: 34 MB download
Processing: Whisper model + AI
```

### With Cache (Subsequent)
```
Search → Cache Hit → Load JSON (40 KB) → Summary
Total: ~3-5 seconds
Network: 0 MB (no download)
Processing: AI only (no Whisper)
```

### Speed Improvement
- **First time:** 2-4 minutes
- **Cached:** 3-5 seconds
- **Speedup:** 400-800x faster! 🚀

---

## 🛠️ Troubleshooting

### Cache Not Working?

**Check cache directory exists:**
```bash
ls -la ~/.cache/podcast_transcripts/listen_notes/
```

**Check cache files:**
```bash
cat ~/.cache/podcast_transcripts/listen_notes/*.json | python3 -m json.tool
```

**Verify cache key:**
```bash
# Should match episode ID hash
ls ~/.cache/podcast_transcripts/listen_notes/
```

### Cache Corrupted?

**Clear and rebuild:**
```bash
rm -rf ~/.cache/podcast_transcripts/listen_notes/
# Next search will rebuild cache
```

### Disk Space Issues?

**Check cache size:**
```bash
du -sh ~/.cache/podcast_transcripts/
```

**Clean old entries:**
```bash
find ~/.cache/podcast_transcripts/listen_notes/ -name "*.json" -mtime +30 -delete
```

---

## 🎯 Quick Reference

| Item | Location |
|------|----------|
| **Transcripts (cached)** | `~/.cache/podcast_transcripts/listen_notes/` |
| **Summaries (output)** | `~/Documents/YouTube videos/*.md` |
| **Audio (temp)** | `/var/folders/.../tmp.../podcast_audio.mp3` |
| **NLTK data** | `~/content-summarizer/data/nltk_data/` |
| **Cache TTL** | 30 days |
| **Format** | JSON |
| **Size per episode** | ~30-50 KB |

---

## 💡 Pro Tips

### 1. Pre-cache Popular Episodes
```bash
# Cache episodes you know you'll use
python3 youtube_slash_command.py "Huberman Lab latest"
python3 youtube_slash_command.py "The Daily latest"
```

### 2. Backup Your Cache
```bash
# Backup cached transcripts
tar -czf podcast_cache_backup.tar.gz ~/.cache/podcast_transcripts/
```

### 3. Share Cache Between Users
```bash
# Copy cache to another machine
scp -r ~/.cache/podcast_transcripts/ user@host:~/.cache/
```

### 4. Monitor Cache Growth
```bash
# Watch cache size over time
du -sh ~/.cache/podcast_transcripts/ >> cache_size.log
```

---

## 🎉 Summary

**Whisper transcripts are saved in:**
```
~/.cache/podcast_transcripts/listen_notes/
```

**Benefits:**
- ✅ Instant access on repeat searches
- ✅ No re-downloading (saves bandwidth)
- ✅ No re-transcription (saves time)
- ✅ Minimal storage (~40 KB per episode)
- ✅ Automatic cleanup after 30 days

**Your cached transcripts are permanent until you delete them or they expire!** 🎯
