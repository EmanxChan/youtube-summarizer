#!/bin/bash

# Example usage of the YouTube transcript summarizer

echo "=== YouTube Transcript Summarizer Usage Examples ==="
echo ""

# Basic usage - extract transcript and display summary
echo "1. Basic usage (displays only summary):"
echo "python3 advanced_youtube_summarizer.py 'https://youtube.com/watch?v=dQw4w9WgXcQ'"
echo ""

# Save transcript and summary to files
echo "2. Save transcript and summary to files:"
echo "python3 advanced_youtube_summarizer.py 'https://youtube.com/watch?v=dQw4w9WgXcQ' -o transcript.txt -s summary.txt"
echo ""

# Customize summary length
echo "3. Shorter summary (50 words):"
echo "python3 advanced_youtube_summarizer.py 'https://youtube.com/watch?v=dQw4w9WgXcQ' -w 50"
echo ""

# More detailed summary (10 sentences using extractive method)
echo "4. More detailed summary:"
echo "python3 advanced_youtube_summarizer.py 'https://youtube.com/watch?v=dQw4w9WgXcQ' -n 10 -m extractive"
echo ""

# Simple summarization method
echo "5. Simple word-based summarization:"
echo "python3 advanced_youtube_summarizer.py 'https://youtube.com/watch?v=dQw4w9WgXcQ' -m simple -w 200"
echo ""

echo "Replace the YouTube URL with any video you want to analyze!"
