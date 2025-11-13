#!/usr/bin/env python3
"""
Quick validator to check if a video has transcripts available
Uses minimal requests to avoid triggering rate limits
"""

import argparse
import re
import sys
from typing import Optional

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    AVAILABLE = True
except ImportError:
    print("❌ youtube-transcript-api not installed")
    print("   Install: pip3 install youtube-transcript-api")
    sys.exit(1)


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def check_transcript_availability(video_url: str) -> dict:
    """Check if transcript is available for a video"""
    video_id = extract_video_id(video_url)
    
    if not video_id:
        return {
            'success': False,
            'error': 'Invalid video URL or ID',
            'video_id': None
        }
    
    try:
        # Try to list available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        available_transcripts = []
        for transcript in transcript_list:
            available_transcripts.append({
                'language': transcript.language,
                'language_code': transcript.language_code,
                'is_generated': transcript.is_generated,
                'is_translatable': transcript.is_translatable
            })
        
        return {
            'success': True,
            'video_id': video_id,
            'has_transcript': len(available_transcripts) > 0,
            'transcripts': available_transcripts
        }
    
    except Exception as e:
        error_str = str(e).lower()
        
        if '429' in error_str or 'too many requests' in error_str:
            return {
                'success': False,
                'error': 'Rate limited (429) - YouTube has temporarily blocked transcript access',
                'video_id': video_id,
                'rate_limited': True
            }
        elif 'transcript' in error_str or 'could not retrieve' in error_str:
            return {
                'success': True,
                'video_id': video_id,
                'has_transcript': False,
                'error': 'No transcript available for this video'
            }
        else:
            return {
                'success': False,
                'error': str(e),
                'video_id': video_id
            }


def main():
    parser = argparse.ArgumentParser(
        description='Check if a YouTube video has transcripts available',
        epilog='Example: %(prog)s https://youtu.be/VIDEO_ID'
    )
    parser.add_argument('video_url', help='YouTube video URL or video ID')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    result = check_transcript_availability(args.video_url)
    
    if args.json:
        import json
        print(json.dumps(result, indent=2))
        return
    
    # Pretty print
    print(f"\n📹 Video: {result.get('video_id', 'Unknown')}")
    print(f"🔗 URL: {args.video_url}\n")
    
    if not result['success']:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        if result.get('rate_limited'):
            print("\n💡 Solutions:")
            print("  • Wait 24+ hours for rate limit to reset")
            print("  • Try from different IP address (VPN, different network)")
            print("  • Use YouTube Data API v3 with API key")
        sys.exit(1)
    
    if result.get('has_transcript'):
        print("✅ Transcript available!\n")
        print("Available transcripts:")
        for transcript in result.get('transcripts', []):
            trans_type = "Auto-generated" if transcript['is_generated'] else "Manual"
            print(f"  • {transcript['language']} ({transcript['language_code']}) - {trans_type}")
    else:
        print("❌ No transcript available")
        print("\nThis video does not have captions/subtitles enabled.")


if __name__ == '__main__':
    main()
