#!/usr/bin/env python3
"""
Taddy API integration for podcast transcripts.
API Docs: https://taddy.org/developers/podcast-api/episode-transcripts
"""

import os
import json
import requests
import re
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs


class TaddyClient:
    """Client for Taddy Podcast API"""
    
    def __init__(self, api_key: Optional[str] = None, user_id: Optional[str] = None):
        """
        Initialize Taddy API client.
        
        Args:
            api_key: Taddy API key (or set TADDY_API_KEY env var)
            user_id: Taddy User ID (or set TADDY_USER_ID env var)
        """
        self.api_key = api_key or os.getenv('TADDY_API_KEY')
        self.user_id = user_id or os.getenv('TADDY_USER_ID')
        
        if not self.api_key:
            raise ValueError("Taddy API key required. Set TADDY_API_KEY env var.")
        if not self.user_id:
            raise ValueError("Taddy User ID required. Set TADDY_USER_ID env var.")
        
        self.base_url = "https://api.taddy.org"
        self.headers = {
            "X-USER-ID": self.user_id,
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        self.quota_remaining = 500  # Free tier default
        self.requests_made = 0
    
    def search_podcast_by_name(self, podcast_name: str) -> Optional[str]:
        """
        Search for podcast series UUID by name.
        
        Args:
            podcast_name: Name of the podcast show
            
        Returns:
            Series UUID if found, None otherwise
        """
        query = f"""
        query {{
            getPodcastSeries(name: "{podcast_name}") {{
                uuid
                name
                itunesId
            }}
        }}
        """
        try:
            response = self._graphql_request(query)
            series = response.get('data', {}).get('getPodcastSeries')
            if series:
                return series['uuid']
        except Exception as e:
            print(f"  ⚠️ Taddy search error: {e}")
        
        return None
    
    def search_episode_by_identifiers(self, platform: str, show_id: str = None, 
                                     episode_id: str = None, rss_url: str = None) -> Optional[str]:
        """
        Search for episode UUID using platform identifiers.
        
        Args:
            platform: 'apple_podcasts', 'spotify', or 'rss'
            show_id: Platform-specific show identifier
            episode_id: Platform-specific episode identifier
            rss_url: RSS feed URL (if available)
            
        Returns:
            Episode UUID if found, None otherwise
        """
        # For Apple Podcasts - try to get series by iTunes ID
        if platform == 'apple_podcasts' and show_id:
            query = f"""
            query {{
                getPodcastSeries(itunesId: {show_id}) {{
                    uuid
                    name
                }}
            }}
            """
            try:
                response = self._graphql_request(query)
                series = response.get('data', {}).get('getPodcastSeries')
                if series:
                    return self._get_latest_episode_from_series(series['uuid'])
            except:
                pass
        
        # For Spotify or other platforms - try general search
        return None
    
    def _get_latest_episode_from_series(self, series_uuid: str) -> Optional[str]:
        """Get latest episode UUID from podcast series"""
        query = f"""
        query {{
            getPodcastSeries(uuid: "{series_uuid}") {{
                uuid
                name
                episodes(limitPerPage: 1, page: 1) {{
                    uuid
                    name
                    datePublished
                }}
            }}
        }}
        """
        try:
            response = self._graphql_request(query)
            series = response.get('data', {}).get('getPodcastSeries')
            
            if not series:
                return None
            
            episodes = series.get('episodes', [])
            
            if episodes and len(episodes) > 0:
                return episodes[0]['uuid']
                
        except Exception as e:
            print(f"  ⚠️ Error getting episodes: {e}")
        
        return None
    
    def get_episode_transcript(self, episode_uuid: str) -> Optional[Dict]:
        """
        Get transcript for episode UUID.
        
        Args:
            episode_uuid: Taddy episode UUID
            
        Returns:
            Dict with {transcript, title, duration, description, source} or None
        """
        query = f"""
        query {{
            getEpisodeTranscript(uuid: "{episode_uuid}") {{
                uuid
                name
                description
                duration
                transcript
                audioUrl
                datePublished
            }}
        }}
        """
        
        try:
            response = self._graphql_request(query)
            episode = response.get('data', {}).get('getEpisodeTranscript')
            
            if not episode:
                print(f"  ℹ️ Taddy: No transcript data in response")
                return None
            
            # Try different transcript field names
            transcript = (episode.get('transcript') or 
                         episode.get('transcriptWithSpeakersAndTimecodes') or 
                         episode.get('transcriptText') or '')
            
            if not transcript or len(transcript) < 100:
                print(f"  ℹ️ Taddy: Transcript too short or missing")
                return None
            
            return {
                'transcript': transcript,
                'title': episode.get('name', 'Unknown Episode'),
                'duration': episode.get('duration', 0),
                'description': episode.get('description', ''),
                'source': 'taddy_api',
                'episode_uuid': episode_uuid
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"  ℹ️ Taddy: Episode not found in database")
            elif e.response.status_code == 429:
                print(f"  ⚠️ Taddy: Rate limit exceeded")
            else:
                print(f"  ⚠️ Taddy HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            print(f"  ⚠️ Taddy transcript fetch failed: {e}")
            return None
    
    def get_transcript_by_url(self, podcast_url: str, podcast_name: str = None) -> Optional[Dict]:
        """
        Main entry point: Get transcript directly from podcast URL.
        
        Args:
            podcast_url: Apple Podcasts, Spotify, or RSS URL
            podcast_name: Optional podcast name for searching
            
        Returns:
            Transcript dict or None
        """
        # Parse URL to get identifiers
        parsed = self._parse_podcast_url(podcast_url)
        
        if not parsed:
            print(f"  ℹ️ Taddy: Unsupported URL format")
            return None
        
        # Try to find episode by platform identifiers
        episode_uuid = self.search_episode_by_identifiers(
            platform=parsed['platform'],
            show_id=parsed.get('show_id'),
            episode_id=parsed.get('episode_id'),
            rss_url=parsed.get('rss_url')
        )
        
        # If that fails and we have a podcast name, try searching by name
        if not episode_uuid and podcast_name:
            print(f"  🔍 Trying search by podcast name...")
            series_uuid = self.search_podcast_by_name(podcast_name)
            if series_uuid:
                episode_uuid = self._get_latest_episode_from_series(series_uuid)
        
        if not episode_uuid:
            print(f"  ℹ️ Taddy: Could not find episode")
            return None
        
        # Get transcript
        return self.get_episode_transcript(episode_uuid)
    
    def _graphql_request(self, query: str) -> Dict:
        """Execute GraphQL query against Taddy API"""
        response = requests.post(
            f"{self.base_url}/graphql",
            headers=self.headers,
            json={"query": query},
            timeout=30
        )
        
        self.requests_made += 1
        
        # Track rate limits from response headers
        if 'X-RateLimit-Remaining' in response.headers:
            self.quota_remaining = int(response.headers['X-RateLimit-Remaining'])
        
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
            'quota_remaining': self.quota_remaining,
            'quota_limit': 500  # Free tier
        }
