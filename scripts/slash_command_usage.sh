#!/bin/bash
# Usage examples for the YouTube slash command

# Display help
echo "=== Help ===" 
python3 droid_slash_cli.py /help
echo ""

# Example 1: URL with default word count (150 words)
echo "=== Example 1: Process URL with default summary length ==="
echo "python3 droid_slash_cli.py /youtube \"https://www.youtube.com/watch?v=VIDEO_ID\""
echo ""

# Example 2: URL with custom word count
echo "=== Example 2: Process URL with custom summary length ==="
echo "python3 droid_slash_cli.py /youtube \"https://www.youtube.com/watch?v=VIDEO_ID\" --words 200"
echo ""

# Example 3: Search query with default word count
echo "=== Example 3: Search and process video ==="
echo "python3 droid_slash_cli.py /youtube \"Python programming tutorial\""
echo ""

# Example 4: Short URL format
echo "=== Example 4: Short URL format ==="
echo "python3 droid_slash_cli.py /youtube \"https://youtu.be/VIDEO_ID\" --words 100"
echo ""

# Note about output
echo "=== Output Location ==="
echo "Transcript and summary files are saved to: ~/Documents/YouTube videos/"
echo "Files are named based on video title (or video ID if title unavailable)"
echo "If files exist, numeric suffixes are added (_1, _2, etc.)"
