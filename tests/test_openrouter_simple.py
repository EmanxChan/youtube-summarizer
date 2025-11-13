#!/usr/bin/env python3
"""
Simple OpenRouter benchmark with sample transcript
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_summarizer import AITranscriptSummarizer

# Sample transcript about AI/ML for testing
SAMPLE_TRANSCRIPT = """
Large language models like GPT work by predicting the next token in a sequence based on patterns learned from massive amounts of text data during training. The model doesn't truly understand language but excels at statistical pattern matching. The transformer architecture enables these models to process entire sequences in parallel using attention mechanisms, which weigh the importance of different words in context.

However, this approach has fundamental limitations. The models are prone to hallucination - confidently generating plausible-sounding but incorrect information. They lack true reasoning capabilities and can't verify facts or maintain consistent logical chains across long conversations. The context window, while impressive at 128K+ tokens for modern models, still constrains the amount of information the model can actively reference.

Training these models requires enormous computational resources and energy. GPT-4 reportedly cost over $100 million to train and uses clusters of thousands of specialized GPUs. This creates a concentration of power among well-funded organizations and raises environmental concerns about the carbon footprint of AI development.

The tradeoff between model size and efficiency is critical. Larger models generally perform better but are expensive to run and slow to respond. Techniques like quantization and distillation can reduce model size by 4-8x while maintaining 95%+ of performance, making deployment more practical. The recent trend toward mixture-of-experts architectures activates only portions of the model for each query, improving efficiency without sacrificing capability.

In practice, prompt engineering becomes crucial because these models are highly sensitive to how questions are framed. The same query phrased differently can yield vastly different quality responses. This brittleness reveals that LLMs are sophisticated pattern matchers rather than genuine intelligences - they excel within their training distribution but struggle with novel situations requiring actual reasoning.
"""

SAMPLE_TITLE = "Understanding Large Language Models: Architecture and Limitations"

# Models to test
MODELS = [
    {
        'name': 'DeepSeek V3.1 Free',
        'provider': 'openrouter',
        'model': 'deepseek/deepseek-chat-v3.1:free',
    },
    {
        'name': 'Kimi K2 0711 Free',
        'provider': 'openrouter',
        'model': 'moonshotai/kimi-k2:free',
    },
    {
        'name': 'Qwen 2.5 7B Local',
        'provider': 'ollama',
        'model': 'qwen2.5:7b-instruct-q4_K_M',
    }
]

def test_model(model_config):
    """Test a single model"""
    print(f"\n{'='*70}")
    print(f"Testing: {model_config['name']}")
    print(f"{'='*70}")
    
    try:
        start_time = time.time()
        
        summarizer = AITranscriptSummarizer(
            provider=model_config['provider'],
            model=model_config['model']
        )
        
        print("  Generating key takeaways...")
        takeaways = summarizer.generate_key_takeaways(
            SAMPLE_TRANSCRIPT, 
            SAMPLE_TITLE, 
            count=5
        )
        
        print("  Generating executive summary...")
        summary = summarizer.generate_executive_summary(
            SAMPLE_TRANSCRIPT,
            SAMPLE_TITLE,
            word_count=150
        )
        
        elapsed = time.time() - start_time
        
        result = {
            'model': model_config['name'],
            'provider': model_config['provider'],
            'elapsed': round(elapsed, 2),
            'takeaways': takeaways,
            'summary': summary,
            'success': True
        }
        
        print(f"✓ Completed in {elapsed:.1f}s")
        print(f"  Takeaways: {len(takeaways)}")
        print(f"  Summary length: {len(summary.split())} words")
        
        return result
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return {
            'model': model_config['name'],
            'success': False,
            'error': str(e)
        }

def score_quality(takeaways):
    """Simple quality scoring"""
    score = 0
    
    # Check for depth markers (good)
    depth_markers = ['tradeoff', 'constraint', 'limitation', 'because', 'however', 'whereas', 'while']
    # Check for generic phrases (bad)
    generic = ['improve', 'better', 'faster', 'helps', 'allows', 'learn', 'master']
    
    for takeaway in takeaways:
        lower = takeaway.lower()
        score += sum(2 for marker in depth_markers if marker in lower)
        score -= sum(0.5 for phrase in generic if phrase in lower)
        
        # Length check
        words = len(takeaway.split())
        if 25 <= words <= 50:
            score += 1
        elif words < 15:
            score -= 0.5
    
    # Normalize to 0-10
    normalized = 5 + (score / max(len(takeaways), 1))
    return max(0, min(10, round(normalized, 1)))

def print_results(results):
    """Print comparison results"""
    print("\n" + "="*70)
    print("BENCHMARK RESULTS")
    print("="*70 + "\n")
    
    successful = [r for r in results if r['success']]
    
    if not successful:
        print("No successful tests to compare")
        return
    
    # Print comparison table
    print("| Model | Speed | Quality | Takeaways |")
    print("|-------|-------|---------|-----------|")
    
    for r in successful:
        quality = score_quality(r['takeaways'])
        print(f"| {r['model'][:25]:<25} | {r['elapsed']}s | {quality}/10 | {len(r['takeaways'])} |")
    
    # Print detailed outputs
    for r in successful:
        quality = score_quality(r['takeaways'])
        print(f"\n{'='*70}")
        print(f"{r['model']}")
        print(f"Speed: {r['elapsed']}s | Quality: {quality}/10")
        print(f"{'='*70}\n")
        
        print("**Key Takeaways:**\n")
        for i, t in enumerate(r['takeaways'], 1):
            print(f"{i}. {t}\n")
        
        print("\n**Executive Summary:**\n")
        print(f"{r['summary']}\n")
    
    # Recommendation
    best = max(successful, key=lambda r: score_quality(r['takeaways']))
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    print(f"\n🏆 Best Model: {best['model']}")
    print(f"   Quality Score: {score_quality(best['takeaways'])}/10")
    print(f"   Speed: {best['elapsed']}s")
    print(f"\n   Reason: Best balance of insight depth and performance")
    print("="*70 + "\n")

def main():
    os.environ['OPENROUTER_API_KEY'] = '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'
    
    print("="*70)
    print("OpenRouter Model Comparison Test")
    print("="*70)
    print(f"\nSample content: {SAMPLE_TITLE}")
    print(f"Transcript length: {len(SAMPLE_TRANSCRIPT)} characters\n")
    
    results = []
    
    for model in MODELS:
        result = test_model(model)
        results.append(result)
        time.sleep(2)  # Rate limit buffer
    
    print_results(results)
    
    # Save to file
    report_file = 'openrouter_comparison.md'
    with open(report_file, 'w') as f:
        f.write(f"# OpenRouter Model Comparison\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Test Content\n{SAMPLE_TITLE}\n\n")
        
        for r in results:
            if r['success']:
                quality = score_quality(r['takeaways'])
                f.write(f"\n## {r['model']}\n\n")
                f.write(f"- Speed: {r['elapsed']}s\n")
                f.write(f"- Quality Score: {quality}/10\n\n")
                f.write(f"### Key Takeaways\n\n")
                for i, t in enumerate(r['takeaways'], 1):
                    f.write(f"{i}. {t}\n\n")
                f.write(f"### Executive Summary\n\n{r['summary']}\n\n")
    
    print(f"Full report saved to: {report_file}")

if __name__ == "__main__":
    main()
