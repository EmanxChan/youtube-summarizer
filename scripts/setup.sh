#!/bin/bash
# Setup script for Content Summarizer on macOS/Linux

# Exit on error
set -e

echo "🚀 Starting Content Summarizer Setup..."

# Determine project root (one level up from scripts/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

cd "$PROJECT_ROOT"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install it from python.org"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment (venv)..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists."
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found."
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "📝 PLEASE EDIT .env AND ADD YOUR GROQ_API_KEY!"
    open -e .env 2>/dev/null || echo "   (Could not open editor automatically. Please open .env manually)"
else
    echo "✅ .env file detected."
fi

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "To run the app, use:"
echo "  ./scripts/run.sh"
echo ""
