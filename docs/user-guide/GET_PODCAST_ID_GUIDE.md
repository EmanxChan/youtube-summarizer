# How to Get a Podcast ID from Listen Notes

## Method 1: Search by Name (Easiest!) ✅

### Quick Command:
```bash
export LISTEN_NOTES_API_KEY="4e8b3079caaf4cd28bb70df528bc652c"

python3 -c "
from listen_notes_client import ListenNotesClient
client = ListenNotesClient()

# Search for your podcast
results = client.search_podcast('Huberman Lab', limit=3)

for i, podcast in enumerate(results, 1):
    print(f'{i}. {podcast[\"title\"]}')
    print(f'   ID: {podcast[\"id\"]}')
    print(f'   Episodes: {podcast[\"total_episodes\"]}')
    print()
"
```

### Output:
```
1. Huberman Lab
   ID: aad0a6234cfa422d99661240da26273c  ← This is what you need!
   Episodes: 356

2. Губерман по-русски | HubermanLab
   ID: 71b3e679e1c4482dbb32d42ea48b99ea
   Episodes: 4
```

---

## Method 2: Helper Script

### Create a Simple ID Lookup Tool:

Save this as `get_podcast_id.py`:
```python
#!/usr/bin/env python3
"""
Quick tool to get podcast ID from Listen Notes
Usage: python3 get_podcast_id.py "Podcast Name"
"""
import sys
from listen_notes_client import ListenNotesClient

if len(sys.argv) < 2:
    print("Usage: python3 get_podcast_id.py 'Podcast Name'")
    sys.exit(1)

podcast_name = sys.argv[1]
client = ListenNotesClient()

print(f"\n🔍 Searching for: {podcast_name}\n")

results = client.search_podcast(podcast_name, limit=5)

if not results:
    print("❌ No podcasts found")
    sys.exit(1)

print("Found podcasts:\n")
for i, podcast in enumerate(results, 1):
    print(f"{i}. {podcast['title']}")
    print(f"   📋 ID: {podcast['id']}")
    print(f"   👤 Publisher: {podcast['publisher']}")
    print(f"   📊 Episodes: {podcast['total_episodes']}")
    print()

# Copy first result to clipboard (optional)
top_id = results[0]['id']
print(f"✅ Top result ID: {top_id}")
print(f"💡 Tip: Copy this ID for use in your code")
```

### Usage:
```bash
python3 get_podcast_id.py "Huberman Lab"
python3 get_podcast_id.py "The Daily"
python3 get_podcast_id.py "How I Built This"
```

---

## Method 3: Common Podcast IDs (Pre-looked Up)

### Popular Podcasts:

```python
PODCAST_IDS = {
    "Huberman Lab": "aad0a6234cfa422d99661240da26273c",
    "The Daily": "f2eb196b20884b0490cc60a58b05bbb6",
    "How I Built This": "xyz123...",  # Look up as needed
    # Add more as you use them
}

# Use directly:
podcast_id = PODCAST_IDS["Huberman Lab"]
episodes = client.get_podcast_episodes(podcast_id)
```

---

## Method 4: Interactive Search in Python

### Try It Now:
```bash
python3 -i -c "
from listen_notes_client import ListenNotesClient
client = ListenNotesClient()

def find_podcast(name):
    '''Search for podcast and show IDs'''
    results = client.search_podcast(name, limit=5)
    for i, p in enumerate(results, 1):
        print(f'{i}. {p[\"title\"]}: {p[\"id\"]}')
    return results

# Usage:
# >>> find_podcast('Huberman Lab')
# >>> find_podcast('The Daily')
"
```

Then in the Python shell:
```python
>>> find_podcast('Huberman Lab')
1. Huberman Lab: aad0a6234cfa422d99661240da26273c
2. Губерман по-русски: 71b3e679e1c4482dbb32d42ea48b99ea
```

---

## What to Do with the Podcast ID

### Once You Have the ID:

```python
podcast_id = "aad0a6234cfa422d99661240da26273c"

# Get episodes
episodes = client.get_podcast_episodes(podcast_id, limit=10)

# Each episode has:
for episode in episodes:
    print(f"Title: {episode['title']}")
    print(f"Audio: {episode['audio_url']}")  # ← Direct MP3 link!
    print(f"Duration: {episode['duration']} seconds")
    print()
```

---

## Quick Test for Common Podcasts

```bash
export LISTEN_NOTES_API_KEY="4e8b3079caaf4cd28bb70df528bc652c"

# Test with popular podcasts
python3 -c "
from listen_notes_client import ListenNotesClient
client = ListenNotesClient()

podcasts = ['Huberman Lab', 'The Daily', 'Joe Rogan Experience']

print('PODCAST IDS:\n')
for name in podcasts:
    results = client.search_podcast(name, limit=1)
    if results:
        print(f'{name}:')
        print(f'  ID: {results[0][\"id\"]}')
        print(f'  Episodes: {results[0][\"total_episodes\"]}\n')
"
```

---

## Building a Podcast ID Cache

### Create a Persistent Cache:

```python
import json
from pathlib import Path

class PodcastIDCache:
    def __init__(self, cache_file="podcast_ids.json"):
        self.cache_file = Path(cache_file)
        self.cache = self.load()
    
    def load(self):
        if self.cache_file.exists():
            with open(self.cache_file) as f:
                return json.load(f)
        return {}
    
    def save(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get(self, podcast_name):
        return self.cache.get(podcast_name)
    
    def add(self, podcast_name, podcast_id):
        self.cache[podcast_name] = podcast_id
        self.save()
    
    def search_and_cache(self, podcast_name):
        # Check cache first
        cached_id = self.get(podcast_name)
        if cached_id:
            return cached_id
        
        # Search Listen Notes
        client = ListenNotesClient()
        results = client.search_podcast(podcast_name, limit=1)
        if results:
            podcast_id = results[0]['id']
            self.add(podcast_name, podcast_id)
            return podcast_id
        
        return None

# Usage:
cache = PodcastIDCache()
podcast_id = cache.search_and_cache("Huberman Lab")
# Next time: instant lookup from cache!
```

---

## Summary: Getting Podcast IDs

### Easiest Method:
```python
from listen_notes_client import ListenNotesClient
client = ListenNotesClient()

# Search by name
results = client.search_podcast("Huberman Lab", limit=1)
podcast_id = results[0]['id']

print(f"ID: {podcast_id}")
```

### Pro Tips:
1. ✅ Search once, cache the ID
2. ✅ Build a dictionary of common podcast IDs
3. ✅ IDs are stable (don't change)
4. ✅ One search = one API request

### Common Pattern:
```python
# Search once
HUBERMAN_ID = "aad0a6234cfa422d99661240da26273c"

# Use many times
episodes = client.get_podcast_episodes(HUBERMAN_ID, limit=10)
# No additional API calls needed!
```

---

## Bottom Line

**Getting a podcast ID is simple**:
1. Search by podcast name
2. Get ID from results
3. Use ID for all future episode lookups
4. Cache it for reuse

**One search gives you the ID forever!** 🎯
