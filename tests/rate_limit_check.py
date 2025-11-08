#!/usr/bin/env python3
"""
Simple script to check if YouTube rate limiting is still active
Tests with a popular video that definitely has transcripts
"""

import sys
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("❌ youtube-transcript-api not installed")
    sys.exit(1)

# Test with a popular video (Rick Astley - Never Gonna Give You Up)
TEST_VIDEO_ID = 'dQw4w9WgXcQ'

print("🔍 Checking YouTube rate limit status...")
print(f"📹 Test video: {TEST_VIDEO_ID}")
print()

try:
    transcript = YouTubeTranscriptApi.get_transcript(TEST_VIDEO_ID)
    print("✅ SUCCESS! Rate limiting is cleared")
    print(f"📊 Retrieved {len(transcript)} transcript segments")
    print("\n💡 You can now use enhanced_extractor.py to extract transcripts")
    sys.exit(0)

except Exception as e:
    error_str = str(e).lower()
    
    if '429' in error_str or 'too many requests' in error_str:
        print("❌ Still rate limited (429 error)")
        print("\n⏳ YouTube is still blocking transcript requests from your IP")
        print("\n💡 Solutions:")
        print("  1. Wait longer (try again in 24+ hours)")
        print("  2. Use a VPN to change your IP address")
        print("  3. Try from a different network (mobile hotspot, different WiFi)")
        print("  4. Use YouTube Data API v3 with an API key")
        sys.exit(1)
    else:
        print(f"⚠️  Unexpected error: {e}")
        print("\nThis might not be rate limiting. Try the video validator:")
        print("  python3 video_validator.py YOUR_VIDEO_URL")
        sys.exit(1)
