#!/bin/bash

echo "🤖 Ollama Installation Guide for Mac"
echo "===================================="
echo ""
echo "Ollama needs to be installed via the Mac app."
echo ""
echo "Steps:"
echo "1. Opening Ollama download page in your browser..."
echo "2. Download Ollama-darwin.zip"
echo "3. Unzip and move Ollama.app to Applications"
echo "4. Run Ollama.app (it will show in menu bar)"
echo ""

# Open download page
open https://ollama.ai/download/mac

echo "Waiting for you to install Ollama..."
echo "Press Enter once you've installed and launched Ollama.app"
read

# Check if ollama is now available
if command -v ollama &> /dev/null; then
    echo "✅ Ollama installed successfully!"
    echo ""
    echo "Now downloading the best model for YouTube summaries..."
    echo ""
    
    # Download llama3.2 - best balance of size and quality
    echo "📦 Downloading Llama 3.2 (3GB) - this will take a few minutes..."
    ollama pull llama3.2:3b
    
    echo ""
    echo "✅ Model downloaded successfully!"
    echo ""
    echo "Testing Ollama..."
    echo "---"
    echo "Test prompt: Summarize this: AI is transforming software development"
    echo ""
    ollama run llama3.2:3b "Summarize this in one sentence: AI is transforming software development by automating repetitive tasks and helping developers write better code faster."
    echo ""
    echo "---"
    echo "🎉 Ollama is ready to use!"
    echo ""
    echo "You can now use it with YouTube summarizer:"
    echo "  ./youtube https://youtu.be/VIDEO_ID --ai-provider ollama"
    echo ""
    echo "Or try other models:"
    echo "  ollama pull phi3       # Smaller (2GB), faster"
    echo "  ollama pull mistral    # Larger (4GB), better quality"
    echo "  ollama pull gemma2:2b  # Tiny (1.5GB), very fast"
    echo ""
else
    echo "⚠️  Ollama not detected. Please install it manually from:"
    echo "https://ollama.ai/download/mac"
    echo ""
    echo "After installing, run this script again or run:"
    echo "  ollama pull llama3.2:3b"
fi
