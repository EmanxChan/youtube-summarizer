#!/usr/bin/env python3
"""Caching layer for podcast API responses to preserve quota"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict


class PodcastCache:
    """Cache podcast API responses to avoid quota waste"""
    
    def __init__(self, cache_dir: Optional[Path] = None, provider: str = "podcast"):
        """
        Initialize cache.
        
        Args:
            cache_dir: Custom cache directory (optional)
            provider: Provider name for cache subdirectory (e.g., 'listen_notes', 'taddy')
        """
        self.cache_dir = cache_dir or (Path.home() / ".cache" / "podcast_transcripts" / provider)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_days = 30  # Metadata doesn't change often
    
    def get(self, podcast_url: str) -> Optional[Dict]:
        """
        Get cached data for URL.
        
        Args:
            podcast_url: Podcast URL
            
        Returns:
            Cached data dict or None
        """
        cache_key = self._get_cache_key(podcast_url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            # Check if expired
            cached_at = datetime.fromisoformat(cached['cached_at'])
            if datetime.now() - cached_at > timedelta(days=self.ttl_days):
                cache_file.unlink()  # Remove stale cache
                return None
            
            return cached['data']
            
        except Exception as e:
            return None
    
    def set(self, podcast_url: str, data: Dict):
        """
        Cache podcast data.
        
        Args:
            podcast_url: Podcast URL
            data: Podcast data to cache
        """
        cache_key = self._get_cache_key(podcast_url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'data': data,
                    'cached_at': datetime.now().isoformat(),
                    'url': podcast_url
                }, f, indent=2)
        except Exception as e:
            print(f"  ⚠️ Podcast cache write failed: {e}")
    
    def _get_cache_key(self, podcast_url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.md5(podcast_url.encode()).hexdigest()
    
    def clear_old(self):
        """Clear expired cache entries"""
        cutoff = datetime.now() - timedelta(days=self.ttl_days)
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                cached_at = datetime.fromisoformat(cached['cached_at'])
                if cached_at < cutoff:
                    cache_file.unlink()
            except:
                pass
    
    def clear_all(self):
        """Clear all cached entries"""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except:
                pass
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in cache_files if f.exists())
        
        return {
            'total_entries': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }
