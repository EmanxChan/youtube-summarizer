import re
import json
from typing import Optional, Tuple, Dict, Any, List
import requests
from bs4 import BeautifulSoup

class TranscriptService:
    """Service for parsing and extracting transcripts from various formats."""

    def parse_vtt(self, vtt_content: str) -> str:
        """Parse WebVTT format transcript."""
        lines = vtt_content.split('\n')
        transcript = []
        
        for line in lines:
            line = line.strip()
            if (line and 
                not line.startswith('WEBVTT') and 
                not line.startswith('NOTE') and
                not '-->' in line and
                not line.isdigit()):
                line = re.sub(r'<[^>]+>', '', line)
                transcript.append(line)
        
        return ' '.join(transcript)

    def parse_srt(self, srt_content: str) -> str:
        """Parse SRT format transcript."""
        lines = srt_content.split('\n')
        transcript = []
        
        for line in lines:
            line = line.strip()
            if (line and 
                not line.isdigit() and
                not '-->' in line):
                transcript.append(line)
        
        return ' '.join(transcript)

    def parse_html(self, html_content: str) -> str:
        """Parse HTML transcript."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for element in soup.find_all(['script', 'style']):
                element.decompose()
            return soup.get_text(separator=' ', strip=True)
        except:
            return html_content

    def parse_json(self, json_content: str) -> str:
        """Parse JSON transcript format."""
        try:
            data = json.loads(json_content)
            if isinstance(data, list):
                texts = [item.get('text', '') for item in data if 'text' in item]
                return ' '.join(texts)
            elif 'segments' in data:
                texts = [seg.get('text', '') for seg in data['segments']]
                return ' '.join(texts)
            elif 'text' in data:
                return data['text']
            return str(data)
        except:
            return json_content

    def auto_parse(self, content: str) -> str:
        """Try to auto-detect and parse transcript format."""
        if 'WEBVTT' in content[:100]:
            return self.parse_vtt(content)
        elif '-->' in content[:500]:
            return self.parse_srt(content)
        elif content.strip().startswith('{') or content.strip().startswith('['):
            try:
                return self.parse_json(content)
            except:
                pass
        return self.parse_html(content)

    def fetch_from_rss(self, rss_url: str, episode_url: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Fetch transcript from RSS feed using Podcasting 2.0 namespace."""
        try:
            import feedparser
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                return None, None
            
            target_episode = None
            if episode_url:
                for entry in feed.entries:
                    if episode_url in entry.get('link', '') or episode_url in entry.get('id', ''):
                        target_episode = entry
                        break
            
            if not target_episode:
                target_episode = feed.entries[0]
            
            episode_title = target_episode.get('title', 'Unknown Episode')
            
            transcript_url = None
            transcript_type = None
            
            if hasattr(target_episode, 'podcast_transcript'):
                transcript_info = target_episode.podcast_transcript
                if isinstance(transcript_info, list):
                    transcript_info = transcript_info[0]
                transcript_url = transcript_info.get('url') or transcript_info.get('href')
                transcript_type = transcript_info.get('type')
            
            if not transcript_url:
                for link in target_episode.get('links', []):
                    if 'transcript' in link.get('type', '').lower():
                        transcript_url = link.get('href')
                        transcript_type = link.get('type')
                        break
            
            if not transcript_url:
                return episode_title, None
            
            response = requests.get(transcript_url, timeout=15)
            response.raise_for_status()
            
            if transcript_type and 'vtt' in transcript_type.lower():
                transcript_text = self.parse_vtt(response.text)
            elif transcript_type and 'srt' in transcript_type.lower():
                transcript_text = self.parse_srt(response.text)
            elif transcript_type and 'html' in transcript_type.lower():
                transcript_text = self.parse_html(response.text)
            elif transcript_type and 'json' in transcript_type.lower():
                transcript_text = self.parse_json(response.text)
            else:
                transcript_text = self.auto_parse(response.text)
            
            return episode_title, transcript_text
            
        except Exception as e:
            print(f"  ⚠️ Could not extract transcript from RSS: {e}")
            return None, None
