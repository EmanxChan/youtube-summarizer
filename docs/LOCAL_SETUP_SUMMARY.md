# YouTube Summarizer - Local Setup Complete! 🎉

## ✅ What's Running

Your YouTube Summarizer is live on localhost with **Local Qwen 2.5 7B** as the AI engine.

---

## 🌐 Access Your App

**URL:** http://localhost:8501

**Status:** ✅ Running (Process ID: 3682)

---

## 🔧 Current Configuration

### AI Provider
- **Default:** Ollama (local)
- **Model:** Qwen 2.5 7B Instruct (q4_K_M quantized)
- **Size:** 4.7 GB
- **Cost:** $0 (completely free, runs on your Mac)

### Available Models
1. **qwen2.5:7b-instruct-q4_K_M** - Default, good balance
2. **llama3.2:3b** - Backup, lighter and faster

### Alternative Providers (Configured but not active)
- OpenAI (requires API key)
- Anthropic Claude (requires API key)
- DeepSeek (requires API key - $0.002/video)
- OpenRouter (requires API key + privacy config - free tier available)

---

## 🚀 Features

Your Streamlit app supports:

✨ **Content Types:**
- 📺 YouTube videos (with transcripts)
- 🎙️ Podcasts (Apple/Spotify/RSS via Listen Notes API)
- 📰 Web articles

✨ **AI Features:**
- Key Takeaways (5 profound insights)
- Executive Summary
- Next Steps (actionable items)

✨ **UI Features:**
- 🌙 Dark/Light mode toggle
- Customizable summary length (50-3000 words)
- Download markdown reports
- Preview in-app

---

## 📊 Performance Profile

**Qwen 2.5 7B Local:**
- Quality Score: 7.1/10 (good insight depth)
- Speed: ~30-40s per summary
- ⚠️ Note: May cause Mac heating with heavy use

**Quality Characteristics:**
- ✅ Identifies tradeoffs and limitations
- ✅ Technical depth and mechanisms
- ✅ Non-obvious insights
- ✅ Strategic context included

---

## 🎯 How to Use

### Via Streamlit UI (Recommended)
1. Open: http://localhost:8501
2. Paste YouTube/Podcast/Article URL
3. Adjust word count (default: 500)
4. Click "✨ Summarize"
5. Download or view results

### Via Command Line
```bash
# Basic usage (uses Ollama/Qwen by default)
python3 youtube_slash_command.py "https://youtube.com/watch?v=..."

# Customize output
python3 youtube_slash_command.py "VIDEO_URL" \
  --words 800 \
  --format md \
  --takeaways-count 7

# Use different AI provider
python3 youtube_slash_command.py "VIDEO_URL" \
  --ai-provider deepseek \
  --ai-model deepseek-chat
```

---

## 🔄 Switching AI Providers

### To Use DeepSeek API (for deployment/no heating)
```bash
export DEEPSEEK_API_KEY="sk-1c20a90f0d3947a3b3ca1a45c911dea8"

python3 youtube_slash_command.py "VIDEO_URL" --ai-provider deepseek
```
**Cost:** ~$0.002 per video

### To Use OpenRouter (free tier)
1. Configure privacy: https://openrouter.ai/settings/privacy
2. ```bash
   export OPENROUTER_API_KEY="sk-or-v1-..."
   
   python3 youtube_slash_command.py "VIDEO_URL" \
     --ai-provider openrouter \
     --ai-model deepseek/deepseek-chat-v3.1:free
   ```

---

## 📁 Project Structure

```
/Users/e.chan/
├── summarizer_ui.py              # Streamlit web interface
├── youtube_slash_command.py      # Main CLI script
├── ai_summarizer.py              # AI provider integrations
├── listen_notes_client.py        # Podcast API client
├── find_test_content.py          # Test content finder
├── test_openrouter_simple.py     # Model comparison tool
├── openrouter_comparison.md      # Benchmark results
└── DEPLOYMENT_GUIDE.md           # Cloud deployment instructions
```

---

## 🛠️ Troubleshooting

### Streamlit Not Running?
```bash
# Start manually
python3 -m streamlit run summarizer_ui.py --server.port 8501
```

### Ollama Not Responding?
```bash
# Check status
ollama list

# If not running, launch Ollama.app from Applications
```

### Model Too Slow / Mac Overheating?
**Option 1:** Switch to lighter model
```bash
# In ai_summarizer.py, change line 127 to:
self.model = self.model or "llama3.2:3b"
```

**Option 2:** Use API instead (DeepSeek recommended)
- No local processing = no heating
- Faster response times
- ~$0.002 per video

---

## 📈 Next Steps

### For Personal Use:
✅ Keep using local Qwen - it's working great!

### For Deployment (Other Computer Access):
1. Review: `DEPLOYMENT_GUIDE.md`
2. Choose platform: Streamlit Cloud (free) or Railway ($5/month)
3. Switch to API provider (DeepSeek recommended)
4. Deploy with 1-click

### For Better Quality:
Test DeepSeek V3 or GPT-4o-mini for deeper insights
- DeepSeek: $0.002/video
- GPT-4o-mini: $0.003/video

---

## 🎊 You're All Set!

Your YouTube Summarizer is running locally with Qwen 2.5 7B, ready to generate profound insights from any video, podcast, or article!

**Access now:** http://localhost:8501

**Questions?** Everything is documented in the files above.
