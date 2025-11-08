#!/bin/bash

echo "🧪 Testing Ollama with YouTube Summarizer"
echo "=========================================="
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed yet."
    echo ""
    echo "Please:"
    echo "1. Download from the browser window that just opened"
    echo "2. Install Ollama.app to Applications"
    echo "3. Launch Ollama (it will appear in your menu bar)"
    echo "4. Then run this script again"
    exit 1
fi

echo "✅ Ollama is installed!"
echo ""

# Check if any models are available
models=$(ollama list 2>/dev/null | tail -n +2)
if [ -z "$models" ]; then
    echo "📦 No models found. Downloading llama3.2 (3GB)..."
    echo "This will take a few minutes..."
    ollama pull llama3.2:3b
    echo "✅ Model downloaded!"
else
    echo "📦 Available models:"
    ollama list
fi

echo ""
echo "🎬 Testing with a YouTube video..."
echo ""

# Test with a short video
VIDEO_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
echo "Testing with: $VIDEO_URL"
echo "Running: ./youtube \"$VIDEO_URL\" --ai-provider ollama --words 100"
echo ""

# Run the YouTube summarizer with Ollama
/Users/e.chan/youtube "$VIDEO_URL" --ai-provider ollama --words 100

echo ""
echo "---"
echo ""
echo "✨ If you see a summary above, Ollama is working perfectly!"
echo ""
echo "Usage examples:"
echo "  ./youtube URL --ai-provider ollama              # Use default model"
echo "  ./youtube URL --ai-provider ollama --words 300  # Longer summary"
echo ""
echo "To try different models:"
echo "  ollama pull phi3        # Smaller, faster (2GB)"
echo "  ollama pull mistral     # Better quality (4GB)"
echo "  ollama pull gemma2:2b   # Tiny, very fast (1.5GB)"
echo ""
echo "Then use: ./youtube URL --ai-provider ollama --ai-model [model-name]"
