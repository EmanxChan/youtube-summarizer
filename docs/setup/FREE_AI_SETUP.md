# 🆓 Free AI Alternatives for YouTube Summarization

## Truly Free Options (No Limits)

### 1. Ollama (Recommended - 100% Free)
**Completely free, runs on your Mac locally**

#### Install Ollama:
```bash
# Download from https://ollama.ai/download
# Or install via curl:
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Download a Model:
```bash
# Best for summaries (3GB)
ollama pull llama3.2

# Smaller, faster (2GB)
ollama pull phi3

# Good balance (4GB)
ollama pull mistral
```

#### Use with YouTube Summarizer:
```bash
# Start Ollama server (if not running)
ollama serve

# Use with the summarizer
./youtube https://youtu.be/VIDEO_ID --ai-provider ollama
```

**Pros:**
- ✅ 100% free forever
- ✅ No API keys needed
- ✅ Private - data stays on your machine
- ✅ No rate limits

**Cons:**
- ❌ Uses your Mac's resources (RAM/CPU)
- ❌ Slower than cloud APIs
- ❌ Need to download models (2-7GB each)

---

## Free Tier Options (Limited but Good)

### 2. Groq (Best Free Tier)
**Very fast, generous free limits**

#### Setup:
1. Get API key: https://console.groq.com/keys
2. Set environment variable:
```bash
export GROQ_API_KEY="your-key"
```

**Free Limits:**
- 30 requests/minute
- 14,400 requests/day
- Super fast inference (10x faster than OpenAI)

**Models:**
- llama3-70b (best quality)
- mixtral-8x7b (good balance)
- gemma2-9b (fastest)

---

### 3. Google Gemini
**Good free tier with Gemini 1.5 Flash**

#### Setup:
1. Get API key: https://aistudio.google.com/apikey
2. Set environment variable:
```bash
export GEMINI_API_KEY="your-key"
```

**Free Limits:**
- 15 requests/minute
- 1 million tokens/day
- 1500 requests/day

---

### 4. Mistral AI
**Limited free tier**

#### Setup:
1. Get API key: https://console.mistral.ai/
2. Has free tier but very limited

**Note:** Not recommended for regular use due to limits

---

### 5. Together AI
**$25 free credits on signup**

#### Setup:
1. Sign up: https://together.ai/
2. Get $25 free credits
3. Access to many open models

**Good for:** Testing different models

---

## Comparison Table

| Provider | Cost | Speed | Quality | Limits | Privacy |
|----------|------|-------|---------|---------|---------|
| **Ollama** | Free | Medium | Good | None | 100% Private |
| **Groq** | Free tier | Very Fast | Good | 30/min | Cloud |
| **Gemini** | Free tier | Fast | Good | 15/min | Cloud |
| **DeepSeek** | $0.001/video | Fast | Excellent | Pay-as-you-go | Cloud |
| **Mistral** | Limited free | Fast | Good | Very limited | Cloud |

---

## Quick Ollama Setup for Mac

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Download a model (choose one)
ollama pull llama3.2     # Best overall (3GB)
ollama pull phi3         # Smallest (2GB)
ollama pull mistral      # Good balance (4GB)

# 3. Test it
ollama run llama3.2 "Summarize this: AI is transforming how we code"

# 4. Use with YouTube summarizer
./youtube https://youtu.be/VIDEO_ID --ai-provider ollama
```

---

## Recommendation

### For Completely Free:
**Use Ollama** with llama3.2 model
- No costs ever
- Good quality summaries
- Private and secure

### For Best Free Tier:
**Use Groq** with their free API
- Very generous limits
- Super fast
- High quality

### For Best Value (Nearly Free):
**Use DeepSeek** ($0.001 per video)
- Exceptional quality
- Minimal cost
- Fast and reliable

---

## Setting Up Ollama Support

The YouTube summarizer already supports Ollama! Just:

1. Install Ollama
2. Pull a model
3. Run: `./youtube URL --ai-provider ollama`

No API keys, no costs, just free AI summaries!
