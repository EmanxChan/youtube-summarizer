#!/usr/bin/env python3
"""Find lightweight test content for benchmarking"""

import sys
import os

# Suggested lightweight YouTube videos (tech/educational, ~10 min)
YOUTUBE_CANDIDATES = [
    "https://www.youtube.com/watch?v=0qo78R_yYFA",  # Docker in 100 Seconds
    "https://www.youtube.com/watch?v=gd6rYPfTjgk",  # Kubernetes in 100 Seconds  
    "https://www.youtube.com/watch?v=tc4ROCJYbm0",  # TypeScript in 100 Seconds
]

def check_youtube_videos():
    """Check YouTube video availability"""
    from youtube_transcript_api import YouTubeTranscriptApi
    
    print("YouTube Video Candidates:")
    print("="*60)
    
    valid_videos = []
    
    for url in YOUTUBE_CANDIDATES:
        video_id = url.split('v=')[1].split('&')[0]
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['en'])
            data = transcript.fetch()
            duration = max([item['start'] + item['duration'] for item in data]) if data else 0
            word_count = sum(len(item['text'].split()) for item in data)
            
            print(f"✓ {url}")
            print(f"  Duration: {duration/60:.1f} minutes")
            print(f"  Segments: {len(data)}")
            print(f"  Word count: {word_count:,}")
            print()
            
            valid_videos.append({
                'url': url,
                'video_id': video_id,
                'duration': duration,
                'word_count': word_count
            })
            
        except Exception as e:
            print(f"✗ {url}")
            print(f"  Error: {e}")
            print()
    
    return valid_videos

def find_podcast_episode():
    """Find a lightweight podcast episode using Listen Notes"""
    try:
        from listen_notes_client import ListenNotesClient
        
        api_key = os.getenv('LISTEN_NOTES_API_KEY')
        if not api_key:
            print("⚠️  Listen Notes API key not found (LISTEN_NOTES_API_KEY)")
            print("   Skipping podcast search...")
            return None
        
        client = ListenNotesClient()
        
        print("\nSearching for podcast episodes...")
        print("="*60)
        
        # Search for tech podcasts with shorter episodes
        results = client.search_podcast("technology explained", limit=5)
        
        if not results:
            print("No podcasts found")
            return None
        
        print(f"Found {len(results)} podcasts, checking episodes...\n")
        
        for i, podcast in enumerate(results[:3], 1):
            try:
                episodes = client.get_podcast_episodes(podcast['id'], limit=1)
                if episodes:
                    ep = episodes[0]
                    duration_min = ep['duration'] // 60 if ep['duration'] else 0
                    
                    if 5 <= duration_min <= 20:  # Look for 5-20 min episodes
                        print(f"✓ Found suitable episode:")
                        print(f"  Podcast: {ep['podcast_title']}")
                        print(f"  Episode: {ep['title']}")
                        print(f"  Duration: {duration_min} minutes")
                        if ep.get('audio_url'):
                            print(f"  Audio URL: {ep['audio_url'][:60]}...")
                        print()
                        return ep
            except Exception as e:
                print(f"  Error checking podcast {i}: {e}")
                continue
        
        print("No suitable episodes found (looking for 5-20 min duration)")
        return None
        
    except ImportError:
        print("⚠️  listen_notes_client not available")
        print("   Skipping podcast search...")
        return None
    except Exception as e:
        print(f"⚠️  Podcast search error: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("Finding Test Content for OpenRouter Benchmark")
    print("="*60 + "\n")
    
    # Check YouTube videos
    videos = check_youtube_videos()
    
    if videos:
        print(f"\n✅ Found {len(videos)} valid YouTube videos")
        best_video = min(videos, key=lambda v: v['duration'])
        print(f"\n📹 Recommended YouTube video:")
        print(f"   {best_video['url']}")
        print(f"   Duration: {best_video['duration']/60:.1f} min")
        print(f"   Words: {best_video['word_count']:,}")
    else:
        print("\n❌ No valid YouTube videos found")
    
    # Try to find podcast
    episode = find_podcast_episode()
    
    if episode:
        print(f"\n✅ Found suitable podcast episode")
        print(f"\n🎙️  Recommended podcast:")
        print(f"   {episode['title']}")
        print(f"   Duration: {episode['duration']//60} min")
    else:
        print(f"\n⚠️  No podcast found - will use YouTube only for testing")
    
    print("\n" + "="*60)
    print("Content selection complete!")
    print("="*60 + "\n")
    
    return videos, episode

if __name__ == "__main__":
    main()
