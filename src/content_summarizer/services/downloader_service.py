import sys
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

class DownloaderService:
    """Service for downloading content from various sources (YouTube, Twitter, Podcasts)."""

    def extract_video_id(self, url_or_id: str) -> str:
        """Extract YouTube video ID from URL or return as-is."""
        if "youtube.com/watch?v=" in url_or_id:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url_or_id)
            query = parse_qs(parsed.query)
            if "v" in query:
                return query["v"][0]
        elif "youtu.be/" in url_or_id:
            return url_or_id.split("youtu.be/")[1].split("?")[0]
        
        # Simple regex check for ID format (alphanumeric + _ -)
        import re
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
            return url_or_id
            
        raise ValueError(f"Invalid YouTube URL or video ID format: {url_or_id}")

    def download_podcast_audio(self, audio_url: str, output_path: Path) -> bool:
        """Download podcast audio using yt-dlp."""
        try:
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                audio_url,
                '-o', str(output_path),
                '--extract-audio',
                '--audio-format', 'mp3',
                '--no-playlist'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            return result.returncode == 0 and output_path.exists()
            
        except Exception as e:
            print(f"  ⚠️ Audio download failed: {e}")
            return False

    def download_twitter_video(self, twitter_url: str) -> Tuple[Optional[str], Optional[str]]:
        """Download video from Twitter/X URL."""
        import tempfile
        
        try:
            temp_dir = Path(tempfile.mkdtemp())
            output_template = str(temp_dir / "twitter_video.%(ext)s")
            
            print(f"  📥 Downloading Twitter video...")
            
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                twitter_url,
                '-o', output_template,
                '--format', 'best[ext=mp4]/best',
                '--no-playlist',
                '--quiet',
                '--no-warnings'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                # Find the downloaded file
                video_files = list(temp_dir.glob("twitter_video.*"))
                if video_files:
                    video_path = video_files[0]
                    print(f"  ✓ Video downloaded: {video_path.name}")
                    
                    # Get title
                    title_cmd = [
                        sys.executable, '-m', 'yt_dlp',
                        twitter_url,
                        '--get-title',
                        '--no-warnings'
                    ]
                    title_result = subprocess.run(title_cmd, capture_output=True, text=True, timeout=10)
                    title = title_result.stdout.strip() if title_result.returncode == 0 else "Twitter Video"
                    
                    return str(video_path), title
            
            print(f"  ⚠️ Download failed: {result.stderr}")
            return None, None
            
        except Exception as e:
            print(f"  ⚠️ Download error: {e}")
            return None, None

    def find_youtube_mirror(self, podcast_title: str, episode_title: Optional[str] = None) -> Optional[str]:
        """Search for podcast episode on YouTube."""
        import re
        
        try:
            search_query = podcast_title if podcast_title else ""
            if episode_title:
                if search_query and episode_title.lower() != podcast_title.lower():
                    search_query = f"{podcast_title} {episode_title}"
                elif not search_query:
                    search_query = episode_title
            
            if not search_query:
                return None
            
            # Clean up
            search_query = re.sub(r'Episode \d+', '', search_query)
            search_query = re.sub(r'#\d+', '', search_query)
            search_query = search_query.strip()
            
            print(f"  🔍 YouTube search: \"{search_query}\"")
            
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                f'ytsearch1:{search_query}',
                '--print-json',
                '--skip-download'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            
            if result.returncode != 0:
                return None
            
            video_data = json.loads(result.stdout.strip())
            video_id = video_data.get('id')
            video_title = video_data.get('title', '')
            
            if not video_title:
                return None
            
            print(f"  📺 Found: {video_title}")
            
            # Validate match
            video_title_lower = video_title.lower()
            
            if podcast_title:
                podcast_core = podcast_title.lower()
                for common in ['podcast', 'the', 'show', 'with']:
                    podcast_core = podcast_core.replace(common, '')
                podcast_core = podcast_core.strip()
                
                if podcast_core and podcast_core not in video_title_lower:
                    print(f"  ⚠️ YouTube video doesn't match podcast '{podcast_title}' - skipping")
                    return None
            
            if episode_title:
                episode_words = set(episode_title.lower().split())
                video_words = set(video_title_lower.split())
                common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                               'of', 'with', 'by', 'from', 'how', 'why', 'what', 'dr', 'essentials',
                               'episode', 'part', 'vol', 'volume'}
                episode_words = episode_words - common_words
                video_words = video_words - common_words
                
                if len(episode_words) > 0:
                    overlap = len(episode_words & video_words) / len(episode_words)
                    if overlap < 0.5:
                        print(f"  ⚠️ YouTube video overlap too low: {overlap:.0%} - skipping")
                        return None
            
            print(f"  ✓ YouTube match validated")
            return video_id
            
        except Exception as e:
            print(f"  ⚠️ Could not find YouTube mirror: {e}")
            return None
