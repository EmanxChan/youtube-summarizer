#!/usr/bin/env python3
import sys
import argparse
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    if "youtube.com/watch?v=" in url:
        return parse_qs(urlparse(url).query)["v"][0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format")

def get_youtube_transcript(video_id):
    """Get transcript using youtube-transcript-api"""
    try:
        # Get available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to find an English transcript first, otherwise use any transcript
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-gb'])
            transcript_data = transcript.fetch()
        except:
            # Use first available transcript
            available_transcripts = list(transcript_list)
            if not available_transcripts:
                raise NoTranscriptFound(video_id)
            
            transcript = available_transcripts[0]
            transcript_data = transcript.fetch()
        
        # Combine transcript segments
        full_transcript = " ".join([item['text'] for item in transcript_data])
        return full_transcript
        
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video")
        return None
    except NoTranscriptFound:
        print("No transcript found for this video")
        return None
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def summarize_transcript(transcript, word_count=150):
    """Simple extractive summarization by word count"""
    words = transcript.split()
    
    if len(words) <= word_count:
        return transcript
    
    # Try to end at a sentence boundary
    summary_words = words[:word_count]
    for i in range(word_count - 1, max(word_count - 20, 0), -1):
        if summary_words[i].endswith(('.', '!', '?')):
            summary_words = summary_words[:i+1]
            break
    
    summary = ' '.join(summary_words)
    return summary + '...' if not summary.endswith(('.', '!', '?')) else summary

def clean_transcript(transcript_text):
    """Clean transcript text"""
    # Remove any remaining XML tags or special characters
    text = re.sub(r'<[^>]+>', '', transcript_text)
    text = re.sub(r'&[^;]+;', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

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
        transcript = get_youtube_transcript(video_id)
        
        if not transcript:
            print("Failed to get transcript. This video may not have subtitles available.")
            sys.exit(1)
        
        # Clean transcript
        transcript = clean_transcript(transcript)
        
        if len(transcript) < 50:
            print("Transcript appears to be very short or empty.")
            sys.exit(1)
        
        print(f"Transcript length: {len(transcript)} characters")
        
        # Save transcript
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"Transcript saved to {args.output}")
        
        # Generate summary
        print("Generating summary...")
        summary = summarize_transcript(transcript, args.words)
        
        # Save summary
        if args.summary:
            with open(args.summary, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"Summary saved to {args.summary}")
        
        # Display results
        print("\n" + "="*50)
        print("VIDEO SUMMARY")
        print("="*50)
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
