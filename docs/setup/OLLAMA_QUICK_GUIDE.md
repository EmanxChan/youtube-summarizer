# 🚀 Ollama YouTube Summarizer - Quick Guide

## ✅ Setup Complete!
You now have **FREE, UNLIMITED** AI-powered YouTube summaries running locally on your Mac!

## 📋 Usage

### Basic Command
```bash
./youtube https://youtu.be/VIDEO_ID --ai-provider ollama
```

### Examples
```bash
# Standard summary
./youtube https://youtu.be/VIDEO_ID --ai-provider ollama

# Longer summary (300 words)
./youtube https://youtu.be/VIDEO_ID --ai-provider ollama --words 300

# More key takeaways (7 instead of 5)
./youtube https://youtu.be/VIDEO_ID --ai-provider ollama --takeaways-count 7

# Full featured
./youtube URL --ai-provider ollama --words 400 --takeaways-count 7
```

## 🚄 Speed Tips

### Make Ollama the Default
Edit `~/.zshrc` and add:
```bash
alias youtube='/Users/e.chan/youtube --ai-provider ollama'
```

Then just use:
```bash
youtube https://youtu.be/VIDEO_ID
```

### Try Smaller/Faster Models
```bash
# Download a smaller, faster model (1.5GB)
ollama pull gemma2:2b

# Use it
./youtube URL --ai-provider ollama --ai-model gemma2:2b
```

## 🎯 Model Recommendations

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **llama3.2:3b** ✅ | 3GB | Medium | Good | Default - best balance |
| gemma2:2b | 1.5GB | Fast | OK | Quick summaries |
| phi3 | 2GB | Fast | Good | Technical content |
| mistral | 4GB | Slower | Better | Longer videos |

## 📊 Current Setup
- **Model:** llama3.2:3b
- **Cost:** $0.00 (FREE forever!)
- **Privacy:** 100% local
- **Speed:** ~10-15 seconds per summary

## 🔥 Pro Tips

1. **Keep Ollama Running**: Ollama runs in background after first use
2. **Check Models**: `ollama list` to see installed models
3. **Update Models**: `ollama pull llama3.2:3b` to get latest version
4. **Monitor Usage**: Activity Monitor → Ollama to see resource usage

## 💡 Comparison

| Feature | Ollama (Free) | DeepSeek ($) | OpenAI ($$$) |
|---------|---------------|--------------|--------------|
| Cost per video | $0.00 | $0.001 | $0.01+ |
| 100 videos cost | $0.00 | $0.10 | $1.00+ |
| Privacy | 100% Local | Cloud | Cloud |
| Internet Required | Only for download | Yes | Yes |
| Speed | 10-15s | 5-10s | 5-10s |
| Quality | Good | Excellent | Excellent |

## 🎉 You're All Set!

You now have a powerful, FREE YouTube summarizer that:
- ✅ Generates actionable takeaways
- ✅ Creates coherent summaries
- ✅ Suggests next steps
- ✅ Costs nothing to run
- ✅ Keeps your data private

Enjoy unlimited YouTube summaries!
