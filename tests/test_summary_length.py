#!/usr/bin/env python3
"""
Test script to verify the summary length enhancement is working.
Tests both the enhanced prompt and retry logic.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_summarizer import AITranscriptSummarizer


def test_summary_length():
    """Test that summaries meet the requested word count"""
    
    # Sample transcript (relatively short to challenge the AI)
    sample_transcript = """
    Welcome to this tutorial on using Cursor IDE for AI-assisted development. 
    Cursor is a modern code editor built specifically for working with AI.
    It combines traditional IDE features with powerful AI capabilities.
    
    The main features include intelligent code completion, natural language commands,
    and seamless integration with large language models. You can describe what you want
    to build in plain English, and Cursor will generate the code for you.
    
    Setting up is straightforward - download the app, install it, and sign in with your account.
    The interface will feel familiar if you've used VS Code before, as it's built on the same foundation.
    
    Key shortcuts to learn include Command+K for AI commands and Command+L for chat.
    These shortcuts let you quickly interact with the AI without leaving your workflow.
    
    Best practices include being specific in your prompts, reviewing generated code carefully,
    and using the AI as a collaborator rather than a replacement for understanding.
    Common mistakes include relying too heavily on AI without verification.
    
    By the end of this tutorial, you'll be able to build applications much faster
    while maintaining high code quality standards.
    """
    
    try:
        # Initialize with Mistral via Ollama
        print("Initializing AI summarizer with Mistral...")
        summarizer = AITranscriptSummarizer(provider="ollama", model="mistral:instruct")
        
        # Test with different word counts
        test_cases = [
            (200, "Short Summary"),
            (500, "Medium Summary"),
            (1000, "Long Summary"),
        ]
        
        print("\n" + "=" * 80)
        for target_words, test_name in test_cases:
            print(f"\n{test_name}: Target {target_words} words")
            print("-" * 80)
            
            summary = summarizer.generate_executive_summary(
                sample_transcript,
                "Cursor IDE Tutorial",
                word_count=target_words
            )
            
            actual_words = len(summary.split())
            percentage = (actual_words / target_words) * 100
            
            print(f"Generated: {actual_words} words ({percentage:.1f}% of target)")
            
            if actual_words >= int(target_words * 0.85):
                print("✓ PASS: Summary meets minimum length requirement")
            else:
                print("✗ FAIL: Summary is too short")
            
            print(f"\nSummary preview (first 200 chars):")
            print(summary[:200] + "...")
            print("=" * 80)
        
        print("\n✓ Test completed successfully")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_summary_length()
