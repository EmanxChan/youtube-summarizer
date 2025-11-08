#!/usr/bin/env python3
"""
Test script for Listen Notes API integration.
"""

import os
from listen_notes_client import ListenNotesClient
from podcast_cache import PodcastCache


def test_listen_notes():
    """Test Listen Notes API functionality"""
    
    print("=" * 80)
    print("🎙️  Listen Notes API Test")
    print("=" * 80)
    
    # Check for API key
    api_key = os.getenv('LISTEN_NOTES_API_KEY')
    if not api_key:
        print("❌ Error: LISTEN_NOTES_API_KEY environment variable not set")
        print("   Please set it with: export LISTEN_NOTES_API_KEY='your_key_here'")
        return
    
    # Initialize client
    print("\n1️⃣  Initializing Listen Notes client...")
    try:
        client = ListenNotesClient()
        print("   ✓ Client initialized successfully!")
    except Exception as e:
        print(f"   ❌ Failed to initialize client: {e}")
        return
    
    # Test 1: Search for podcast
    print("\n2️⃣  Testing podcast search...")
    try:
        results = client.search_podcast("The Daily", limit=3)
        if results:
            print(f"   ✓ Found {len(results)} podcast(s):")
            for i, podcast in enumerate(results, 1):
                print(f"      {i}. {podcast['title']}")
                print(f"         Publisher: {podcast['publisher']}")
                print(f"         Episodes: {podcast['total_episodes']}")
                print(f"         ID: {podcast['id']}")
        else:
            print("   ⚠️  No results found")
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
    
    # Test 2: Get podcast episodes
    print("\n3️⃣  Testing episode lookup...")
    try:
        # Use The Daily podcast ID (known podcast)
        podcast_id = "3302bc71139541baa46ecb27dbf6071a"  # The Daily
        episodes = client.get_podcast_episodes(podcast_id, limit=3)
        if episodes:
            print(f"   ✓ Found {len(episodes)} episode(s):")
            for i, ep in enumerate(episodes, 1):
                print(f"      {i}. {ep['title']}")
                print(f"         Duration: {ep['duration']} seconds")
                print(f"         Audio URL: {ep['audio_url'][:60]}..." if ep.get('audio_url') else "         No audio URL")
        else:
            print("   ⚠️  No episodes found")
    except Exception as e:
        print(f"   ❌ Episode lookup failed: {e}")
    
    # Test 3: Look up by URL
    print("\n4️⃣  Testing URL lookup...")
    
    test_urls = [
        "https://podcasts.apple.com/us/podcast/the-daily/id1200361736",
        "https://open.spotify.com/show/7Fht7tyxuZ4BrqHF9xc6vu",
    ]
    
    for test_url in test_urls:
        print(f"\n   Testing URL: {test_url}")
        try:
            result = client.get_episode_by_url(test_url)
            if result and result.get('audio_url'):
                print(f"   ✓ Found episode: {result['title']}")
                print(f"     Podcast: {result['podcast_title']}")
                print(f"     Duration: {result['duration']} seconds")
                print(f"     Audio URL: {result['audio_url'][:60]}...")
            else:
                print(f"   ⚠️  No episode found or no audio URL")
        except Exception as e:
            print(f"   ❌ URL lookup failed: {e}")
    
    # Test 4: Cache functionality
    print("\n5️⃣  Testing cache...")
    try:
        cache = PodcastCache(provider='listen_notes')
        stats = cache.get_stats()
        print(f"   ✓ Cache initialized")
        print(f"     Cache directory: {stats['cache_dir']}")
        print(f"     Cached entries: {stats['total_entries']}")
        print(f"     Total size: {stats['total_size_mb']:.2f} MB")
    except Exception as e:
        print(f"   ❌ Cache test failed: {e}")
    
    # Show API usage
    print("\n6️⃣  API Usage:")
    metrics = client.get_metrics()
    print(f"   Requests made: {metrics['requests_made']}")
    if metrics.get('quota_remaining'):
        print(f"   Quota remaining: {metrics['quota_remaining']}")
    
    print("\n" + "=" * 80)
    print("✅ Listen Notes API test complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_listen_notes()
