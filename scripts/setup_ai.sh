#!/bin/bash
# Setup script for AI-powered YouTube summarization

echo "🤖 YouTube Summarizer AI Setup"
echo "=============================="
echo ""

# Check if config directory exists
CONFIG_DIR="$HOME/.youtube_summarizer"
CONFIG_FILE="$CONFIG_DIR/config.json"

mkdir -p "$CONFIG_DIR"

# Install required packages
echo "📦 Installing AI dependencies..."
python3 -m pip install openai tiktoken anthropic python-dotenv --quiet

# Check if config exists
if [ -f "$CONFIG_FILE" ]; then
    echo "✓ Config file already exists at $CONFIG_FILE"
else
    echo "📝 Creating configuration..."
    echo ""
    echo "Choose your AI provider:"
    echo "1. OpenAI (GPT-4, GPT-3.5)"
    echo "2. Anthropic (Claude)"
    echo "3. DeepSeek (Cost-effective, powerful)"
    echo "4. Skip for now"
    read -p "Enter choice (1-4): " choice
    
    case $choice in
        1)
            read -p "Enter your OpenAI API key (starts with sk-): " api_key
            cat > "$CONFIG_FILE" <<EOF
{
  "openai_api_key": "$api_key",
  "default_provider": "openai",
  "default_model": "gpt-4o-mini"
}
EOF
            echo "✓ OpenAI configured successfully!"
            ;;
        2)
            read -p "Enter your Anthropic API key (starts with sk-ant-): " api_key
            cat > "$CONFIG_FILE" <<EOF
{
  "anthropic_api_key": "$api_key",
  "default_provider": "anthropic",
  "default_model": "claude-3-haiku-20240307"
}
EOF
            echo "✓ Anthropic configured successfully!"
            ;;
        3)
            read -p "Enter your DeepSeek API key: " api_key
            cat > "$CONFIG_FILE" <<EOF
{
  "deepseek_api_key": "$api_key",
  "default_provider": "deepseek",
  "default_model": "deepseek-chat"
}
EOF
            echo "✓ DeepSeek configured successfully!"
            ;;
        *)
            echo "⚠ Skipping AI setup. You can set it up later by:"
            echo "  - Setting environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY, or DEEPSEEK_API_KEY"
            echo "  - Creating config at: $CONFIG_FILE"
            echo "  - See example at: $CONFIG_FILE.example"
            ;;
    esac
fi

echo ""
echo "🚀 Setup complete!"
echo ""
echo "Usage examples:"
echo "  With AI (default):     ./youtube https://youtu.be/VIDEO_ID"
echo "  With specific model:   ./youtube https://youtu.be/VIDEO_ID --ai-model gpt-4"
echo "  Without AI:           ./youtube https://youtu.be/VIDEO_ID --ai-provider none"
echo ""
echo "To get an API key:"
echo "  OpenAI:    https://platform.openai.com/api-keys"
echo "  Anthropic: https://console.anthropic.com/settings/keys"
echo "  DeepSeek:  https://platform.deepseek.com/api_keys"
