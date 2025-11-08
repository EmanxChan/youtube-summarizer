#!/usr/bin/env python3
import requests
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    if "youtube.com/watch?v=" in url:
        return parse_qs(urlparse(url).query)["v"][0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format")

def get_transcript_direct(video_id):
    """Try multiple approaches to get transcript"""
    
    # Approach 1: YouTube's timed text API
    endpoints = [
        f"https://video.google.com/timedtext?lang=en&v={video_id}",
        f"https://video.google.com/timedtext?lang=en&v={video_id}&fmt=srv1",
        f"https://video.google.com/timedtext?lang=en&v={video_id}&fmt=srv2",
        f"https://video.google.com/timedtext?lang=en&v={video_id}&fmt=srv3",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            if response.status_code == 200 and response.text.strip():
                return response.text
        except:
            continue
    
    return None

video_id = extract_video_id("https://www.youtube.com/watch?v=mgiC05hLOck")
print(f"Video ID: {video_id}")

transcript = get_transcript_direct(video_id)
if transcript:
    print(f"Transcript found (length: {len(transcript)} chars)")
    print("First 200 characters:")
    print(transcript[:200])
else:
    print("No transcript found")
