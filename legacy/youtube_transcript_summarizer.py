#!/usr/bin/env python3
import requests
import re
import sys
import argparse
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    if "youtube.com/watch?v=" in url:
        return parse_qs(urlparse(url).query)["v"][0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format")

def get_youtube_transcript(video_id):
    """Extract transcript using YouTube's internal API"""
    try:
        # Get transcript from YouTube's internal API
        transcript_url = f"https://video.google.com/timedtext?lang=en&v={video_id}"
        response = requests.get(transcript_url)
        
        if response.status_code == 200:
            return response.text
        else:
            try_alternative_languages(video_id)
    except:
        pass
    
    print("Could not extract transcript automatically.")
    print("Alternative: Use https://youtubedescription.com/ or install youtube-transcript-api")
    return None

def summarize_transcript(transcript_text, summary_ratio=0.2):
    """Simple extractive summarization"""
    import textwrap
    
    # Clean up transcript (remove XML tags)
    clean_text = re.sub(r'<[^>]+>', '', transcript_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', clean_text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s) > 20]
    
    if not sentences:
        return clean_text[:500] + "..."  # Simple truncation fallback
    
    # Extract key sentences (first 20% or first 5 sentences, whichever is smaller)
    num_sentences = max(3, int(len(sentences) * summary_ratio))
    key_sentences = sentences[:min(num_sentences, len(sentences))]
    
    summary = '. '.join(key_sentences) + '.'
    return summary

def main():
    parser = argparse.ArgumentParser(description='Extract and summarize YouTube video transcripts')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--output', '-o', help='Output file for transcript')
    parser.add_argument('--summary', '-s', help='Output file for summary')
    parser.add_argument('--ratio', '-r', type=float, default=0.2, help='Summary ratio (0.1-0.5)')
    
    args = parser.parse_args()
    
    try:
        video_id = extract_video_id(args.url)
        print(f"Extracting transcript for video ID: {video_id}")
        
        transcript = get_youtube_transcript(video_id)
        if not transcript:
            # Fallback: Tell user about alternative methods
            print("\nTo install the more robust youtube-transcript-api:")
            print("pip install youtube-transcript-api")
            print("python3 -c \"from youtube_transcript_api import YouTubeTranscriptApi; transcript = YouTubeTranscriptApi.get_transcript('" + video_id + "'); print(' '.join([t['text'] for t in transcript]))\"")
            return
        
        # Save transcript
        if args.output:
            with open(args.output, 'w') as f:
                f.write(transcript)
            print(f"Transcript saved to {args.output}")
        
        # Generate and save summary
        summary = summarize_transcript(transcript, args.ratio)
        if args.summary:
            with open(args.summary, 'w') as f:
                f.write(summary)
            print(f"Summary saved to {args.summary}")
        
        # Display results
        print("\n=== SUMMARY ===")
        print(summary)
        print(f"\nOriginal transcript length: {len(transcript)} characters")
        print(f"Summary length: {len(summary)} characters")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
