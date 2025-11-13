#!/usr/bin/env python3
"""Track which method provided each transcript"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict


class TranscriptMetrics:
    """Track transcript sources and success rates"""
    
    def __init__(self, metrics_file: Path = None):
        """
        Initialize metrics tracker.
        
        Args:
            metrics_file: Custom metrics file path (optional)
        """
        self.metrics_file = metrics_file or (Path.home() / ".cache" / "transcript_metrics.json")
        self.metrics = self._load_metrics()
    
    def record(self, source: str, content_url: str, success: bool, duration: float = 0):
        """
        Record transcript retrieval attempt.
        
        Args:
            source: 'listen_notes_api', 'listen_notes_api_cached', 'youtube_mirror', 'whisper', 'show_notes', 'webpage'
            content_url: URL attempted
            success: Whether transcript was obtained
            duration: Time taken in seconds
        """
        if source not in self.metrics['sources']:
            self.metrics['sources'][source] = {
                'attempts': 0,
                'successes': 0,
                'failures': 0,
                'total_duration': 0
            }
        
        self.metrics['sources'][source]['attempts'] += 1
        if success:
            self.metrics['sources'][source]['successes'] += 1
        else:
            self.metrics['sources'][source]['failures'] += 1
        
        self.metrics['sources'][source]['total_duration'] += duration
        
        # Track individual request
        self.metrics['history'].append({
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'url': content_url[:100],  # Truncate for privacy
            'success': success,
            'duration': round(duration, 2)
        })
        
        # Keep only last 100 entries
        self.metrics['history'] = self.metrics['history'][-100:]
        
        self._save_metrics()
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        summary = {}
        for source, stats in self.metrics['sources'].items():
            if stats['attempts'] > 0:
                summary[source] = {
                    'attempts': stats['attempts'],
                    'successes': stats['successes'],
                    'failures': stats['failures'],
                    'success_rate': (stats['successes'] / stats['attempts']) * 100,
                    'avg_duration': stats['total_duration'] / stats['attempts']
                }
        return summary
    
    def print_summary(self):
        """Print metrics to console"""
        print("\n📊 Transcript Source Metrics:")
        print("=" * 80)
        print(f"{'Source':<25} | {'Attempts':>8} | {'Success':>7} | {'Avg Time':>8}")
        print("-" * 80)
        
        summary = self.get_summary()
        
        # Sort by attempts (most used first)
        sorted_sources = sorted(summary.items(), key=lambda x: x[1]['attempts'], reverse=True)
        
        for source, stats in sorted_sources:
            success_rate = f"{stats['success_rate']:.1f}%"
            avg_duration = f"{stats['avg_duration']:.1f}s"
            print(f"{source:<25} | {stats['attempts']:>8} | {success_rate:>7} | {avg_duration:>8}")
        
        print("=" * 80)
        print(f"Total transcript requests: {sum(s['attempts'] for s in summary.values())}")
        print()
    
    def _load_metrics(self) -> Dict:
        """Load metrics from file"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'sources': {},
            'history': []
        }
    
    def _save_metrics(self):
        """Save metrics to file"""
        try:
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            pass  # Silent fail for metrics
