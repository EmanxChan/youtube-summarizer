#!/usr/bin/env python3
"""
Quick test retry script for user's specific video
"""

import subprocess
import time
import sys

def main():
    video_url = "https://www.youtube.com/watch?v=mgiC05hLOck"
    
    print("🎬 YouTube Transcript Extractor with Auto-Retry")
    print("=" * 50)
    print(f"Video: {video_url}")
    print("This will keep retrying until transcript is extracted or max attempts reached.")
    print("Press Ctrl+C to stop at any time.")
    print()
    
    try:
        subprocess.run([
            "python3", "/Users/e.chan/retry_transcript.py",
            video_url,
            "-o", "transcript.txt",
            "-s", "summary.txt",
            "--words", "200",
            "--retries", "15",  # More retries
            "--wait", "180"     # Start with 3 minutes
        ])
    except KeyboardInterrupt:
        print("\n⏹️ Process stopped by user.")
    except Exception as e:
        print(f"Error running retry script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
