# How to Clear Cache - Self-Service Guide

**Last Updated:** November 7, 2025

---

## What Gets Cached?

Your content summarizer caches three types of data to speed up processing:

1. **Podcast Transcripts** - Audio transcriptions from Whisper
2. **AI Summaries** - Generated summaries and key insights
3. **Metrics** - Performance tracking data

---

## Cache Locations

| Cache Type | Location | Purpose | Typical Size |
|------------|----------|---------|--------------|
| **Podcast Transcripts** | `~/.cache/podcast_transcripts/` | Whisper audio transcriptions | 100-500 KB |
| **AI Summaries** | `~/.cache/ai_summaries/` | Cached summaries and takeaways | 200-500 KB |
| **Metrics** | `~/.cache/transcript_metrics.json` | Performance stats | 5-10 KB |

**Note:** `~` means your home directory (`/Users/e.chan/`)

---

## Why Clear Cache?

You should clear the cache when:

✅ Testing new prompts or model changes (like we just did with Llama 3.2 + V2 prompt)  
✅ Cache grows too large (>100 MB)  
✅ Getting stale results from old API responses  
✅ Model or prompt changes need fresh generation  
✅ Troubleshooting unexpected behavior  

---

## Method 1: Quick Clear (Recommended)

### Clear Everything at Once

```bash
# Open Terminal and run:
find ~/.cache/podcast_transcripts -type f -delete 2>/dev/null
find ~/.cache/ai_summaries -type f -delete 2>/dev/null
rm -f ~/.cache/transcript_metrics.json

echo "✅ All caches cleared!"
```

**What this does:**
- Removes all cached podcast transcriptions
- Removes all cached AI summaries and insights
- Removes metrics tracking file
- Safe: Only deletes cache files, not the directories

---

## Method 2: Clear Individual Caches

### Clear Only Podcast Cache
```bash
find ~/.cache/podcast_transcripts -type f -delete 2>/dev/null
echo "✅ Podcast cache cleared"
```

### Clear Only AI Summaries Cache
```bash
find ~/.cache/ai_summaries -type f -delete 2>/dev/null
echo "✅ AI summaries cache cleared"
```

### Clear Only Metrics
```bash
rm -f ~/.cache/transcript_metrics.json
echo "✅ Metrics cleared"
```

---

## Method 3: Check Cache Size First

Before clearing, see what's using space:

```bash
# Check all cache sizes
du -sh ~/.cache/podcast_transcripts
du -sh ~/.cache/ai_summaries
ls -lh ~/.cache/transcript_metrics.json

# Or combined:
echo "📊 Cache Sizes:"
du -sh ~/.cache/podcast_transcripts 2>/dev/null | grep -v "^0" || echo "Podcast: empty"
du -sh ~/.cache/ai_summaries 2>/dev/null | grep -v "^0" || echo "AI: empty"
ls -lh ~/.cache/transcript_metrics.json 2>/dev/null | awk '{print "Metrics: "$5}'
```

---

## Method 4: Selective Clearing (Advanced)

### Clear Caches Older Than X Days

**Clear podcast cache older than 7 days:**
```bash
find ~/.cache/podcast_transcripts -type f -mtime +7 -delete
echo "✅ Cleared podcasts older than 7 days"
```

**Clear AI cache older than 30 days:**
```bash
find ~/.cache/ai_summaries -type f -mtime +30 -delete
echo "✅ Cleared AI summaries older than 30 days"
```

### Clear Specific Provider Cache

**Clear only Listen Notes podcast cache:**
```bash
find ~/.cache/podcast_transcripts/listen_notes -type f -delete 2>/dev/null
echo "✅ Listen Notes cache cleared"
```

---

## Create a Handy Alias (Optional)

Add this to your `~/.zshrc` or `~/.bashrc`:

```bash
# Quick cache clear alias
alias clear-summary-cache='find ~/.cache/podcast_transcripts -type f -delete 2>/dev/null && find ~/.cache/ai_summaries -type f -delete 2>/dev/null && rm -f ~/.cache/transcript_metrics.json && echo "✅ All summarizer caches cleared!"'

# Check cache sizes
alias check-summary-cache='echo "📊 Summarizer Cache Sizes:" && du -sh ~/.cache/podcast_transcripts ~/.cache/ai_summaries 2>/dev/null && ls -lh ~/.cache/transcript_metrics.json 2>/dev/null | awk "{print \"Metrics: \"\$5}"'
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

Now you can just type:
```bash
clear-summary-cache
check-summary-cache
```

---

## What Happens After Clearing?

After clearing the cache:

1. **Next summary will be slower** - No cached transcripts or summaries
2. **Fresh AI generation** - New insights with current model/prompt
3. **API calls will be made** - For podcasts, Listen Notes API used again
4. **Cache rebuilds automatically** - New content gets cached as you use the tool

**Example:**
- **Before clear:** Summary takes 5 seconds (uses cache)
- **After clear:** Summary takes 30 seconds (regenerates everything)
- **Subsequent requests:** Fast again (new cache built)

---

## Automatic Cache Management

The system has built-in cache management:

**Podcast Cache (TTL: 30 days)**
- Automatically expires old transcripts
- Clean up runs when you fetch new podcasts
- Located in: `podcast_cache.py` (line 24)

**AI Summary Cache (No TTL)**
- Never expires automatically
- Must be cleared manually
- Useful for testing new prompts/models

**Metrics Cache**
- Small file (~6 KB)
- Safe to delete anytime
- Regenerates automatically

---

## Troubleshooting

### Cache Not Clearing?

**Check if directories exist:**
```bash
ls -la ~/.cache/ | grep -E "podcast|ai_summaries"
```

**Manually remove directories:**
```bash
# WARNING: Only do this if you know what you're doing
rm -r ~/.cache/podcast_transcripts
rm -r ~/.cache/ai_summaries
```

### Permission Issues?

**Check permissions:**
```bash
ls -la ~/.cache/
```

**Fix permissions:**
```bash
chmod -R u+w ~/.cache/podcast_transcripts
chmod -R u+w ~/.cache/ai_summaries
```

---

## Quick Reference Card

**Most Common Commands:**

```bash
# Clear everything
find ~/.cache/podcast_transcripts -type f -delete 2>/dev/null && \
find ~/.cache/ai_summaries -type f -delete 2>/dev/null && \
rm -f ~/.cache/transcript_metrics.json

# Check sizes
du -sh ~/.cache/podcast_transcripts ~/.cache/ai_summaries

# Clear if over 100MB
[ $(du -sm ~/.cache/podcast_transcripts 2>/dev/null | cut -f1) -gt 100 ] && \
  find ~/.cache/podcast_transcripts -type f -delete
```

---

## When NOT to Clear Cache

❌ **Before generating a batch of summaries** - You'll slow everything down  
❌ **During active processing** - Wait until jobs complete  
❌ **If cache is small (<50 MB)** - Not worth it unless testing  
❌ **Right before a demo** - Cache speeds up repeated requests  

---

## Cache Statistics

To see detailed cache info:

```bash
echo "📊 Detailed Cache Stats:"
echo "========================"
echo "Podcast Transcripts:"
find ~/.cache/podcast_transcripts -type f 2>/dev/null | wc -l | xargs echo "  Files:"
du -sh ~/.cache/podcast_transcripts 2>/dev/null | awk '{print "  Size: "$1}'
echo ""
echo "AI Summaries:"
find ~/.cache/ai_summaries -type f 2>/dev/null | wc -l | xargs echo "  Files:"
du -sh ~/.cache/ai_summaries 2>/dev/null | awk '{print "  Size: "$1}'
echo ""
echo "Metrics:"
ls -lh ~/.cache/transcript_metrics.json 2>/dev/null | awk '{print "  Size: "$5}' || echo "  No metrics file"
```

---

## Summary

**Quick Clear (Copy-Paste):**
```bash
find ~/.cache/podcast_transcripts -type f -delete 2>/dev/null && \
find ~/.cache/ai_summaries -type f -delete 2>/dev/null && \
rm -f ~/.cache/transcript_metrics.json && \
echo "✅ All summarizer caches cleared!"
```

**Check First:**
```bash
du -sh ~/.cache/podcast_transcripts ~/.cache/ai_summaries
```

**That's it!** 🎉

---

## Related Files

- Cache implementation: `src/podcast_cache.py`
- AI cache functions: `src/youtube_slash_command.py` (lines 883-934)
- Cache cleanup: Automatic for podcasts (30 days TTL)
