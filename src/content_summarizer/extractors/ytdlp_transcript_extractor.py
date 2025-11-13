#!/usr/bin/env python3
import sys
import argparse
import subprocess
import json
import re
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    if "youtube.com/watch?v=" in url:
        return parse_qs(urlparse(url).query)["v"][0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format")

def get_youtube_transcript_ytdlp(video_url):
    """Get transcript using yt-dlp"""
    try:
        # Use yt-dlp to get transcript
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            '--write-auto-sub',
            '--sub-langs', 'en,en-US',
            '--skip-download',
            '--sub-format', 'txt',
            '--print-json',
            video_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"yt-dlp error: {result.stderr}")
            return None
            
        # Parse the JSON output
        data = json.loads(result.stdout)
        
        # Check if subtitles were downloaded
        if data.get('subtitles') or data.get('automatic_captions'):
            # Look for subtitle files that were created
            video_id = data.get('id')
            subtitle_file = f"{video_id}.en.txt"
            
            try:
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    transcript = f.read()
                
                # Clean up the subtitle file
                import os
                os.remove(subtitle_file)
                
                return transcript
            except FileNotFoundError:
                print("Subtitle file not found")
                return None
        else:
            print("No subtitles found")
            return None
            
    except subprocess.TimeoutExpired:
        print("yt-dlp timed out")
        return None
    except json.JSONDecodeError:
        print("Failed to parse yt-dlp output")
        return None
    except Exception as e:
        print(f"Error with yt-dlp: {e}")
        return None

def clean_transcript(transcript_text):
    """Clean transcript text and remove timestamps"""
    if not transcript_text:
        return ""
    
    lines = transcript_text.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip timestamp lines (like "00:00:00,000 --> 00:00:03,000")
        if re.match(r'^\d{2}:\d{2}:\d{2}', line):
            continue
            
        # Skip empty lines
        if not line:
            continue
            
        # Remove remaining HTML tags
        line = re.sub(r'<[^>]+>', '', line)
        
        clean_lines.append(line)
    
    return ' '.join(clean_lines).strip()

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

def main():
    parser = argparse.ArgumentParser(description='Extract and summarize YouTube video transcripts using yt-dlp')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--words', '-w', type=int, default=150, help='Target word count for summary')
    
    args = parser.parse_args()
    
    try:
        print("🎬 YouTube Transcript Extractor (yt-dlp version)")
        print("=" * 50)
        print(f"Video: {args.url}")
        
        # Extract transcript
        print("📥 Extracting transcript using yt-dlp...")
        transcript = get_youtube_transcript_ytdlp(args.url)
        
        if not transcript:
            print("❌ Failed to get transcript using yt-dlp")
            print("Trying fallback method with youtube-transcript-api...")
            
            # Fallback to original method
            from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
            
            try:
                video_id = extract_video_id(args.url)
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                transcript = " ".join([item['text'] for item in transcript_data])
                transcript = clean_transcript(transcript)
            except Exception as e:
                print(f"❌ Fallback method also failed: {e}")
                sys.exit(1)
        
        if not transcript or len(transcript) < 50:
            print("❌ Transcript appears to be empty or too short")
            sys.exit(1)
        
        print(f"✅ Transcript extracted: {len(transcript)} characters")
        
        # Generate summary
        print("📝 Generating summary...")
        summary = summarize_transcript(transcript, args.words)
        
        # Display results
        print("\n" + "=" * 50)
        print("VIDEO SUMMARY")
        print("=" * 50)
        print(summary)
        
        transcript_word_count = len(transcript.split())
        summary_word_count = len(summary.split())
        
        print(f"\n📊 Statistics:")
        print(f"Transcript word count: {transcript_word_count}")
        print(f"Summary word count: {summary_word_count}")
        print(f"Reduction: {round((1 - summary_word_count/transcript_word_count) * 100, 1)}%")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
