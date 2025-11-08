# Installing ffmpeg for Podcast Transcription

## Why ffmpeg?

ffmpeg is required for **Tier 5 (Whisper Audio Transcription)** fallback. However, most podcasts will succeed via earlier tiers:
- **Tier 1-3:** No ffmpeg needed (instant)
- **Tier 4:** YouTube mirror - no ffmpeg needed (10-20 sec)
- **Tier 5:** Whisper transcription - requires ffmpeg (2-3 min)

**Note:** 60-70% of podcasts succeed via Tier 1-4 without ffmpeg!

---

## macOS Installation

### Option 1: Homebrew (Recommended)

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install ffmpeg
brew install ffmpeg

# Verify installation
ffmpeg -version
```

### Option 2: MacPorts

```bash
# Install MacPorts from: https://www.macports.org/install.php

# Install ffmpeg
sudo port install ffmpeg

# Verify installation
ffmpeg -version
```

### Option 3: Manual Download

1. Download pre-compiled binary from: https://evermeet.cx/ffmpeg/
2. Extract the file
3. Move to `/usr/local/bin/`:
   ```bash
   sudo mv ffmpeg /usr/local/bin/
   sudo chmod +x /usr/local/bin/ffmpeg
   ```
4. Verify: `ffmpeg -version`

---

## Linux Installation

### Debian/Ubuntu

```bash
sudo apt update
sudo apt install ffmpeg
ffmpeg -version
```

### Fedora/RHEL/CentOS

```bash
sudo dnf install ffmpeg
ffmpeg -version
```

### Arch Linux

```bash
sudo pacman -S ffmpeg
ffmpeg -version
```

---

## Windows Installation

### Option 1: Chocolatey (Recommended)

```powershell
# Install Chocolatey from: https://chocolatey.org/install

# Install ffmpeg
choco install ffmpeg

# Verify installation
ffmpeg -version
```

### Option 2: Manual Download

1. Download from: https://www.gyan.dev/ffmpeg/builds/
2. Extract to `C:\ffmpeg`
3. Add to PATH:
   - Open "Environment Variables"
   - Edit "Path" variable
   - Add `C:\ffmpeg\bin`
4. Restart terminal
5. Verify: `ffmpeg -version`

---

## Verification

After installation, verify ffmpeg is working:

```bash
ffmpeg -version
```

You should see output like:
```
ffmpeg version 6.0 Copyright (c) 2000-2023 the FFmpeg developers
...
```

---

## Testing Podcast Transcription

Try a podcast URL with all fallbacks enabled:

```bash
python3 youtube_slash_command.py "https://podcasts.apple.com/us/podcast/example/id123" --words 300
```

The tool will automatically try all tiers in order and use Whisper transcription if needed.

---

## Troubleshooting

### "ffmpeg: command not found"

**Solution:** ffmpeg not in PATH
- macOS/Linux: Add to `~/.bashrc` or `~/.zshrc`:
  ```bash
  export PATH="/usr/local/bin:$PATH"
  ```
- Windows: Add ffmpeg directory to System PATH

### "Permission denied"

**Solution:** Make ffmpeg executable
```bash
sudo chmod +x /usr/local/bin/ffmpeg
```

### Transcription is slow

**Solutions:**
- Use Gist mode (automatic for episodes > 60 min)
- First transcription downloads Whisper model (~140MB)
- Subsequent transcriptions use cached model
- Consider using smaller Whisper model (already using "base")

### Cache taking up space

**Location:** `~/.cache/podcast_transcripts/`

**To clear:**
```bash
rm -rf ~/.cache/podcast_transcripts/
```

---

## Performance Tips

1. **Let tier 4 (YouTube) work first** - Most popular podcasts have YouTube versions
2. **Cache is your friend** - Re-running same podcast is instant
3. **Gist mode** - For long podcasts, first 10 minutes often sufficient
4. **Check tier 1-3 first** - 70%+ podcasts have show notes or RSS content

---

**Need Help?** Check [PODCAST_SUPPORT.md](PODCAST_SUPPORT.md) for full documentation.
