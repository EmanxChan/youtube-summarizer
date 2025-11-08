#!/usr/bin/env python3
"""
Migrate existing summaries from ~/Documents/YouTube videos/
to the new organized structure in ~/Documents/AI Content Summaries/
"""

import shutil
from pathlib import Path
import re


def classify_file(file_path: Path) -> str:
    """
    Classify a markdown file by reading its content.
    
    Returns: 'youtube', 'podcast', 'article', or 'unknown'
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check first 500 characters for type indicators
        header = content[:500]
        
        # YouTube indicators
        if 'Video ID:' in header or '**Video ID:**' in header:
            return 'youtube'
        
        # Podcast indicators
        if any(indicator in header for indicator in [
            'Type: Podcast',
            'Podcast Transcript',
            'podcasts.apple.com',
            'Listen Notes',
            'RSS Feed'
        ]):
            return 'podcast'
        
        # Article indicators
        if any(indicator in header for indicator in [
            'Type: Article',
            '**Type:** Article',
            'sherwood.news',
            'semafor.com',
            '.com/article',
            'python.org',
            'every.to'
        ]):
            return 'article'
        
        # Additional heuristics for edge cases
        if '.com/' in header or '.org/' in header:
            # Has URL but not a video ID - likely article
            if 'Video ID:' not in content:
                return 'article'
        
        return 'unknown'
        
    except Exception as e:
        print(f"  ⚠️  Error reading {file_path.name}: {e}")
        return 'unknown'


def migrate_summaries(dry_run=True):
    """
    Migrate files from old to new structure.
    
    Args:
        dry_run: If True, only show what would be done without moving files
    """
    # Directories
    old_dir = Path.home() / "Documents" / "YouTube videos"
    new_base = Path.home() / "Documents" / "AI Content Summaries"
    
    youtube_dir = new_base / "YouTube Summaries"
    podcast_dir = new_base / "Podcast Summaries"
    article_dir = new_base / "Article Summaries"
    unknown_dir = new_base / "Uncategorized"
    
    # Create new directories (in real run only)
    if not dry_run:
        youtube_dir.mkdir(parents=True, exist_ok=True)
        podcast_dir.mkdir(parents=True, exist_ok=True)
        article_dir.mkdir(parents=True, exist_ok=True)
        unknown_dir.mkdir(parents=True, exist_ok=True)
    
    # Statistics
    stats = {
        'youtube': 0,
        'podcast': 0,
        'article': 0,
        'unknown': 0,
        'skipped': 0
    }
    
    print("=" * 70)
    print("SUMMARY FILE MIGRATION")
    print("=" * 70)
    print(f"Source: {old_dir}")
    print(f"Destination: {new_base}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'REAL MIGRATION'}")
    print("=" * 70)
    print()
    
    # Get all markdown files
    md_files = sorted(old_dir.glob("*.md"))
    txt_files = sorted(old_dir.glob("*.txt"))
    
    print(f"Found {len(md_files)} markdown files and {len(txt_files)} text files\n")
    
    # Process markdown files
    for file_path in md_files:
        file_type = classify_file(file_path)
        
        # Determine destination
        if file_type == 'youtube':
            dest_dir = youtube_dir
        elif file_type == 'podcast':
            dest_dir = podcast_dir
        elif file_type == 'article':
            dest_dir = article_dir
        else:
            dest_dir = unknown_dir
        
        dest_path = dest_dir / file_path.name
        
        # Show what we're doing
        icon = {
            'youtube': '📺',
            'podcast': '🎙️',
            'article': '📄',
            'unknown': '❓'
        }.get(file_type, '❓')
        
        print(f"{icon} {file_path.name}")
        print(f"   → {dest_dir.name}/")
        
        # Move file (if not dry run)
        if not dry_run:
            try:
                shutil.copy2(file_path, dest_path)
                stats[file_type] += 1
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                stats['skipped'] += 1
        else:
            stats[file_type] += 1
    
    # Process text files (legacy format)
    if txt_files:
        print(f"\n📝 Legacy text files ({len(txt_files)} found):")
        for txt_file in txt_files:
            print(f"   - {txt_file.name}")
        print("   → Will be left in original location (legacy format)")
    
    # Print summary
    print("\n" + "=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    print(f"📺 YouTube Videos:  {stats['youtube']:3d} files → YouTube Summaries/")
    print(f"🎙️  Podcasts:        {stats['podcast']:3d} files → Podcast Summaries/")
    print(f"📄 Articles:        {stats['article']:3d} files → Article Summaries/")
    print(f"❓ Uncategorized:   {stats['unknown']:3d} files → Uncategorized/")
    print(f"⚠️  Skipped:         {stats['skipped']:3d} files")
    print(f"   Total:          {sum(stats.values()):3d} files")
    print("=" * 70)
    
    if dry_run:
        print("\n💡 This was a DRY RUN - no files were moved")
        print("   Run with --execute flag to perform actual migration")
    else:
        print(f"\n✅ Migration complete!")
        print(f"   Files copied to: {new_base}")
        print(f"   Original files remain in: {old_dir}")
        print(f"\n⚠️  Next step: Review migrated files, then delete old directory if satisfied")


if __name__ == '__main__':
    import sys
    
    # Check for --execute flag
    execute = '--execute' in sys.argv or '-e' in sys.argv
    
    if not execute:
        print("🔍 Running in DRY RUN mode (no changes will be made)\n")
    
    migrate_summaries(dry_run=not execute)
    
    if not execute:
        print("\n" + "=" * 70)
        print("To perform the actual migration, run:")
        print("  python3 scripts/migrate_existing_summaries.py --execute")
        print("=" * 70)
