# How to Get a Podcast ID - Quick Guide

## 🎯 Simplest Method (Use the Helper Script!)

### Command:
```bash
python3 get_podcast_id.py "Podcast Name"
```

### Example:
```bash
python3 get_podcast_id.py "Huberman Lab"
```

### Output:
```
🔍 Searching Listen Notes for: Huberman Lab
============================================================

✅ Found 2 podcast(s):

1. Huberman Lab
   📋 ID: aad0a6234cfa422d99661240da26273c  ← Copy this!
   👤 Publisher: Scicomm Media
   📊 Episodes: 356

============================================================
🎯 Top Result ID: aad0a6234cfa422d99661240da26273c
============================================================

💡 Usage in Python:
   podcast_id = "aad0a6234cfa422d99661240da26273c"
   episodes = client.get_podcast_episodes(podcast_id)
```

---

## 🔢 One-Liner Method

```bash
export LISTEN_NOTES_API_KEY="4e8b3079caaf4cd28bb70df528bc652c"

python3 -c "
from listen_notes_client import ListenNotesClient
results = ListenNotesClient().search_podcast('Huberman Lab', limit=1)
print(f'ID: {results[0][\"id\"]}')
"
```

**Output**: `ID: aad0a6234cfa422d99661240da26273c`

---

## 📚 Common Podcast IDs (Pre-Looked Up)

Save these for quick reference:

```python
PODCAST_IDS = {
    # Science & Health
    "Huberman Lab": "aad0a6234cfa422d99661240da26273c",
    
    # News
    "The Daily": "f2eb196b20884b0490cc60a58b05bbb6",
    
    # Add more as needed...
}

# Use directly:
podcast_id = PODCAST_IDS["Huberman Lab"]
```

---

## 💻 In Python Code

### Method 1: Direct Search
```python
from listen_notes_client import ListenNotesClient

client = ListenNotesClient()

# Search for podcast
results = client.search_podcast("Huberman Lab", limit=1)

# Get the ID
podcast_id = results[0]['id']
print(f"ID: {podcast_id}")

# Use it
episodes = client.get_podcast_episodes(podcast_id, limit=10)
```

### Method 2: With Error Handling
```python
def get_podcast_id(podcast_name):
    """Get podcast ID from Listen Notes"""
    try:
        client = ListenNotesClient()
        results = client.search_podcast(podcast_name, limit=1)
        
        if results:
            return results[0]['id']
        else:
            print(f"❌ Podcast '{podcast_name}' not found")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Usage:
podcast_id = get_podcast_id("Huberman Lab")
if podcast_id:
    print(f"✅ ID: {podcast_id}")
```

---

## 🎓 What the Search Returns

```python
results = client.search_podcast("Huberman Lab", limit=1)

# Each result contains:
podcast = results[0]
print(podcast['id'])           # aad0a6234cfa422d99661240da26273c
print(podcast['title'])        # Huberman Lab
print(podcast['publisher'])    # Scicomm Media
print(podcast['total_episodes'])  # 356
```

---

## 🚀 Quick Examples

### Get Huberman Lab ID:
```bash
python3 get_podcast_id.py "Huberman Lab"
# ID: aad0a6234cfa422d99661240da26273c
```

### Get The Daily ID:
```bash
python3 get_podcast_id.py "The Daily"
# ID: f2eb196b20884b0490cc60a58b05bbb6
```

### Get Joe Rogan ID:
```bash
python3 get_podcast_id.py "Joe Rogan Experience"
# ID: [returns the ID]
```

---

## 💡 Pro Tips

### 1. IDs Are Stable
Once you get an ID, it never changes. Cache it!

### 2. Search Once, Use Forever
```python
# Look up once
HUBERMAN_ID = "aad0a6234cfa422d99661240da26273c"

# Use many times (no API calls!)
episodes = client.get_podcast_episodes(HUBERMAN_ID, limit=10)
more_episodes = client.get_podcast_episodes(HUBERMAN_ID, limit=20)
# etc.
```

### 3. Build Your Own Cache
```python
# Create podcast_ids.py:
PODCAST_IDS = {
    "Huberman Lab": "aad0a6234cfa422d99661240da26273c",
    "The Daily": "f2eb196b20884b0490cc60a58b05bbb6",
    # Add more as you discover them
}

# Import and use:
from podcast_ids import PODCAST_IDS
podcast_id = PODCAST_IDS["Huberman Lab"]
```

---

## ⚠️ Common Issues

### Issue: "No podcasts found"
**Solutions**:
- Check spelling
- Try shorter name ("Huberman" instead of "Huberman Lab Podcast")
- Try longer name if too generic
- Check the podcast exists on Apple Podcasts/Spotify

### Issue: "API key not set"
**Solution**:
```bash
export LISTEN_NOTES_API_KEY="4e8b3079caaf4cd28bb70df528bc652c"
```

### Issue: Wrong podcast returned
**Solution**:
- Check all search results (increase limit)
- Verify by publisher name
- Check episode count matches

---

## 📊 API Usage

Each search = 1 API request

**Your quota**: 300/month

**Recommendation**: 
- Search once per podcast
- Cache the ID
- Reuse forever
- No additional API calls needed!

---

## 🎯 Summary

**Easiest way**:
```bash
python3 get_podcast_id.py "Podcast Name"
```

**Quick lookup**:
```python
from listen_notes_client import ListenNotesClient
results = ListenNotesClient().search_podcast('Name', limit=1)
podcast_id = results[0]['id']
```

**Best practice**:
```python
# Search once, cache it
HUBERMAN_ID = "aad0a6234cfa422d99661240da26273c"

# Use forever
episodes = client.get_podcast_episodes(HUBERMAN_ID)
```

**That's it!** One search gives you the ID you need. 🎉
