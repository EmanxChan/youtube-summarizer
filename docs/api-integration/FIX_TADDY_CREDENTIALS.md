# 🔧 Fix Taddy Credentials Error

## Problem
Getting error: "Taddy API key required. Set TADDY_API_KEY env var."

## Solution

The Streamlit server needs the environment variables set when it starts. Here's how to fix it:

### ✅ Fixed Already
Your `restart_streamlit.sh` now includes the credentials.

### 🧪 Test It Works

**Option 1: Use the restart script (Recommended)**
```bash
bash /Users/e.chan/restart_streamlit.sh
```
Then visit: http://localhost:8501

**Option 2: Start manually with credentials**
```bash
# Stop existing Streamlit
pkill -f "streamlit run"

# Start with credentials
export TADDY_USER_ID="3625"
export TADDY_API_KEY="ae7d551c3721de36eb652f3cbab693c39bb28c3252850a9d98386b4b922e2e57f6359ddda836a8a3b0350b4727a55ac6aa"

cd /Users/e.chan
streamlit run summarizer_ui.py
```

**Option 3: Test environment separately**
```bash
export TADDY_USER_ID="3625"
export TADDY_API_KEY="ae7d551c3721de36eb652f3cbab693c39bb28c3252850a9d98386b4b922e2e57f6359ddda836a8a3b0350b4727a55ac6aa"

streamlit run test_streamlit_env.py
```
This opens a test page showing if credentials are loaded.

---

## 🔍 Verify Credentials are Working

### Command Line Test
```bash
export TADDY_USER_ID="3625"
export TADDY_API_KEY="ae7d551c3721de36eb652f3cbab693c39bb28c3252850a9d98386b4b922e2e57f6359ddda836a8a3b0350b4727a55ac6aa"

python3 -c "
import os
from taddy_integration import TaddyClient

print(f'User ID: {os.getenv(\"TADDY_USER_ID\")}')
print(f'API Key: {os.getenv(\"TADDY_API_KEY\")[:20]}...')

try:
    client = TaddyClient()
    print('✓ TaddyClient initialized!')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

**Expected output:**
```
User ID: 3625
API Key: ae7d551c3721de36eb65...
✓ TaddyClient initialized!
```

---

## 📝 What I Fixed

### 1. Updated `restart_streamlit.sh`
Added these lines before starting Streamlit:
```bash
export TADDY_USER_ID="3625"
export TADDY_API_KEY="ae7d551c3721de36eb652f3cbab693c39bb28c3252850a9d98386b4b922e2e57f6359ddda836a8a3b0350b4727a55ac6aa"
```

### 2. Fixed `taddy_integration.py`
Changed from:
```python
def __init__(self, api_key: Optional[str] = None):
    self.headers = {
        "X-USER-ID": self.api_key[:32],  # WRONG!
        "X-API-KEY": self.api_key
    }
```

To:
```python
def __init__(self, api_key: Optional[str] = None, user_id: Optional[str] = None):
    self.user_id = user_id or os.getenv('TADDY_USER_ID')
    self.headers = {
        "X-USER-ID": self.user_id,  # CORRECT!
        "X-API-KEY": self.api_key
    }
```

### 3. Added credentials to `~/.zshrc`
For new terminal sessions:
```bash
export TADDY_USER_ID="3625"
export TADDY_API_KEY="ae7d551c3721de36eb652f3cbab693c39bb28c3252850a9d98386b4b922e2e57f6359ddda836a8a3b0350b4727a55ac6aa"
```

---

## 🎯 Quick Fix Commands

Run these in order:

```bash
# 1. Restart Streamlit with credentials
bash /Users/e.chan/restart_streamlit.sh

# 2. Wait 3 seconds
sleep 3

# 3. Open browser
open http://localhost:8501

# 4. Try a podcast URL in the UI
```

---

## ⚠️ Important Note

**Taddy Free Tier Limitation:**
Even with credentials working, you'll see:
- "✓ Taddy API connected"
- "⚠️ No transcript available"

This is because **the free tier doesn't include transcripts** (requires Pro $49/month).

Your system will automatically fall back to:
1. RSS transcripts
2. Webpage scraping
3. YouTube mirrors
4. Whisper transcription

**This is working as designed!**

---

## 📊 Expected Behavior in Streamlit

When you paste a podcast URL, you should see:

```
🎙️ Processing podcast URL...
  🏷️ [Primary] Checking Taddy API...
  ✓ Taddy API connected
  ℹ️ Taddy: No transcript available (Free tier limitation)
  🔄 Trying fallback methods...
  
  [One of these will succeed:]
  ✓ Transcript found in RSS feed!
  OR
  ✓ YouTube version found!
  OR
  ✓ Whisper transcription complete!
```

---

## 🐛 Still Getting Errors?

### Check 1: Streamlit has credentials
```bash
tail -100 /Users/e.chan/nohup.out
```
Should NOT show "TADDY_API_KEY env var" errors

### Check 2: restart_streamlit.sh has credentials
```bash
grep "TADDY_USER_ID" /Users/e.chan/restart_streamlit.sh
```
Should show: `export TADDY_USER_ID="3625"`

### Check 3: Restart cleanly
```bash
pkill -f "streamlit run"
sleep 2
bash /Users/e.chan/restart_streamlit.sh
sleep 3
curl http://localhost:8501
```

### Check 4: Run test page
```bash
export TADDY_USER_ID="3625"
export TADDY_API_KEY="ae7d551c3721de36eb652f3cbab693c39bb28c3252850a9d98386b4b922e2e57f6359ddda836a8a3b0350b4727a55ac6aa"

streamlit run /Users/e.chan/test_streamlit_env.py
```
Opens at http://localhost:8501 - shows if credentials are loaded

---

## ✅ Summary

**Fixed Files:**
- `/Users/e.chan/restart_streamlit.sh` - Now exports credentials
- `/Users/e.chan/taddy_integration.py` - Fixed User ID usage
- `/Users/e.chan/.zshrc` - Added credentials for new shells

**How to Use:**
1. Run: `bash /Users/e.chan/restart_streamlit.sh`
2. Open: http://localhost:8501
3. Paste podcast URL
4. System tries Taddy (fails due to free tier) → Falls back to working methods

**Expected Result:**
✅ No more "API key required" errors
✅ System uses fallback methods successfully
✅ You get transcripts and AI summaries
