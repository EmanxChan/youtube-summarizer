#!/usr/bin/env python3
"""
Example test for Taddy API integration using their format.

Based on Taddy's example query:
query {
  getPodcastSeries(name:"The Daily"){
    uuid
    name
    itunesId
    description
    imageUrl
    totalEpisodesCount
  }
}
"""

import os
from taddy_integration import TaddyClient

def test_taddy_by_name():
    """Test searching for a podcast by name"""
    
    # Check if API key is set
    api_key = os.getenv('TADDY_API_KEY')
    if not api_key:
        print("❌ TADDY_API_KEY not set!")
        print("   Set it with: export TADDY_API_KEY='your_key_here'")
        return
    
    print("🧪 Testing Taddy API Integration\n")
    print("=" * 70)
    
    # Initialize client
    try:
        client = TaddyClient()
        print("✓ TaddyClient initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test 1: Search by podcast name (like their example)
    print("\n📝 Test 1: Search by podcast name")
    print("-" * 70)
    podcast_name = "The Daily"
    print(f"Searching for: '{podcast_name}'")
    
    try:
        series_uuid = client.search_podcast_by_name(podcast_name)
        if series_uuid:
            print(f"✓ Found series UUID: {series_uuid}")
            
            # Get an episode from this series
            episode_uuid = client._get_latest_episode_from_series(series_uuid)
            if episode_uuid:
                print(f"✓ Found episode UUID: {episode_uuid}")
                
                # Get transcript
                transcript_data = client.get_episode_transcript(episode_uuid)
                if transcript_data:
                    print(f"✓ Got transcript!")
                    print(f"  Title: {transcript_data['title']}")
                    print(f"  Length: {len(transcript_data['transcript'])} chars")
                    print(f"  Duration: {transcript_data.get('duration', 0)} seconds")
                else:
                    print("⚠️ No transcript available for this episode")
            else:
                print("⚠️ No episodes found for this series")
        else:
            print(f"⚠️ Podcast '{podcast_name}' not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Test with Apple Podcasts URL
    print("\n📝 Test 2: Apple Podcasts URL")
    print("-" * 70)
    apple_url = "https://podcasts.apple.com/us/podcast/the-daily/id1200361736"
    print(f"Testing URL: {apple_url}")
    
    try:
        result = client.get_transcript_by_url(apple_url, podcast_name="The Daily")
        if result:
            print(f"✓ Got transcript!")
            print(f"  Title: {result['title']}")
            print(f"  Length: {len(result['transcript'])} chars")
        else:
            print("⚠️ No transcript found via URL")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Show quota
    print("\n📊 Quota Status")
    print("-" * 70)
    metrics = client.get_metrics()
    print(f"Requests made: {metrics['requests_made']}")
    print(f"Quota remaining: {metrics['quota_remaining']}/{metrics['quota_limit']}")
    
    print("\n" + "=" * 70)
    print("✅ Test complete!")

if __name__ == "__main__":
    test_taddy_by_name()
