#!/usr/bin/env python3
import sys
import argparse
from urllib.parse import urlparse, parse_qs
import re
import requests

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    if "youtube.com/watch?v=" in url:
        return parse_qs(urlparse(url).query)["v"][0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format")

def get_youtube_transcript(video_id):
    """Get transcript using YouTube's internal API"""
    try:
        # Try English transcript first
        url = f"https://video.google.com/timedtext?lang=en&v={video_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200 and response.text.strip():
            return response.text
    except:
        pass
    
    # Try auto-generated transcript
    try:
        url = f"https://video.google.com/timedtext?lang=en&v={video_id}&fmt=srv1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200 and response.text.strip():
            return response.text
    except:
        pass
    
    return None

def clean_transcript(transcript_text):
    """Clean transcript by removing XML tags and formatting"""
    # Remove XML tags
    clean_text = re.sub(r'<[^>]+>', '', transcript_text)
    
    # Clean up multiple spaces and newlines
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Remove any remaining XML entities
    clean_text = re.sub(r'&amp;quot;|&quot;|&apos;|&lt;|&gt;|&amp;', '', clean_text)
    
    return clean_text.strip()

def summarize_text(text, word_limit=150):
    """Simple extractive summarization by word count"""
    if word_limit >= len(text.split()):
        return text
    
    words = text.split()
    
    # Find a good cutoff point near a sentence ending
    for i in range(len(words)-1, -1, -1):
        if i <= word_limit and (words[i].endswith('.') or words[i].endswith('!') or words[i].endswith('?')):
            summary = ' '.join(words[:i+1])
            if len(summary.split()) >= word_limit * 0.7:  # At least 70% of target
                return summary + '...'
    
    # Fallback: just truncate at word limit
    summary = ' '.join(words[:word_limit])
    return summary + '...'

def main():
    parser = argparse.ArgumentParser(description='Extract and summarize YouTube video transcripts')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--output', '-o', help='Output file for transcript')
    parser.add_argument('--summary', '-s', help='Output file for summary')
    parser.add_argument('--words', '-w', type=int, default=150, help='Target word count for summary')
    
    args = parser.parse_args()
    
    try:
        # Extract video ID
        video_id = extract_video_id(args.url)
        print(f"Processing video ID: {video_id}")
        
        # Get transcript
        print("Fetching transcript...")
        transcript_raw = get_youtube_transcript(video_id)
        
        if not transcript_raw:
            print("No transcript found for this video.")
            print("This video may not have subtitles available.")
            sys.exit(1)
        
        # Clean transcript
        transcript = clean_transcript(transcript_raw)
        
        if len(transcript) < 50:
            print("Transcript appears to be empty or mostly XML tags.")
            print("This video may not have proper subtitles.")
            sys.exit(1)
        
        print(f"Transcript length: {len(transcript)} characters")
        
        # Save transcript
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"Transcript saved to {args.output}")
        
        # Generate summary
        print("Generating summary...")
        summary = summarize_text(transcript, args.words)
        
        # Save summary
        if args.summary:
            with open(args.summary, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"Summary saved to {args.summary}")
        
        # Display results
        print("\n" + "="*60)
        print("VIDEO SUMMARY")
        print("="*60)
        print(summary)
        
        transcript_word_count = len(transcript.split())
        summary_word_count = len(summary.split())
        
        print(f"\nTranscript word count: {transcript_word_count}")
        print(f"Summary word count: {summary_word_count}")
        print(f"Reduction: {round((1 - summary_word_count/transcript_word_count) * 100, 1)}%")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
