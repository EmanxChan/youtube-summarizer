#!/usr/bin/env python3
"""
Demo of the YouTube slash command with sample transcript data.
Shows the full workflow without hitting YouTube API rate limits.
"""
from pathlib import Path
from youtube_slash_command import (
    slugify,
    clean_transcript,
    summarize_transcript,
    get_unique_filepath
)

# Sample transcript from a typical programming tutorial
SAMPLE_TRANSCRIPT = """
Welcome to this introduction to Python programming. Today we're going to cover the fundamentals 
of Python that every beginner needs to know. Python is one of the most popular programming 
languages in the world and it's known for being easy to learn and powerful enough for professional 
development. Let's start with variables. A variable is a container for storing data values. 
In Python you don't need to declare the type of a variable, it's automatically determined based 
on the value you assign. For example, x equals five creates an integer variable. If you assign 
text in quotes, like name equals John, that creates a string variable. Python supports various 
data types including integers, floats, strings, booleans, lists, and dictionaries. Lists are 
ordered collections that can contain multiple items. You create a list using square brackets. 
Dictionaries store data in key value pairs using curly braces. Control flow is essential in 
programming. We use if statements to make decisions. The if keyword checks a condition and 
executes code only if the condition is true. You can add else and elif for alternative paths. 
Loops allow you to repeat code. The for loop iterates over sequences like lists or ranges. 
The while loop continues as long as a condition is true. Functions are reusable blocks of code. 
You define a function using the def keyword followed by the function name and parentheses. 
Functions can accept parameters and return values. This makes your code more organized and 
maintainable. Python also has powerful built-in functions like print, len, type, and input. 
Object oriented programming is supported through classes. A class is a blueprint for creating 
objects. You define attributes and methods inside a class. Inheritance allows classes to inherit 
properties from other classes. Exception handling with try and except blocks helps manage errors 
gracefully. Python has a rich standard library with modules for file handling, math operations, 
regular expressions, and much more. You can also install third party packages using pip. 
Popular packages include NumPy for numerical computing, Pandas for data analysis, and Flask 
for web development. To continue learning Python I recommend practicing regularly with small 
projects, reading documentation, and working through coding challenges on platforms like 
LeetCode or HackerRank. Remember that programming is a skill that improves with practice. 
Don't get discouraged by errors, they're a natural part of the learning process. Thank you 
for watching and happy coding!
"""

def demo_youtube_command():
    """Demonstrate the YouTube command workflow"""
    
    print("="*70)
    print("DEMO: /youtube command workflow")
    print("="*70)
    print()
    
    # Simulated video info
    video_id = "ocMOZpuAMw4"
    video_title = "Introduction to Python Programming - Complete Tutorial"
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    print(f"Processing: {video_url}")
    print(f"Video ID: {video_id}")
    print(f"Title: {video_title}")
    print()
    
    # Step 1: Clean transcript
    print("Step 1: Cleaning transcript...")
    transcript = clean_transcript(SAMPLE_TRANSCRIPT)
    print(f"✓ Transcript cleaned ({len(transcript)} characters, {len(transcript.split())} words)")
    print()
    
    # Step 2: Generate summary
    word_count = 150
    print(f"Step 2: Generating summary (target: {word_count} words)...")
    summary = summarize_transcript(transcript, word_count)
    summary_word_count = len(summary.split())
    print(f"✓ Summary generated ({summary_word_count} words)")
    print()
    
    # Step 3: Generate filename
    print("Step 3: Generating filename...")
    slug = slugify(video_title)
    print(f"✓ Slug: {slug}")
    print()
    
    # Step 4: Save files
    print("Step 4: Saving files...")
    output_dir = Path.home() / "Documents" / "YouTube videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    transcript_file = get_unique_filepath(output_dir, slug, "transcript.txt")
    summary_file = get_unique_filepath(output_dir, slug, "summary.txt")
    
    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(transcript)
    print(f"✓ Transcript saved: {transcript_file}")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"✓ Summary saved: {summary_file}")
    print()
    
    # Step 5: Display summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(summary)
    print("="*70)
    print()
    
    # Statistics
    transcript_words = len(transcript.split())
    reduction = round((1 - summary_word_count/transcript_words) * 100, 1)
    print(f"Statistics:")
    print(f"  Original: {transcript_words} words")
    print(f"  Summary: {summary_word_count} words")
    print(f"  Reduction: {reduction}%")
    print()
    
    print("="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print()
    print("This demonstrates the full workflow. When YouTube APIs are available,")
    print("the system will:")
    print("  1. Fetch actual video transcripts")
    print("  2. Support both URLs and search queries")
    print("  3. Handle multiple videos without file collisions")
    print()

if __name__ == "__main__":
    demo_youtube_command()
