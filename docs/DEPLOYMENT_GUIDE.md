# Deployment Guide: YouTube Summarizer

## Prerequisites
1. Get a DeepSeek API key from https://platform.deepseek.com/
   - Sign up (free initial credits often available)
   - Create API key in dashboard
   - **Cost:** ~$0.002 per video summary (very cheap!)

## Option 1: Railway (Recommended - $5 free credit)

### Steps:
1. **Initialize Git repo (if not already)**
   ```bash
   cd /Users/e.chan
   git init
   git add summarizer_ui.py youtube_slash_command.py ai_summarizer.py
   git add requirements_deploy.txt Procfile .streamlit/
   git commit -m "Initial commit for deployment"
   ```

2. **Push to GitHub**
   ```bash
   # Create new repo at github.com/new
   git remote add origin https://github.com/YOUR_USERNAME/youtube-summarizer.git
   git branch -M main
   git push -u origin main
   ```

3. **Deploy to Railway**
   - Go to https://railway.app/
   - Click "Start a New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Add environment variables:
     - `DEEPSEEK_API_KEY` = your-api-key-here
   - Railway will auto-detect Procfile and deploy

4. **Access your app**
   - Railway provides a public URL like: `your-app.railway.app`
   - Access from any computer!

**Cost:** ~$2-5/month (you get $5 free monthly credit)

---

## Option 2: Streamlit Cloud (Easiest - FREE)

### Steps:
1. **Push code to GitHub** (same as above)

2. **Deploy to Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Click "New app"
   - Connect GitHub repository
   - Select `summarizer_ui.py` as main file
   - Add secrets in dashboard:
     ```
     DEEPSEEK_API_KEY = "your-api-key-here"
     ```
   - Click "Deploy"

3. **Access your app**
   - Get a URL like: `your-app.streamlit.app`
   - 100% free!

**Cost:** FREE

---

## Option 3: Render (Alternative - Free tier)

### Steps:
1. **Push to GitHub** (same as above)

2. **Deploy to Render**
   - Go to https://render.com/
   - Click "New +" → "Web Service"
   - Connect GitHub repo
   - Build command: `pip install -r requirements_deploy.txt`
   - Start command: `streamlit run summarizer_ui.py --server.port $PORT`
   - Add environment variable: `DEEPSEEK_API_KEY`

**Cost:** FREE (with sleep after inactivity)

---

## Important Notes

### 1. Update Default AI Provider for Deployment
Your code currently defaults to `ollama` which won't work on cloud platforms.

**In `youtube_slash_command.py`, change:**
```python
default='ollama'  # ← Change this
```
**To:**
```python
default='deepseek'  # ← For deployment
```

### 2. Remove Heavy Dependencies
`faster-whisper` is removed from `requirements_deploy.txt` because:
- It's 2GB+ with models
- Requires CPU-intensive transcription
- YouTube Transcript API is sufficient for most videos

### 3. Cost Estimates with DeepSeek
- 1 video: $0.002
- 100 videos/month: $0.20
- 1000 videos/month: $2.00

Much cheaper than running your Mac 24/7!

---

## Testing Locally with DeepSeek First

Before deploying, test with DeepSeek locally:

```bash
export DEEPSEEK_API_KEY="your-key-here"
python3 youtube_slash_command.py "https://youtube.com/watch?v=..." --ai-provider deepseek
```

If it works locally, it'll work deployed!

---

## Quick Start Command Summary

```bash
# 1. Create GitHub repo
git init
git add .
git commit -m "Deploy YouTube Summarizer"

# 2. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/youtube-summarizer.git
git push -u origin main

# 3. Go to streamlit.io/cloud and click "New app"
# 4. Add DEEPSEEK_API_KEY in secrets
# 5. Done! Access from anywhere
```

**Questions? Issues?** Check the logs in your deployment platform's dashboard.
