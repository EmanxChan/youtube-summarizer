#!/usr/bin/env python3
import sys
import argparse
from urllib.parse import urlparse, parse_qs
import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

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
        # List available transcripts first
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English transcript first
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US'])
        except:
            # Fall back to any available transcript
            transcript = list(transcript_list)[0]
        
        # Fetch the transcript
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
    """Simple extractive summarization"""
    sentences = sent_tokenize(transcript)
    
    if not sentences:
        return transcript[:300] + "..."  # Truncation fallback
    
    # Select first few sentences until word count reached
    summary_sentences = []
    word_total = 0
    
    for sentence in sentences:
        sentence_words = len(word_tokenize(sentence))
        if word_total + sentence_words <= word_count:
            summary_sentences.append(sentence)
            word_total += sentence_words
        else:
            break
    
    if not summary_sentences:
        return sentences[0] if sentences else transcript[:100] + "..."
    
    return ' '.join(summary_sentences)

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
            print("Failed to get transcript. Please check the video URL.")
            print("Some videos may not have subtitles enabled.")
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
        print(f"\nOriginal transcript: {len(transcript)} characters")
        print(f"Summary: {len(summary)} characters")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
