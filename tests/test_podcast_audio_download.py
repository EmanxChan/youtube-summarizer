#!/usr/bin/env python3
"""
Test podcast audio download to diagnose issues.
"""
import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, '/Users/e.chan/content-summarizer/src')

# Set environment
os.environ['LISTEN_NOTES_API_KEY'] = '4e8b3079caaf4cd28bb70df528bc652c'
os.environ['PATH'] = f"/Users/e.chan/content-summarizer/bin:{os.environ['PATH']}"

from listen_notes_client import ListenNotesClient

def test_audio_download():
    """Test downloading audio from Listen Notes episode"""
    
    print("=" * 70)
    print("PODCAST AUDIO DOWNLOAD TEST")
    print("=" * 70)
    print()
    
    # Initialize client
    print("1️⃣ Initializing Listen Notes client...")
    client = ListenNotesClient()
    print("   ✓ Client initialized\n")
    
    # Search for The Daily
    print("2️⃣ Searching for 'The Daily' podcast...")
    podcasts = client.search_podcast("The Daily", limit=1)
    
    if not podcasts:
        print("   ❌ Podcast not found!")
        return
    
    podcast = podcasts[0]
    podcast_id = podcast['id']
    print(f"   ✓ Found: {podcast['title']}")
    print(f"   📊 Podcast ID: {podcast_id}")
    print(f"   📊 Total episodes: {podcast['total_episodes']}\n")
    
    # Get recent episodes
    print("3️⃣ Fetching recent episodes...")
    episodes = client.get_podcast_episodes(podcast_id, limit=5)
    
    if not episodes:
        print("   ❌ No episodes found!")
        return
    
    print(f"   ✓ Retrieved {len(episodes)} episodes\n")
    
    # Show first episode details
    episode = episodes[0]
    print("4️⃣ Episode Details:")
    print(f"   Title: {episode['title']}")
    print(f"   Episode ID: {episode['episode_id']}")
    print(f"   Published: {episode.get('pub_date_ms', 'N/A')}")
    
    audio_url = episode.get('audio_url')
    if audio_url:
        print(f"   ✓ Audio URL: {audio_url[:80]}...")
    else:
        print(f"   ❌ No audio URL available!")
        return
    
    print()
    
    # Test yt-dlp availability
    print("5️⃣ Checking yt-dlp...")
    import subprocess
    try:
        result = subprocess.run(['python3', '-m', 'yt_dlp', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   ✓ yt-dlp version: {result.stdout.strip()}")
        else:
            print(f"   ⚠️ yt-dlp check failed: {result.stderr}")
    except Exception as e:
        print(f"   ❌ yt-dlp not available: {e}")
        return
    
    print()
    
    # Test ffmpeg availability
    print("6️⃣ Checking ffmpeg...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   ✓ {version_line}")
        else:
            print(f"   ⚠️ ffmpeg check failed")
    except FileNotFoundError:
        print(f"   ❌ ffmpeg not in PATH")
        print(f"   💡 Trying from bin folder...")
        try:
            result = subprocess.run(['/Users/e.chan/content-summarizer/bin/ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            version_line = result.stdout.split('\n')[0]
            print(f"   ✓ {version_line}")
        except Exception as e:
            print(f"   ❌ ffmpeg also failed from bin: {e}")
            return
    except Exception as e:
        print(f"   ❌ ffmpeg error: {e}")
        return
    
    print()
    
    # Try to download audio
    print("7️⃣ Testing audio download with yt-dlp...")
    temp_dir = Path(tempfile.mkdtemp())
    audio_path = temp_dir / "test_podcast.mp3"
    
    print(f"   📂 Output: {audio_path}")
    print(f"   🌐 Downloading from: {audio_url[:60]}...")
    
    try:
        cmd = [
            'python3', '-m', 'yt_dlp',
            audio_url,
            '-o', str(audio_path),
            '--extract-audio',
            '--audio-format', 'mp3',
            '--no-playlist',
            '--verbose'  # More output for debugging
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f"\n   📤 yt-dlp exit code: {result.returncode}")
        
        if result.returncode == 0 and audio_path.exists():
            file_size = audio_path.stat().st_size
            print(f"   ✅ SUCCESS! Downloaded {file_size:,} bytes")
            print(f"   📁 File: {audio_path}")
        else:
            print(f"   ❌ FAILED - File not created")
            if result.stdout:
                print(f"\n   📝 STDOUT:\n{result.stdout[:500]}")
            if result.stderr:
                print(f"\n   ⚠️  STDERR:\n{result.stderr[:500]}")
    
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  TIMEOUT after 60 seconds")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    finally:
        # Cleanup
        try:
            if audio_path.exists():
                audio_path.unlink()
            temp_dir.rmdir()
        except:
            pass
    
    print()
    
    # Alternative: Try direct download with requests
    print("8️⃣ Testing direct HTTP download...")
    try:
        import requests
        print(f"   🌐 Requesting: {audio_url[:60]}...")
        
        response = requests.head(audio_url, timeout=10, allow_redirects=True)
        print(f"   📊 HTTP Status: {response.status_code}")
        print(f"   📦 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   📏 Content-Length: {response.headers.get('Content-Length', 'N/A')} bytes")
        
        if response.status_code == 200:
            print(f"   ✅ URL is accessible!")
            
            # Try actual download (first 1MB only)
            print(f"   📥 Downloading first 1MB...")
            response = requests.get(audio_url, stream=True, timeout=30)
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                downloaded += len(chunk)
                if downloaded > 1024 * 1024:  # 1MB
                    break
            
            print(f"   ✅ Downloaded {downloaded:,} bytes successfully!")
        else:
            print(f"   ❌ URL not accessible (status {response.status_code})")
    
    except Exception as e:
        print(f"   ❌ HTTP download failed: {e}")
    
    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    test_audio_download()
