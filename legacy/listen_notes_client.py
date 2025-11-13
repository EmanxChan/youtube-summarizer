#!/usr/bin/env python3
"""
Listen Notes API integration for podcast metadata and audio URLs.
API Docs: https://www.listennotes.com/api/docs/
"""

import os
import re
import requests
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs


class ListenNotesClient:
    """Client for Listen Notes Podcast API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Listen Notes API client.
        
        Args:
            api_key: Listen Notes API key (or set LISTEN_NOTES_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('LISTEN_NOTES_API_KEY')
        
        if not self.api_key:
            raise ValueError("Listen Notes API key required. Set LISTEN_NOTES_API_KEY env var.")
        
        self.base_url = "https://listen-api.listennotes.com/api/v2"
        self.headers = {
            "X-ListenAPI-Key": self.api_key
        }
        self.requests_made = 0
        self.quota_remaining = None
    
    def get_episode_by_url(self, podcast_url: str) -> Optional[Dict]:
        """
        Get episode metadata and audio URL from podcast URL.
        Supports Apple Podcasts, Spotify, and RSS URLs.
        
        Args:
            podcast_url: Apple Podcasts, Spotify, or RSS URL
            
        Returns:
            Dict with {audio_url, title, description, duration, podcast_title} or None
        """
        # Parse URL to get identifiers
        parsed = self._parse_podcast_url(podcast_url)
        
        if not parsed:
            print(f"  ℹ️ Listen Notes: Unsupported URL format")
            return None
        
        # Try to find episode by URL
        episode_data = None
        
        # For Apple Podcasts episode URLs
        if parsed['platform'] == 'apple_podcasts' and parsed.get('episode_id'):
            episode_data = self._lookup_by_apple_id(parsed['show_id'], parsed['episode_id'])
        
        # For Spotify episode URLs
        elif parsed['platform'] == 'spotify' and parsed.get('episode_id'):
            episode_data = self._lookup_by_spotify_id(parsed['episode_id'])
        
        # For RSS or show-only URLs, try search
        elif parsed.get('show_id') or parsed.get('rss_url'):
            # Use the URL directly with Listen Notes search
            episode_data = self._search_by_url(podcast_url)
        
        return episode_data
    
    def search_podcast(self, query: str, limit: int = 5) -> list:
        """
        Search for podcasts by name.
        
        Args:
            query: Search query (podcast name)
            limit: Max results to return (default 5)
            
        Returns:
            List of podcast dicts with metadata
        """
        try:
            response = self._api_request(
                'GET',
                '/search',
                params={
                    'q': query,
                    'type': 'podcast',
                    'only_in': 'title',
                    'page_size': limit
                }
            )
            
            results = response.get('results', [])
            podcasts = []
            
            for result in results:
                podcasts.append({
                    'id': result.get('id'),
                    'title': result.get('title_original', result.get('title')),
                    'publisher': result.get('publisher_original', result.get('publisher')),
                    'rss_url': result.get('rss'),
                    'thumbnail': result.get('thumbnail'),
                    'total_episodes': result.get('total_episodes', 0)
                })
            
            return podcasts
            
        except Exception as e:
            print(f"  ⚠️ Listen Notes search error: {e}")
            return []
    
    def get_podcast_episodes(self, podcast_id: str, limit: int = 10) -> list:
        """
        Get recent episodes for a podcast.
        
        Args:
            podcast_id: Listen Notes podcast ID
            limit: Max episodes to return
            
        Returns:
            List of episode dicts
        """
        try:
            response = self._api_request(
                'GET',
                f'/podcasts/{podcast_id}',
                params={'sort': 'recent_first'}
            )
            
            episodes = []
            for ep in response.get('episodes', [])[:limit]:
                episodes.append(self._format_episode_data(ep, response))
            
            return episodes
            
        except Exception as e:
            print(f"  ⚠️ Listen Notes podcast lookup error: {e}")
            return []
    
    def _lookup_by_apple_id(self, show_id: str, episode_id: str) -> Optional[Dict]:
        """Look up episode by Apple Podcasts IDs"""
        # Listen Notes doesn't have direct Apple ID lookup, use search
        return None
    
    def _lookup_by_spotify_id(self, episode_id: str) -> Optional[Dict]:
        """Look up episode by Spotify ID"""
        # Listen Notes doesn't have direct Spotify ID lookup, use search
        return None
    
    def _search_by_url(self, url: str) -> Optional[Dict]:
        """
        Search for episode/podcast by URL.
        Since just_listen endpoint isn't available on free tier,
        we'll extract info from URL and use search/lookup methods.
        """
        # Note: The just_listen endpoint requires a paid plan
        # For free tier, we'll rely on RSS fallback in youtube_slash_command.py
        # This returns None to allow the fallback chain to work
        
        print(f"  ℹ️ Listen Notes: Direct URL lookup not available on free tier")
        print(f"  ℹ️ Will use RSS feed extraction as fallback")
        return None
    
    def _format_episode_data(self, episode: Dict, podcast: Dict = None) -> Dict:
        """Format episode data into standard structure"""
        return {
            'audio_url': episode.get('audio'),
            'title': episode.get('title'),
            'description': episode.get('description', ''),
            'duration': episode.get('audio_length_sec', 0),
            'podcast_title': podcast.get('title') if podcast else episode.get('podcast', {}).get('title', ''),
            'podcast_id': episode.get('podcast', {}).get('id', ''),
            'episode_id': episode.get('id', ''),
            'pub_date': episode.get('pub_date_ms', 0),
            'thumbnail': episode.get('thumbnail') or episode.get('image'),
            'source': 'listen_notes_api'
        }
    
    def _api_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Execute API request against Listen Notes"""
        url = f"{self.base_url}{endpoint}"
        
        response = requests.request(
            method,
            url,
            headers=self.headers,
            timeout=30,
            **kwargs
        )
        
        self.requests_made += 1
        
        # Track rate limits from response headers
        if 'X-ListenAPI-FreeQuota' in response.headers:
            self.quota_remaining = int(response.headers['X-ListenAPI-FreeQuota'])
        
        response.raise_for_status()
        return response.json()
    
    def _parse_podcast_url(self, url: str) -> Optional[Dict]:
        """
        Extract identifiers from podcast URLs.
        
        Returns:
            Dict with platform, show_id, episode_id, or None
        """
        # Apple Podcasts: podcasts.apple.com/.../id{SHOW}?i={EPISODE}
        apple_match = re.search(r'podcasts\.apple\.com.*?/id(\d+)(?:\?i=(\d+))?', url)
        if apple_match:
            show_id = apple_match.group(1)
            episode_id = apple_match.group(2)  # May be None
            return {
                'platform': 'apple_podcasts',
                'show_id': show_id,
                'episode_id': episode_id
            }
        
        # Spotify: open.spotify.com/episode/{EPISODE_ID}
        spotify_match = re.search(r'spotify\.com/episode/([a-zA-Z0-9]+)', url)
        if spotify_match:
            return {
                'platform': 'spotify',
                'episode_id': spotify_match.group(1)
            }
        
        # Spotify: open.spotify.com/show/{SHOW_ID}
        spotify_show_match = re.search(r'spotify\.com/show/([a-zA-Z0-9]+)', url)
        if spotify_show_match:
            return {
                'platform': 'spotify',
                'show_id': spotify_show_match.group(1)
            }
        
        # RSS Feed
        if url.startswith('http') and (url.endswith('.rss') or url.endswith('.xml') or 
                                        '/rss' in url.lower() or '/feed' in url.lower() or 
                                        'feeds.' in url.lower()):
            return {
                'platform': 'rss',
                'rss_url': url
            }
        
        return None
    
    def get_metrics(self) -> Dict:
        """Get usage metrics"""
        return {
            'requests_made': self.requests_made,
            'quota_remaining': self.quota_remaining
        }
