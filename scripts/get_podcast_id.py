#!/usr/bin/env python3
"""
Quick tool to get podcast ID from Listen Notes
Usage: python3 get_podcast_id.py "Podcast Name"
"""
import sys
from listen_notes_client import ListenNotesClient

if len(sys.argv) < 2:
    print("\n📋 Podcast ID Lookup Tool")
    print("=" * 60)
    print("\nUsage: python3 get_podcast_id.py 'Podcast Name'")
    print("\nExamples:")
    print("  python3 get_podcast_id.py 'Huberman Lab'")
    print("  python3 get_podcast_id.py 'The Daily'")
    print("  python3 get_podcast_id.py 'How I Built This'")
    print()
    sys.exit(1)

podcast_name = ' '.join(sys.argv[1:])

try:
    client = ListenNotesClient()
except ValueError as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Make sure LISTEN_NOTES_API_KEY is set:")
    print('   export LISTEN_NOTES_API_KEY="your_key_here"')
    print()
    sys.exit(1)

print(f"\n🔍 Searching Listen Notes for: {podcast_name}")
print("=" * 60)

try:
    results = client.search_podcast(podcast_name, limit=5)
    
    if not results:
        print("\n❌ No podcasts found")
        print("\n💡 Try:")
        print("  - Different spelling")
        print("  - Fewer/more words")
        print("  - Check the podcast exists on major platforms")
        print()
        sys.exit(1)
    
    print(f"\n✅ Found {len(results)} podcast(s):\n")
    
    for i, podcast in enumerate(results, 1):
        print(f"{i}. {podcast['title']}")
        print(f"   📋 ID: {podcast['id']}")
        print(f"   👤 Publisher: {podcast['publisher']}")
        print(f"   📊 Episodes: {podcast['total_episodes']}")
        if podcast.get('rss_url'):
            print(f"   🔗 RSS: {podcast['rss_url'][:60]}...")
        print()
    
    # Show top result prominently
    top_id = results[0]['id']
    print("=" * 60)
    print(f"🎯 Top Result ID: {top_id}")
    print("=" * 60)
    print("\n💡 Usage in Python:")
    print(f'   podcast_id = "{top_id}"')
    print(f'   episodes = client.get_podcast_episodes(podcast_id)')
    print()
    
    # Show API usage
    metrics = client.get_metrics()
    print(f"📊 API Usage: {metrics['requests_made']} requests")
    if metrics.get('quota_remaining'):
        print(f"   Quota remaining: {metrics['quota_remaining']}")
    print()

except Exception as e:
    print(f"\n❌ Error: {e}")
    print()
    sys.exit(1)
