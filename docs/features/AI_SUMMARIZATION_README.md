# 🤖 AI-Powered YouTube Summarization

## Overview
The YouTube summarizer now supports AI-powered summarization using OpenAI, Anthropic Claude, DeepSeek, or local Ollama models. This generates truly insightful summaries and actionable takeaways instead of just extracting sentences.

## Features

### 🎯 Actionable Key Takeaways
- Each takeaway starts with an action verb (Learn, Master, Implement, etc.)
- Specific and practical - things you can actually DO
- Includes the benefit or outcome of taking the action

### 📝 Coherent Executive Summary  
- Opens with what the video teaches and why it matters
- Explains the main concepts clearly
- Focuses on value, not play-by-play actions
- Helps you decide if the video is worth watching

### 🚀 Recommended Next Steps
- Builds on what was learned in the video
- Includes specific resources and exercises
- Has clear success metrics

## Setup

### Quick Setup
```bash
./setup_ai.sh
```

### Manual Setup

#### Option 1: Environment Variables
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
# OR
export ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
# OR
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

#### Option 2: Config File
Create `~/.youtube_summarizer/config.json`:
```json
{
  "openai_api_key": "sk-your-api-key",
  "deepseek_api_key": "your-deepseek-key",
  "default_provider": "deepseek",
  "default_model": "deepseek-chat"
}
```

### Install Dependencies
```bash
pip install -r requirements_ai.txt
```

## Usage

### Basic Usage (AI enabled by default)
```bash
./youtube https://youtu.be/VIDEO_ID
```

### Specify AI Provider
```bash
# Use OpenAI
./youtube https://youtu.be/VIDEO_ID --ai-provider openai

# Use DeepSeek (recommended - great quality, low cost)
./youtube https://youtu.be/VIDEO_ID --ai-provider deepseek

# Use Anthropic Claude  
./youtube https://youtu.be/VIDEO_ID --ai-provider anthropic

# Use local Ollama
./youtube https://youtu.be/VIDEO_ID --ai-provider ollama

# Disable AI (use extraction method)
./youtube https://youtu.be/VIDEO_ID --ai-provider none
```

### Specify Model
```bash
# DeepSeek models (best value!)
./youtube URL --ai-provider deepseek --ai-model deepseek-chat   # General purpose (default)
./youtube URL --ai-provider deepseek --ai-model deepseek-coder  # For technical/coding videos

# OpenAI models
./youtube URL --ai-model gpt-4           # Best quality, slower
./youtube URL --ai-model gpt-4o-mini     # Good quality, faster (default)
./youtube URL --ai-model gpt-3.5-turbo   # Decent quality, fastest

# Anthropic models
./youtube URL --ai-provider anthropic --ai-model claude-3-5-sonnet-20241022  # Best
./youtube URL --ai-provider anthropic --ai-model claude-3-haiku-20240307     # Faster
```

### Adjust Summary Length
```bash
./youtube URL --words 500  # Longer summary
```

## Cost Estimates

### DeepSeek (per video) - MOST COST-EFFECTIVE
- **deepseek-chat**: ~$0.001-0.002 (10x cheaper than GPT-4o-mini!)
- **deepseek-coder**: ~$0.001-0.002 (for technical content)

### OpenAI (per video)
- **gpt-4o-mini**: ~$0.01-0.02 (recommended)
- **gpt-4**: ~$0.10-0.20
- **gpt-3.5-turbo**: ~$0.005-0.01

### Anthropic (per video)
- **claude-3-haiku**: ~$0.01-0.02 (recommended)
- **claude-3-5-sonnet**: ~$0.05-0.10

## Example Output

With AI enabled, you get:

```markdown
# Video Title

## 🎯 Key Takeaways
1. **Master keyboard shortcuts in Cursor to code 3x faster than traditional IDEs**
2. **Configure AI code completion settings to match your coding style**
3. **Implement test-driven development workflow to catch bugs early**

## 📝 Executive Summary
This comprehensive tutorial teaches AI-assisted coding using Cursor IDE...
[Coherent 200-word summary explaining concepts and value]

## 🚀 Recommended Next Steps
- [ ] Practice Cursor shortcuts for 15 minutes daily
- [ ] Build a sample TODO app using AI-assisted workflow
- [ ] Join Cursor Discord community to share your project

## 📄 Full Transcript
[Complete transcript for reference]
```

## Troubleshooting

### "API key not found"
- Run `./setup_ai.sh` to configure
- Or set environment variable: `export OPENAI_API_KEY="your-key"`

### "AI summarization failed, using extraction method"
- Check your API key is valid
- Ensure you have API credits remaining
- Try a different model with `--ai-model`

### "Module not found" error
```bash
pip install -r requirements_ai.txt
```

## Getting API Keys

- **DeepSeek** (Recommended - cheapest): https://platform.deepseek.com/api_keys
  - $1 gets you ~500-1000 video summaries!
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys

All providers offer free credits for new users to get started.
