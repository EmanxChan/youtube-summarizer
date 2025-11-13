#!/usr/bin/env python3
"""
Test Groq models vs Local Qwen 7B
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
        'name': 'Groq Llama 3.3 70B',
        'provider': 'groq',
        'model': 'llama-3.3-70b-versatile',
        'params': '70B (best quality)'
    },
    {
        'name': 'Groq Llama 3.1 8B',
        'provider': 'groq',
        'model': 'llama-3.1-8b-instant',
        'params': '8B (fastest)'
    },
    {
        'name': 'Qwen 2.5 7B Local',
        'provider': 'ollama',
        'model': 'qwen2.5:7b-instruct-q4_K_M',
        'params': '7B (local)'
    }
]

def test_model(model_config):
    """Test a single model"""
    print(f"\n{'='*70}")
    print(f"Testing: {model_config['name']} ({model_config['params']})")
    print(f"{'='*70}")
    
    try:
        start_time = time.time()
        
        summarizer = AITranscriptSummarizer(
            provider=model_config['provider'],
            model=model_config['model']
        )
        
        print("  Generating key takeaways...")
        takeaways_start = time.time()
        takeaways = summarizer.generate_key_takeaways(
            SAMPLE_TRANSCRIPT, 
            SAMPLE_TITLE, 
            count=5
        )
        takeaways_time = time.time() - takeaways_start
        
        print("  Generating executive summary...")
        summary_start = time.time()
        summary = summarizer.generate_executive_summary(
            SAMPLE_TRANSCRIPT,
            SAMPLE_TITLE,
            word_count=150
        )
        summary_time = time.time() - summary_start
        
        elapsed = time.time() - start_time
        
        result = {
            'model': model_config['name'],
            'provider': model_config['provider'],
            'params': model_config['params'],
            'total_time': round(elapsed, 2),
            'takeaways_time': round(takeaways_time, 2),
            'summary_time': round(summary_time, 2),
            'takeaways': takeaways,
            'summary': summary,
            'success': True
        }
        
        print(f"✓ Completed in {elapsed:.1f}s")
        print(f"  Takeaways: {len(takeaways)} ({takeaways_time:.1f}s)")
        print(f"  Summary: {len(summary.split())} words ({summary_time:.1f}s)")
        
        return result
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'model': model_config['name'],
            'success': False,
            'error': str(e)
        }

def score_quality(takeaways):
    """Simple quality scoring based on insight depth"""
    score = 0
    
    # Check for depth markers (good)
    depth_markers = ['tradeoff', 'constraint', 'limitation', 'because', 'however', 'whereas', 'while', 'although']
    # Check for generic phrases (bad)
    generic = ['improve', 'better', 'faster', 'helps', 'allows', 'learn', 'master', 'use']
    
    for takeaway in takeaways:
        lower = takeaway.lower()
        # Add points for depth
        score += sum(2 for marker in depth_markers if marker in lower)
        # Subtract for generic
        score -= sum(0.5 for phrase in generic if phrase in lower)
        
        # Length check (30-40 words is ideal)
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
    print("GROQ vs LOCAL QWEN BENCHMARK RESULTS")
    print("="*70 + "\n")
    
    successful = [r for r in results if r['success']]
    
    if not successful:
        print("❌ No successful tests to compare")
        return
    
    # Print comparison table
    print("| Model | Speed | Quality | Takeaways |")
    print("|-------|-------|---------|-----------|")
    
    for r in successful:
        quality = score_quality(r['takeaways'])
        print(f"| {r['model'][:28]:<28} | {r['total_time']}s | {quality}/10 | {len(r['takeaways'])} |")
    
    print("\n")
    
    # Print detailed outputs
    for r in successful:
        quality = score_quality(r['takeaways'])
        print(f"\n{'='*70}")
        print(f"{r['model']} - {r['params']}")
        print(f"Speed: {r['total_time']}s | Quality: {quality}/10")
        print(f"{'='*70}\n")
        
        print("**Key Takeaways:**\n")
        for i, t in enumerate(r['takeaways'], 1):
            print(f"{i}. {t}\n")
        
        print("\n**Executive Summary:**\n")
        print(f"{r['summary']}\n")
    
    # Speed analysis
    print("\n" + "="*70)
    print("SPEED ANALYSIS")
    print("="*70)
    groq_models = [r for r in successful if r['provider'] == 'groq']
    local_models = [r for r in successful if r['provider'] == 'ollama']
    
    if groq_models and local_models:
        avg_groq = sum(r['total_time'] for r in groq_models) / len(groq_models)
        avg_local = sum(r['total_time'] for r in local_models) / len(local_models)
        speedup = avg_local / avg_groq
        print(f"\nGroq average: {avg_groq:.1f}s")
        print(f"Local average: {avg_local:.1f}s")
        print(f"⚡ Groq is {speedup:.1f}x faster than local!")
    
    # Recommendation
    best = max(successful, key=lambda r: (score_quality(r['takeaways']), -r['total_time']))
    print("\n" + "="*70)
    print("🏆 RECOMMENDATION")
    print("="*70)
    print(f"\nBest Model: {best['model']}")
    print(f"Quality Score: {score_quality(best['takeaways'])}/10")
    print(f"Speed: {best['total_time']}s")
    print(f"Provider: {best['provider']}")
    
    if best['provider'] == 'groq':
        print(f"\n✨ Groq wins! Benefits:")
        print(f"   - Much faster than local")
        print(f"   - No Mac overheating")
        print(f"   - FREE tier (7K requests/day)")
        print(f"   - Better or equal quality")
    
    print("="*70 + "\n")

def main():
    # Set Groq API key
    os.environ['GROQ_API_KEY'] = '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'
    
    print("="*70)
    print("🚀 GROQ MODEL BENCHMARK")
    print("="*70)
    print(f"\nTest Content: {SAMPLE_TITLE}")
    print(f"Transcript: {len(SAMPLE_TRANSCRIPT)} characters")
    print(f"Models to test: {len(MODELS)}\n")
    
    results = []
    
    for model in MODELS:
        result = test_model(model)
        results.append(result)
        time.sleep(1)  # Brief pause between tests
    
    print_results(results)
    
    # Save to file
    report_file = 'groq_benchmark_results.md'
    with open(report_file, 'w') as f:
        f.write(f"# Groq vs Local Qwen Benchmark\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Test Content\n{SAMPLE_TITLE}\n\n")
        
        for r in results:
            if r['success']:
                quality = score_quality(r['takeaways'])
                f.write(f"\n## {r['model']} - {r['params']}\n\n")
                f.write(f"- Speed: {r['total_time']}s\n")
                f.write(f"- Quality Score: {quality}/10\n")
                f.write(f"- Provider: {r['provider']}\n\n")
                f.write(f"### Key Takeaways\n\n")
                for i, t in enumerate(r['takeaways'], 1):
                    f.write(f"{i}. {t}\n\n")
                f.write(f"### Executive Summary\n\n{r['summary']}\n\n")
    
    print(f"📄 Full report saved to: {report_file}")

if __name__ == "__main__":
    main()
