# Setup Guide for New Machine (MacBook)

This guide will help you set up the Content Summarizer on a new MacBook.

## 1. Prerequisites

Ensure you have the following installed:

*   **Python 3.10 or newer**: [Download Python](https://www.python.org/downloads/)
*   **Git**: [Download Git](https://git-scm.com/downloads)
*   **FFmpeg**: Required for audio processing.
    *   Open Terminal and run: `brew install ffmpeg`
    *   *(Note: If you don't have Homebrew, install it first from [brew.sh](https://brew.sh/))*

## 2. Clone the Repository

Open your Terminal and run:

```bash
# Navigate to where you want the project (e.g., Documents)
cd Documents

# Clone the repository
git clone https://github.com/EmanxChan/youtube-summarizer.git

# Enter the directory
cd youtube-summarizer
```

## 3. Automatic Setup (Recommended)

We have created a script to handle the setup for you. It will create the virtual environment and install all dependencies.

```bash
# Make the script executable (only needed once)
chmod +x scripts/setup.sh

# Run the setup
./scripts/setup.sh
```

## 4. Manual Setup (Alternative)

If the script fails or you prefer doing it manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 5. API Key Configuration

**Important:** For security, API keys are not stored in GitHub. You must add them manually.

1.  Copy the example file to create your config:
    ```bash
    cp .env.example .env
    ```
2.  Open `.env` in a text editor (like TextEdit, VS Code, or Nano):
    ```bash
    open -e .env
    ```
3.  Replace `gsk_your_key_here` with your actual **Groq API Key**.
    *   If you don't have it, find it in your password manager or generate a new one at [console.groq.com](https://console.groq.com).

## 6. Run the Application

To start the app:

```bash
./scripts/run.sh
```

Or manually:

```bash
# Make sure venv is active
source venv/bin/activate

# Run Streamlit
streamlit run src/content_summarizer/app.py
```
