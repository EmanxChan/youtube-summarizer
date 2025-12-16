#!/usr/bin/env python3
"""
History manager for tracking summarization history.
Stores history in a local JSON file for quick access and re-processing.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# Default history file location
DEFAULT_HISTORY_PATH = Path.home() / '.youtube_summarizer' / 'history.json'
MAX_HISTORY_ENTRIES = 500  # Keep last N entries


class HistoryManager:
    """Manages summarization history stored in a local JSON file."""

    def __init__(self, history_path: Optional[Path] = None):
        """
        Initialize history manager.

        Args:
            history_path: Path to history JSON file. Defaults to ~/.youtube_summarizer/history.json
        """
        self.history_path = history_path or DEFAULT_HISTORY_PATH
        self._ensure_directory()
        self._history = self._load_history()

    def _ensure_directory(self):
        """Ensure the history directory exists."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_history(self) -> Dict:
        """Load history from JSON file."""
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure proper structure
                    if 'entries' not in data:
                        data = {'entries': [], 'version': 1}
                    return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load history file: {e}")
                return {'entries': [], 'version': 1}
        return {'entries': [], 'version': 1}

    def _save_history(self):
        """Save history to JSON file."""
        try:
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save history file: {e}")

    def add_entry(
        self,
        url: str,
        title: str,
        content_type: str,
        source_label: str,
        transcript_preview: str = "",
        summary_preview: str = "",
        duration_seconds: int = 0,
        extra_metadata: Optional[Dict] = None
    ) -> str:
        """
        Add a new entry to history.

        Args:
            url: Source URL
            title: Content title
            content_type: Type of content (video, podcast, article)
            source_label: Source label (e.g., "YouTube Transcript", "Podcast RSS")
            transcript_preview: First ~200 chars of transcript
            summary_preview: First ~200 chars of summary
            duration_seconds: Duration in seconds (for video/podcast)
            extra_metadata: Any additional metadata to store

        Returns:
            Entry ID
        """
        entry_id = str(uuid.uuid4())[:8]

        entry = {
            'id': entry_id,
            'url': url,
            'title': title,
            'content_type': content_type,
            'source_label': source_label,
            'created_at': datetime.now().isoformat(),
            'transcript_preview': transcript_preview[:300] if transcript_preview else "",
            'summary_preview': summary_preview[:300] if summary_preview else "",
            'duration_seconds': duration_seconds,
        }

        if extra_metadata:
            entry['metadata'] = extra_metadata

        # Add to beginning of list (most recent first)
        self._history['entries'].insert(0, entry)

        # Trim to max entries
        if len(self._history['entries']) > MAX_HISTORY_ENTRIES:
            self._history['entries'] = self._history['entries'][:MAX_HISTORY_ENTRIES]

        self._save_history()
        return entry_id

    def get_entries(
        self,
        limit: int = 50,
        offset: int = 0,
        content_type: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict]:
        """
        Get history entries with optional filtering.

        Args:
            limit: Max entries to return
            offset: Number of entries to skip
            content_type: Filter by content type (video, podcast, article)
            search_query: Search in title and URL

        Returns:
            List of history entries
        """
        entries = self._history['entries']

        # Filter by content type
        if content_type:
            entries = [e for e in entries if e.get('content_type') == content_type]

        # Search filter
        if search_query:
            query_lower = search_query.lower()
            entries = [
                e for e in entries
                if query_lower in e.get('title', '').lower()
                or query_lower in e.get('url', '').lower()
            ]

        # Apply pagination
        return entries[offset:offset + limit]

    def get_entry_by_id(self, entry_id: str) -> Optional[Dict]:
        """Get a specific entry by ID."""
        for entry in self._history['entries']:
            if entry.get('id') == entry_id:
                return entry
        return None

    def get_entry_by_url(self, url: str) -> Optional[Dict]:
        """Get the most recent entry for a URL."""
        for entry in self._history['entries']:
            if entry.get('url') == url:
                return entry
        return None

    def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry by ID."""
        for i, entry in enumerate(self._history['entries']):
            if entry.get('id') == entry_id:
                del self._history['entries'][i]
                self._save_history()
                return True
        return False

    def clear_history(self) -> int:
        """Clear all history entries. Returns number of entries deleted."""
        count = len(self._history['entries'])
        self._history['entries'] = []
        self._save_history()
        return count

    def get_stats(self) -> Dict:
        """Get history statistics."""
        entries = self._history['entries']

        type_counts = {}
        for entry in entries:
            ct = entry.get('content_type', 'unknown')
            type_counts[ct] = type_counts.get(ct, 0) + 1

        return {
            'total_entries': len(entries),
            'by_type': type_counts,
            'oldest_entry': entries[-1].get('created_at') if entries else None,
            'newest_entry': entries[0].get('created_at') if entries else None,
        }

    def format_entry_for_display(self, entry: Dict) -> Dict:
        """Format an entry for UI display."""
        created_at = entry.get('created_at', '')

        # Parse and format date
        try:
            dt = datetime.fromisoformat(created_at)
            now = datetime.now()
            diff = now - dt

            if diff.days == 0:
                if diff.seconds < 3600:
                    time_ago = f"{diff.seconds // 60}m ago"
                else:
                    time_ago = f"{diff.seconds // 3600}h ago"
            elif diff.days == 1:
                time_ago = "Yesterday"
            elif diff.days < 7:
                time_ago = f"{diff.days}d ago"
            else:
                time_ago = dt.strftime("%b %d")
        except:
            time_ago = created_at[:10] if created_at else "Unknown"

        # Format duration
        duration = entry.get('duration_seconds', 0)
        if duration:
            mins = duration // 60
            secs = duration % 60
            duration_str = f"{mins}:{secs:02d}"
        else:
            duration_str = ""

        # Content type icon
        content_type = entry.get('content_type', '')
        icons = {
            'video': '📺',
            'podcast': '🎙️',
            'article': '📄',
        }
        icon = icons.get(content_type, '📝')

        # Extract domain from URL
        url = entry.get('url', '')
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace('www.', '')
        except:
            domain = url[:30]

        return {
            **entry,
            'icon': icon,
            'time_ago': time_ago,
            'duration_str': duration_str,
            'domain': domain,
        }


# Global instance for easy access
_history_manager: Optional[HistoryManager] = None


def get_history_manager() -> HistoryManager:
    """Get the global history manager instance."""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager


def record_history(
    url: str,
    title: str,
    content_type: str,
    source_label: str,
    transcript: str = "",
    summary: str = "",
    duration_seconds: int = 0,
    **extra_metadata
) -> str:
    """
    Convenience function to record a history entry.

    Args:
        url: Source URL
        title: Content title
        content_type: Type (video, podcast, article)
        source_label: Source label
        transcript: Full transcript (preview will be extracted)
        summary: Full summary (preview will be extracted)
        duration_seconds: Duration in seconds
        **extra_metadata: Any additional metadata

    Returns:
        Entry ID
    """
    manager = get_history_manager()
    return manager.add_entry(
        url=url,
        title=title,
        content_type=content_type,
        source_label=source_label,
        transcript_preview=transcript[:300] if transcript else "",
        summary_preview=summary[:300] if summary else "",
        duration_seconds=duration_seconds,
        extra_metadata=extra_metadata if extra_metadata else None
    )
