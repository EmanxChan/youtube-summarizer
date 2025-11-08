#!/usr/bin/env python3
import sys
import time
import argparse
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
import random

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    if "youtube.com/watch?v=" in url:
        return parse_qs(urlparse(url).query)["v"][0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format")

def get_youtube_transcript(video_id):
    """Get transcript using youtube-transcript-api with fallbacks"""
    try:
        # Try older API method first
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine transcript segments
        full_transcript = " ".join([item['text'] for item in transcript_data])
        return full_transcript
        
    except AttributeError:
        # Try newer API method for newer versions
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to find English transcript
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
            
        except Exception as e:
            print(f"Alternative method failed: {e}")
            return None
            
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video")
        return None
    except NoTranscriptFound:
        print("No transcript found for this video")
        return None
    except Exception as e:
        error_msg = str(e).lower()
        if "too many requests" in error_msg or "429" in error_msg:
            raise Exception("RATE_LIMIT")
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

def retry_transcript_extraction(video_url, max_retries=10, wait_time=300, output_file=None, summary_file=None, word_count=150):
    """Retry transcript extraction with backoff strategy"""
    video_id = extract_video_id(video_url)
    print(f"Video ID: {video_id}")
    print(f"Attempting to extract transcript for: {video_url}")
    
    for attempt in range(1, max_retries + 1):
        print(f"\nAttempt {attempt}/{max_retries}")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            transcript = get_youtube_transcript(video_id)
            
            if transcript:
                # Clean transcript
                transcript = clean_transcript(transcript)
                
                if len(transcript) < 50:
                    print("Transcript appears to be very short or empty.")
                    continue
                
                print(f"✅ SUCCESS! Transcript length: {len(transcript)} characters")
                
                # Generate summary
                print("Generating summary...")
                summary = summarize_transcript(transcript, word_count)
                
                # Save files
                if output_file:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(transcript)
                    print(f"Transcript saved to {output_file}")
                
                if summary_file:
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        f.write(summary)
                    print(f"Summary saved to {summary_file}")
                
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
                
                print(f"\n🎉 Success after {attempt} attempt(s)!")
                return transcript, summary
            
        except Exception as e:
            if "RATE_LIMIT" in str(e):
                print("🚫 Rate limited by YouTube. Waiting...")
                
                if attempt < max_retries:
                    # Add some randomness to wait time
                    actual_wait = wait_time + random.randint(-60, 60)
                    
                    # Exponential backoff for longer waits
                    if attempt > 3:
                        actual_wait = int(actual_wait * (1 + (attempt - 3) * 0.2))
                    
                    print(f"Waiting {actual_wait} seconds ({actual_wait//60} minutes) before retry...")
                    
                    # Countdown timer
                    for remaining in range(actual_wait, 0, -1):
                        mins, secs = divmod(remaining, 60)
                        print(f"\rNext attempt in: {mins:02d}:{secs:02d}", end="")
                        time.sleep(1)
                    print("\nRetrying now...")
                else:
                    print("📅 Maximum retries reached. Try again later.")
            else:
                print(f"❌ Other error: {e}")
                if attempt < max_retries:
                    wait_time_short = 30  # Shorter wait for non-rate-limit errors
                    print(f"Waiting {wait_time_short} seconds before retry...")
                    time.sleep(wait_time_short)
    
    print(f"\n❌ Failed after {max_retries} attempts. The video may not have captions available.")
    return None, None

def main():
    parser = argparse.ArgumentParser(description='Retry YouTube transcript extraction with automatic retries')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--output', '-o', help='Output file for transcript')
    parser.add_argument('--summary', '-s', help='Output file for summary')
    parser.add_argument('--words', '-w', type=int, default=150, help='Target word count for summary')
    parser.add_argument('--retries', '-r', type=int, default=10, help='Maximum number of retries')
    parser.add_argument('--wait', type=int, default=300, help='Initial wait time in seconds (default: 5 minutes)')
    
    args = parser.parse_args()
    
    try:
        retry_transcript_extraction(
            args.url, 
            max_retries=args.retries, 
            wait_time=args.wait,
            output_file=args.output,
            summary_file=args.summary,
            word_count=args.words
        )
        
    except KeyboardInterrupt:
        print("\n⏹️ Retry process stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
