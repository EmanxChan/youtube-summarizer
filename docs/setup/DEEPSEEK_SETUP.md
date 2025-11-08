# 🚀 Using DeepSeek with YouTube Summarizer

DeepSeek is now fully integrated! It's an excellent choice because:
- **10x cheaper** than OpenAI GPT-4o-mini 
- **High quality** - comparable to GPT-4 for summarization
- **Fast** response times
- **Simple setup** - OpenAI-compatible API

## Quick Setup

### 1. Get Your API Key
1. Go to https://platform.deepseek.com/api_keys
2. Sign up (you get free credits to start!)
3. Create an API key

### 2. Configure (Choose One Method)

#### Method A: Environment Variable (Easiest)
```bash
export DEEPSEEK_API_KEY="your-key-here"
```

#### Method B: Config File
```bash
# Run the setup script
./setup_ai.sh
# Choose option 3 (DeepSeek)
# Enter your API key
```

#### Method C: Manual Config
Create `~/.youtube_summarizer/config.json`:
```json
{
  "deepseek_api_key": "your-key-here",
  "default_provider": "deepseek",
  "default_model": "deepseek-chat"
}
```

## Usage Examples

### Basic Usage (DeepSeek as default)
```bash
./youtube https://youtu.be/VIDEO_ID
```

### Explicitly Use DeepSeek
```bash
./youtube https://youtu.be/VIDEO_ID --ai-provider deepseek
```

### Use DeepSeek Coder Model (for technical videos)
```bash
./youtube https://youtu.be/VIDEO_ID --ai-provider deepseek --ai-model deepseek-coder
```

### Compare with Other Providers
```bash
# DeepSeek (cheapest, great quality)
./youtube URL --ai-provider deepseek

# OpenAI (more expensive, similar quality)
./youtube URL --ai-provider openai

# No AI (free, lower quality extraction)
./youtube URL --ai-provider none
```

## Cost Comparison

For a typical 20-minute video:
- **DeepSeek**: ~$0.001-0.002 
- **OpenAI GPT-4o-mini**: ~$0.01-0.02 (10x more)
- **OpenAI GPT-4**: ~$0.10-0.20 (100x more)

With $1 of DeepSeek credits, you can summarize **500-1000 videos**!

## Models Available

- **deepseek-chat** (default): Best for general content, tutorials, talks
- **deepseek-coder**: Optimized for coding tutorials and technical content

## Example Output

With DeepSeek, you get the same high-quality output:
- 🎯 Actionable key takeaways
- 📝 Coherent executive summary
- 🚀 Recommended next steps
- 📄 Full transcript

## Troubleshooting

### "DeepSeek API key not found"
Set the environment variable:
```bash
export DEEPSEEK_API_KEY="your-key"
```

### Testing Your Setup
```bash
# Test with a short video
./youtube https://youtu.be/dQw4w9WgXcQ --ai-provider deepseek
```

## Why DeepSeek?

1. **Cost-Effective**: 10x cheaper than GPT-4o-mini
2. **Quality**: Comparable to GPT-4 for summarization tasks
3. **Speed**: Fast response times
4. **Reliability**: Stable API with good uptime
5. **No Rate Limits**: Generous usage limits

Perfect for users who want AI-quality summaries without breaking the bank!
