#!/usr/bin/env python3
"""
Benchmark OpenRouter models (DeepSeek V3.1, Kimi K2) vs local Qwen 7B
"""

import os
import sys
import time
import json
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_summarizer import AITranscriptSummarizer

# Test configurations
MODELS_TO_TEST = [
    {
        'name': 'DeepSeek V3.1 Free',
        'provider': 'openrouter',
        'model': 'deepseek/deepseek-chat-v3.1:free',
        'params': '671B (hybrid reasoning)'
    },
    {
        'name': 'Kimi K2 0711 Free',
        'provider': 'openrouter', 
        'model': 'moonshotai/kimi-k2:free',
        'params': '1T MoE, 32B active'
    },
    {
        'name': 'Qwen 2.5 7B Local',
        'provider': 'ollama',
        'model': 'qwen2.5:7b-instruct-q4_K_M',
        'params': '7B quantized'
    }
]

def get_youtube_transcript(video_id):
    """Get YouTube transcript"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en'])
        data = transcript.fetch()
        
        # Get video title (approximate from first segment or use video_id)
        full_text = " ".join([item['text'] for item in data])
        title = f"Video {video_id}"
        
        return full_text, title
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None, None

def score_quality(takeaways, summary):
    """
    Score quality based on your use case criteria:
    - Non-obvious insights (not generic)
    - Tradeoff identification 
    - Technical depth
    - Actionable implications
    """
    score = 0
    total = 0
    
    # Check each takeaway for quality markers
    generic_phrases = ['improve', 'better', 'faster', 'learn', 'master', 'use', 'helps', 'allows']
    depth_markers = ['tradeoff', 'constraint', 'limitation', 'because', 'when', 'why', 'however', 'whereas']
    
    for takeaway in takeaways:
        total += 1
        takeaway_lower = takeaway.lower()
        
        # Deduct for generic phrases
        generic_count = sum(1 for phrase in generic_phrases if phrase in takeaway_lower)
        score -= generic_count * 0.5
        
        # Add for depth markers
        depth_count = sum(1 for marker in depth_markers if marker in takeaway_lower)
        score += depth_count * 2
        
        # Length check (30-40 words = good)
        word_count = len(takeaway.split())
        if 25 <= word_count <= 50:
            score += 1
        elif word_count < 15:
            score -= 1  # Too short, likely superficial
    
    # Normalize to 0-10 scale
    if total == 0:
        return 0
    
    normalized = 5 + (score / max(total, 1)) * 2
    return max(0, min(10, round(normalized, 1)))

def run_single_test(model_config, content_type, content_url, transcript, title):
    """Test single model on content"""
    print(f"\n{'='*60}")
    print(f"Testing: {model_config['name']}")
    print(f"Content: {content_type} - {title[:50]}...")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        
        # Initialize summarizer
        summarizer = AITranscriptSummarizer(
            provider=model_config['provider'],
            model=model_config['model']
        )
        
        # Generate takeaways
        print("  Generating key takeaways...")
        takeaways = summarizer.generate_key_takeaways(transcript, title, count=5)
        
        # Generate summary
        print("  Generating executive summary...")
        summary = summarizer.generate_executive_summary(transcript, title, word_count=200)
        
        elapsed = time.time() - start_time
        
        # Score quality
        quality_score = score_quality(takeaways, summary)
        
        result = {
            'model': model_config['name'],
            'params': model_config['params'],
            'provider': model_config['provider'],
            'content_type': content_type,
            'elapsed_seconds': round(elapsed, 2),
            'quality_score': quality_score,
            'takeaways_count': len(takeaways),
            'summary_length': len(summary.split()),
            'takeaways': takeaways,
            'summary': summary,
            'success': True,
            'error': None
        }
        
        print(f"✓ Success in {elapsed:.1f}s")
        print(f"  Quality Score: {quality_score}/10")
        print(f"  Takeaways: {len(takeaways)}")
        print(f"  Summary words: {len(summary.split())}")
        
        return result
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"✗ Failed: {e}")
        return {
            'model': model_config['name'],
            'params': model_config['params'],
            'provider': model_config['provider'],
            'content_type': content_type,
            'elapsed_seconds': round(elapsed, 2),
            'success': False,
            'error': str(e)
        }

def generate_report(results):
    """Generate comparison report"""
    report = []
    report.append("# OpenRouter Model Benchmark Report")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Group by content type
    youtube_results = [r for r in results if r['content_type'] == 'youtube']
    podcast_results = [r for r in results if r['content_type'] == 'podcast']
    
    for content_type, group in [('YouTube', youtube_results), ('Podcast', podcast_results)]:
        if not group:
            continue
            
        report.append(f"\n## {content_type} Results\n")
        report.append("| Model | Quality | Speed | Takeaways | Summary Words | Status |")
        report.append("|-------|---------|-------|-----------|---------------|--------|")
        
        for r in group:
            if r['success']:
                report.append(f"| {r['model']} | {r['quality_score']}/10 | {r['elapsed_seconds']}s | {r['takeaways_count']} | {r['summary_length']} | ✅ |")
            else:
                error_msg = r['error'][:30] + "..." if len(r['error']) > 30 else r['error']
                report.append(f"| {r['model']} | N/A | {r['elapsed_seconds']}s | N/A | N/A | ❌ {error_msg} |")
    
    # Best model recommendation
    successful = [r for r in results if r['success']]
    if successful:
        # Calculate average quality score per model
        model_scores = {}
        for r in successful:
            model_name = r['model']
            if model_name not in model_scores:
                model_scores[model_name] = []
            model_scores[model_name].append(r['quality_score'])
        
        avg_scores = {model: sum(scores)/len(scores) for model, scores in model_scores.items()}
        best_model_name = max(avg_scores, key=avg_scores.get)
        best_score = avg_scores[best_model_name]
        
        # Get average speed for best model
        best_model_results = [r for r in successful if r['model'] == best_model_name]
        avg_speed = sum(r['elapsed_seconds'] for r in best_model_results) / len(best_model_results)
        
        report.append(f"\n## Recommendation\n")
        report.append(f"**Best Model: {best_model_name}**\n")
        report.append(f"- Average Quality Score: {best_score:.1f}/10")
        report.append(f"- Average Speed: {avg_speed:.1f}s")
        report.append(f"- Reason: Best balance of insight depth for your 'profound insights' use case\n")
        
        # Show all model rankings
        report.append(f"\n### All Models Ranked by Quality:\n")
        for i, (model, score) in enumerate(sorted(avg_scores.items(), key=lambda x: x[1], reverse=True), 1):
            report.append(f"{i}. **{model}**: {score:.1f}/10")
    
    # Detailed outputs
    report.append(f"\n## Detailed Outputs\n")
    for r in results:
        if r['success']:
            report.append(f"\n### {r['model']} - {r['content_type']}\n")
            report.append(f"**Quality Score:** {r['quality_score']}/10")
            report.append(f"**Speed:** {r['elapsed_seconds']}s")
            report.append(f"**Model Params:** {r['params']}\n")
            
            report.append(f"**Key Takeaways:**\n")
            for i, t in enumerate(r['takeaways'], 1):
                report.append(f"{i}. {t}\n")
            
            report.append(f"**Executive Summary:**\n")
            report.append(f"{r['summary']}\n")
            report.append(f"\n---\n")
    
    return '\n'.join(report)

def main():
    """Run full benchmark"""
    
    # Set API key
    api_key = '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'
    os.environ['OPENROUTER_API_KEY'] = api_key
    
    print("="*80)
    print("OpenRouter Model Benchmark")
    print("="*80)
    print("\nTesting Models:")
    for m in MODELS_TO_TEST:
        print(f"  - {m['name']} ({m['params']})")
    
    results = []
    
    # Test 1: YouTube video - use a lightweight one from find_test_content
    print("\n\n" + "="*80)
    print("PHASE 1: YouTube Video Test")
    print("="*80)
    
    # Use a well-known educational video with transcripts
    # Trying Fireship's "100 seconds" series which usually has captions
    youtube_url = "https://www.youtube.com/watch?v=Mus_vwhTCq0"  # Git explained in 100 seconds
    video_id = youtube_url.split('v=')[1].split('&')[0]
    
    print(f"\nFetching transcript for: {youtube_url}")
    transcript, title = get_youtube_transcript(video_id)
    
    if transcript:
        print(f"✓ Transcript fetched successfully")
        print(f"  Length: {len(transcript)} characters")
        print(f"  Words: {len(transcript.split())}")
        
        for model_config in MODELS_TO_TEST:
            result = run_single_test(model_config, 'youtube', youtube_url, transcript, title)
            results.append(result)
            time.sleep(2)  # Rate limit buffer between requests
    else:
        print("✗ Failed to fetch YouTube transcript")
    
    # Test 2: Podcast would go here if LISTEN_NOTES_API_KEY is available
    # Skipping for now to keep test simple
    
    # Generate report
    print("\n\n" + "="*80)
    print("Generating Report...")
    print("="*80)
    
    report = generate_report(results)
    
    # Save report
    report_file = 'openrouter_benchmark_results.md'
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n✓ Report saved: {report_file}")
    
    # Print summary to console
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        print(f"\n✅ Successful tests: {len(successful)}")
        for r in successful:
            print(f"   {r['model']}: Quality {r['quality_score']}/10, Speed {r['elapsed_seconds']}s")
    
    if failed:
        print(f"\n❌ Failed tests: {len(failed)}")
        for r in failed:
            print(f"   {r['model']}: {r['error']}")
    
    print("\n" + "="*80)
    print(f"✓ Benchmark Complete! Full report: {report_file}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
