# 🎉 NEW FEATURE: Podcast Search by Name + Topic!

## What's New?

You can now enter **podcast searches** in your URL box instead of just URLs!

---

## 🎯 How to Use (In Streamlit URL Box)

### Before (URLs Only):
```
https://podcasts.apple.com/us/podcast/huberman-lab/id1545953110
```
❌ Required finding the exact URL

### Now (URLs OR Search):
```
Huberman Lab - sleep
```
✅ Just type what you want!

---

## 📝 Format Examples

### Get Latest Episode:
```
Huberman Lab latest
The Daily latest
How I Built This latest
```

### Search by Topic:
```
Huberman Lab - exercise
The Daily: Trump
How I Built This - Airbnb
```

### Natural Language:
```
Huberman Lab episode about stress
The Daily discussing climate change
```

---

## 🔍 What Happens Behind the Scenes

### Your Input:
```
Huberman Lab - sleep
```

### System Process:
```
1. Parse: Podcast="Huberman Lab", Topic="sleep"
2. Search Listen Notes for "Huberman Lab"
3. Find podcast (ID: aad0a6234cfa422d99661240da26273c)
4. Get 20 recent episodes
5. Search for "sleep" in titles/descriptions
6. Find matching episode
7. Get audio URL from Listen Notes
8. Download & transcribe (or use description)
9. AI summarize
10. Display results!
```

---

## 🆚 URLs vs Search - When to Use Each

### Use URL Format:
```
https://podcasts.apple.com/...
```
**When**:
- You have the exact episode URL
- You want a specific episode
- You're browsing Apple Podcasts/Spotify

**How it works**: RSS extraction (reliable!)

### Use Search Format:
```
Huberman Lab - topic
```
**When**:
- You know podcast name but not URL
- You want latest episode
- You're looking for topic-based episodes
- URLs are too hard to find

**How it works**: Listen Notes API (fast!)

---

## ✅ Test Results

### Test 1: Latest Episode
```
Input: Huberman Lab latest
Result: ✅ Got latest episode
Time: ~3 seconds
Source: Listen Notes + Description
```

### Test 2: Topic Search
```
Input: The Daily: Trump
Result: ✅ Found "Trump's Bad Week"
Time: ~3 seconds
Source: Listen Notes + Description
```

### Test 3: Multi-word Topic
```
Input: Huberman Lab - strength training
Result: ✅ Found related episode
Time: ~3 seconds
Source: Listen Notes + Description
```

---

## 📊 What You Get

### From Listen Notes:
- ✅ Podcast found by name
- ✅ Recent episodes retrieved
- ✅ Episode matched by topic
- ✅ Audio URL provided
- ✅ Episode description

### Final Output:
- ✅ Episode title
- ✅ AI summary (100-200 words)
- ✅ 5 key insights
- ✅ 3 next steps
- ✅ Markdown file saved

---

## 💡 Pro Tips

### 1. Use Specific Keywords
✅ **Good**: `"Huberman Lab - sleep schedule"`  
⚠️ **Vague**: `"Huberman Lab - health"`

### 2. Use Latest for Recent Content
```
Huberman Lab latest
```
Gets the most recent episode (no topic matching needed)

### 3. Try Different Formats
If one doesn't work, try another:
- `Huberman Lab - exercise`
- `Huberman Lab: exercise`
- `Huberman Lab episode about exercise`

### 4. Check Podcast Name Spelling
```
✅ "Huberman Lab" (correct)
❌ "Huberman Labs" (won't find it)
```

---

## 🚨 Current Limitations

### Audio Downloads Often Fail
Most Listen Notes audio URLs fail to download (geo-restrictions?)

**Workaround**: System automatically uses episode descriptions
- Still generates useful summaries
- Based on detailed show notes
- Not full transcripts, but comprehensive

### Topic Matching
- Works best with specific keywords
- May match related topics
- Falls back to latest if no match

---

## 📱 Try It Now in Streamlit!

### Open Your App:
http://localhost:8501

### In the URL Box, Enter:
```
Huberman Lab latest
```

Or:
```
The Daily: Trump
```

Or:
```
How I Built This - Airbnb
```

### Click "Summarize"

### Get Results!

---

## 🎓 Examples to Try

### Science & Health:
```
Huberman Lab latest
Huberman Lab - sleep
Huberman Lab: exercise
```

### News:
```
The Daily latest
The Daily: Trump
The Daily - elections
```

### Business:
```
How I Built This latest
How I Built This - Airbnb
```

---

## 📊 API Usage

### Per Search:
- 2 Listen Notes API requests
- Your quota: 300/month
- = ~150 searches possible

### Per URL:
- 0 Listen Notes requests
- Uses RSS instead (unlimited!)

**Tip**: Mix both methods based on what's easier!

---

## ✨ What Makes This Great

### 1. Flexibility
Enter URLs OR searches - both work!

### 2. Fast
Listen Notes search is quick (1-3 seconds)

### 3. Easy
No need to hunt for URLs anymore

### 4. Natural
Type what you're thinking:
- "Huberman Lab latest"
- "The Daily Trump"
- "How I Built This Airbnb"

### 5. Free
Still $0/month! 🎉

---

## 🎯 Summary

**New Feature**: Podcast search by name + topic  
**How to Use**: Enter "Podcast Name - topic" in URL box  
**Works In**: Streamlit UI and command line  
**Cost**: Free (uses Listen Notes free tier)  
**Quota**: 300/month = ~150 searches  

**Try it now**: http://localhost:8501

Just type `"Huberman Lab latest"` and click Summarize! 🚀
