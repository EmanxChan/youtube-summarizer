#!/bin/bash
# Setup script for /youtube command
# Adds alias to your shell configuration

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
YOUTUBE_SCRIPT="$SCRIPT_DIR/youtube"

echo "🔧 Setting up /youtube command..."
echo ""

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_NAME="zsh"
    CONFIG_FILE="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_NAME="bash"
    CONFIG_FILE="$HOME/.bashrc"
else
    SHELL_NAME=$(basename "$SHELL")
    if [ "$SHELL_NAME" = "zsh" ]; then
        CONFIG_FILE="$HOME/.zshrc"
    else
        CONFIG_FILE="$HOME/.bashrc"
    fi
fi

echo "Detected shell: $SHELL_NAME"
echo "Config file: $CONFIG_FILE"
echo ""

# Create alias command
ALIAS_LINE="alias /youtube='$YOUTUBE_SCRIPT'"

# Check if alias already exists
if [ -f "$CONFIG_FILE" ] && grep -q "alias /youtube=" "$CONFIG_FILE"; then
    echo "⚠️  Alias already exists in $CONFIG_FILE"
    echo ""
    echo "Current line:"
    grep "alias /youtube=" "$CONFIG_FILE"
    echo ""
    read -p "Do you want to update it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    # Remove old alias
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' '/alias \/youtube=/d' "$CONFIG_FILE"
    else
        sed -i '/alias \/youtube=/d' "$CONFIG_FILE"
    fi
fi

# Add alias to config file
echo "" >> "$CONFIG_FILE"
echo "# YouTube transcript extractor" >> "$CONFIG_FILE"
echo "$ALIAS_LINE" >> "$CONFIG_FILE"

echo "✅ Alias added to $CONFIG_FILE"
echo ""
echo "To activate immediately, run:"
echo "  source $CONFIG_FILE"
echo ""
echo "Or restart your terminal."
echo ""
echo "Usage examples:"
echo '  /youtube "https://youtu.be/VIDEO_ID"'
echo '  /youtube "https://youtu.be/VIDEO_ID" --words 200'
echo '  /youtube "search query"'
echo ""
echo "Files will be saved to: ~/Documents/YouTube videos/"
