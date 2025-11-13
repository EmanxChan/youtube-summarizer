## Complete OpenRouter Testing Plan

### Objective
Test and compare **DeepSeek V3.1 (free)** vs **Kimi K2 0711 (free)** vs **Local Qwen 7B** using both YouTube and podcast content to determine the best model for your "profound insights" summarization use case.

---

## Phase 1: Integration Setup

### 1.1 Add OpenRouter Provider to `ai_summarizer.py`

**New method to add:**
```python
def _init_openrouter(self):
    """Initialize OpenRouter client (OpenAI-compatible)"""
    try:
        import openai
        
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        
        if not self.api_key:
            config_path = Path.home() / '.youtube_summarizer' / 'config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get('openrouter_api_key')
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable.")
        
        # OpenRouter uses OpenAI-compatible API
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Default to DeepSeek V3.1 free
        self.model = self.model or "deepseek/deepseek-chat-v3.1:free"
        
    except ImportError:
        raise ImportError("OpenAI library not installed. Run: pip install openai")
```

**Update `__init__` method:**
- Add `elif self.provider == "openrouter": self._init_openrouter()`

**API call methods:**
- Already compatible! `self.provider in ["openai", "deepseek"]` → change to `["openai", "deepseek", "openrouter"]`

---

### 1.2 Update `youtube_slash_command.py`

**Line 2318 - Add to choices:**
```python
parser.add_argument('--ai-provider', 
    choices=['openai', 'anthropic', 'deepseek', 'ollama', 'openrouter', 'none'],
    default='deepseek',
    help='AI provider for enhanced summarization (default: deepseek)')
```

---

## Phase 2: Create Test Scripts

### 2.1 Test Comparison Script: `test_openrouter_benchmark.py`

**Purpose:** Run same content through all 3 models and compare results

**Key features:**
- Tests both YouTube video and podcast
- Measures: quality scores, speed, token usage, insight depth
- Outputs detailed comparison report

**Structure:**
```python
#!/usr/bin/env python3
"""
Benchmark OpenRouter models (DeepSeek V3.1, Kimi K2) vs local Qwen 7B
"""

import os
import sys
import time
import json
from datetime import datetime
from ai_summarizer import AITranscriptSummarizer
from youtube_slash_command import get_youtube_transcript, handle_podcast_content

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

# Test content (will use YouTube + podcast)
TEST_YOUTUBE = "https://www.youtube.com/watch?v=..." # Lightweight video (~10 min)
TEST_PODCAST = "..." # Podcast episode URL

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
    generic_phrases = ['improve', 'better', 'faster', 'learn', 'master', 'use']
    depth_markers = ['tradeoff', 'constraint', 'limitation', 'because', 'when', 'why']
    
    for takeaway in takeaways:
        total += 1
        # Deduct for generic phrases
        if any(phrase in takeaway.lower() for phrase in generic_phrases):
            score -= 1
        # Add for depth markers
        if any(marker in takeaway.lower() for marker in depth_markers):
            score += 2
        # Length check (30-40 words = good)
        word_count = len(takeaway.split())
        if 25 <= word_count <= 50:
            score += 1
    
    # Normalize to 0-10 scale
    return max(0, min(10, 5 + (score / max(total, 1)) * 2))

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
        takeaways = summarizer.generate_key_takeaways(transcript, title, count=5)
        
        # Generate summary
        summary = summarizer.generate_executive_summary(transcript, title, word_count=200)
        
        elapsed = time.time() - start_time
        
        # Score quality
        quality_score = score_quality(takeaways, summary)
        
        result = {
            'model': model_config['name'],
            'params': model_config['params'],
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
        
        return result
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return {
            'model': model_config['name'],
            'content_type': content_type,
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
        report.append(f"\n## {content_type} Results\n")
        report.append("| Model | Quality | Speed | Takeaways | Summary Words |")
        report.append("|-------|---------|-------|-----------|---------------|")
        
        for r in group:
            if r['success']:
                report.append(f"| {r['model']} | {r['quality_score']}/10 | {r['elapsed_seconds']}s | {r['takeaways_count']} | {r['summary_length']} |")
            else:
                report.append(f"| {r['model']} | FAILED | - | - | {r['error'][:30]}... |")
    
    # Best model recommendation
    successful = [r for r in results if r['success']]
    if successful:
        best = max(successful, key=lambda x: x['quality_score'])
        report.append(f"\n## Recommendation\n")
        report.append(f"**Best Model:** {best['model']}")
        report.append(f"- Quality Score: {best['quality_score']}/10")
        report.append(f"- Average Speed: {best['elapsed_seconds']}s")
        report.append(f"- Reason: Best balance of insight depth for your 'profound insights' use case")
    
    # Detailed outputs
    report.append(f"\n## Detailed Outputs\n")
    for r in results:
        if r['success']:
            report.append(f"\n### {r['model']} - {r['content_type']}\n")
            report.append(f"**Quality Score:** {r['quality_score']}/10\n")
            report.append(f"**Key Takeaways:**\n")
            for i, t in enumerate(r['takeaways'], 1):
                report.append(f"{i}. {t}\n")
            report.append(f"\n**Executive Summary:**\n{r['summary']}\n")
    
    return '\n'.join(report)

def main():
    """Run full benchmark"""
    # Your API key
    os.environ['OPENROUTER_API_KEY'] = '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'
    
    print("="*80)
    print("OpenRouter Model Benchmark")
    print("="*80)
    print("\nTesting Models:")
    for m in MODELS_TO_TEST:
        print(f"  - {m['name']} ({m['params']})")
    
    results = []
    
    # Test 1: YouTube video (find lightweight one)
    print("\n\n--- PHASE 1: YouTube Video Test ---")
    # TODO: Select random lightweight video
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Placeholder
    video_id = youtube_url.split('v=')[1].split('&')[0]
    transcript, title = get_youtube_transcript(video_id)
    
    if transcript:
        for model_config in MODELS_TO_TEST:
            result = run_single_test(model_config, 'youtube', youtube_url, transcript, title)
            results.append(result)
            time.sleep(2)  # Rate limit buffer
    
    # Test 2: Podcast (use Listen Notes to find one)
    print("\n\n--- PHASE 2: Podcast Test ---")
    # TODO: Search for lightweight podcast episode
    # Will use your Listen Notes API
    
    # Generate report
    report = generate_report(results)
    
    # Save report
    with open('openrouter_benchmark_results.md', 'w') as f:
        f.write(report)
    
    print("\n\n" + "="*80)
    print("✓ Benchmark Complete!")
    print(f"Report saved: openrouter_benchmark_results.md")
    print("="*80)

if __name__ == "__main__":
    main()
```

---

### 2.2 Content Selection Helper: `find_test_content.py`

**Purpose:** Find suitable test content (10-15 min YouTube + podcast)

```python
#!/usr/bin/env python3
"""Find lightweight test content for benchmarking"""

import sys
from listen_notes_client import ListenNotesClient
from youtube_transcript_api import YouTubeTranscriptApi

# Suggested lightweight YouTube videos (tech/educational, ~10 min)
YOUTUBE_CANDIDATES = [
    "https://www.youtube.com/watch?v=0qo78R_yYFA",  # Docker in 100 Seconds
    "https://www.youtube.com/watch?v=gd6rYPfTjgk",  # Kubernetes in 100 Seconds
    "https://www.youtube.com/watch?v=tc4ROCJYbm0",  # TypeScript in 100 Seconds
]

def find_podcast_episode():
    """Find a lightweight podcast episode using Listen Notes"""
    client = ListenNotesClient()
    
    # Search for tech podcasts with shorter episodes
    results = client.search_podcast("programming tutorial", limit=5)
    
    print("\nAvailable Podcast Episodes:")
    for i, podcast in enumerate(results[:3], 1):
        episodes = client.get_podcast_episodes(podcast['id'], limit=1)
        if episodes:
            ep = episodes[0]
            duration_min = ep['duration'] // 60
            print(f"{i}. {ep['podcast_title']} - {ep['title']}")
            print(f"   Duration: {duration_min} min")
            print(f"   Audio URL: {ep['audio_url'][:50]}...")
            return ep
    
    return None

def main():
    print("Finding test content...\n")
    
    # Check YouTube candidates
    print("YouTube Video Candidates:")
    for url in YOUTUBE_CANDIDATES[:3]:
        video_id = url.split('v=')[1]
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['en'])
            data = transcript.fetch()
            duration = max([item['start'] + item['duration'] for item in data])
            print(f"✓ {url}")
            print(f"  Duration: {duration/60:.1f} min")
            print(f"  Transcript: {len(data)} segments\n")
        except Exception as e:
            print(f"✗ {url}: {e}\n")
    
    # Find podcast
    print("\nSearching for podcast...")
    episode = find_podcast_episode()

if __name__ == "__main__":
    main()
```

---

## Phase 3: Execution Plan

### Step 1: Set Environment Variables
```bash
export OPENROUTER_API_KEY="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"
export LISTEN_NOTES_API_KEY="your-listen-notes-key"  # If you have one
```

### Step 2: Find Test Content
```bash
python3 find_test_content.py
# Will output suitable YouTube + podcast URLs
```

### Step 3: Run Individual Tests (Manual)
```bash
# Test DeepSeek V3.1
python3 youtube_slash_command.py "YOUTUBE_URL" \
  --ai-provider openrouter \
  --ai-model deepseek/deepseek-chat-v3.1:free

# Test Kimi K2
python3 youtube_slash_command.py "YOUTUBE_URL" \
  --ai-provider openrouter \
  --ai-model moonshotai/kimi-k2:free

# Test local Qwen (current setup)
python3 youtube_slash_command.py "YOUTUBE_URL" \
  --ai-provider ollama
```

### Step 4: Run Full Benchmark
```bash
python3 test_openrouter_benchmark.py
# Automatically tests all models on both content types
# Generates: openrouter_benchmark_results.md
```

---

## Phase 4: Evaluation Criteria

### Quality Scoring (Your Use Case)

**What you need (based on your prompts):**
1. **Non-obvious insights** - Not generic "X improves Y"
2. **Tradeoff identification** - Costs, constraints, limitations
3. **Technical depth** - Mechanisms, not just descriptions
4. **Concrete examples** - Specific scenarios referenced
5. **Strategic context** - When/where it matters

**Scoring rubric:**
- 9-10: Profound insights, expert-level depth
- 7-8: Good insights, some depth
- 5-6: Adequate, but some generic takeaways
- 3-4: Mostly generic statements
- 1-2: Superficial, obvious content

### Speed Considerations
- **DeepSeek V3.1:** May be slower (671B params) but reasoning mode
- **Kimi K2:** Should be faster (MoE efficiency)
- **Qwen 7B Local:** Fast but causes Mac overheating

---

## Expected Outputs

### 1. Benchmark Report: `openrouter_benchmark_results.md`

**Contains:**
- Performance comparison table
- Quality scores for each model
- Speed measurements
- Full takeaways and summaries from each model
- Final recommendation

### 2. Model Rankings

**Predicted results based on specs:**

| Criterion | DeepSeek V3.1 | Kimi K2 | Qwen 7B |
|-----------|---------------|---------|---------|
| Insight Depth | 8-9/10 | 7-8/10 | 6-7/10 |
| Speed | Slower (~15s) | Fast (~8s) | Fast (~10s) |
| Technical Accuracy | Excellent | Very Good | Good |
| Cost | Free | Free | $0 (local) |
| Mac Heat | None | None | High ❌ |

**Expected winner for your use case: DeepSeek V3.1**
- Reasoning mode designed for depth
- 671B params = better conceptual understanding
- Free tier sufficient for your volume

---

## What You Need to Provide

1. ✅ **OpenRouter API Key** - Already provided
2. ⚠️ **Listen Notes API Key** - Do you have one? (Optional - can test YouTube only)
3. ✅ **Test Video Preference** - Will auto-select lightweight content
4. ✅ **Test Podcast** - Can search automatically if Listen Notes available

---

## Files to Create/Modify

**Create:**
1. `test_openrouter_benchmark.py` - Main benchmark script
2. `find_test_content.py` - Content selection helper
3. `openrouter_benchmark_results.md` - Output report (generated)

**Modify:**
1. `ai_summarizer.py` - Add `_init_openrouter()` method and update conditionals
2. `youtube_slash_command.py` - Add `'openrouter'` to provider choices

**No modifications needed:**
- `requirements_ai.txt` - Already has `openai>=1.12.0`
- Existing summarization logic - Works with OpenRouter

---

## Success Criteria

✅ Both OpenRouter models successfully generate summaries  
✅ Quality comparison clearly shows differences  
✅ Speed measurements accurate  
✅ Clear winner identified for "profound insights" use case  
✅ No Mac overheating (cloud-based models)  
✅ Report actionable for deployment decision  

---

## Timeline

- **Integration:** 10 min (add OpenRouter provider)
- **Content selection:** 5 min (auto or manual)
- **Benchmark execution:** 5-10 min (3 models × 2 content types)
- **Report generation:** Automatic
- **Total:** ~20-30 minutes

---

Ready to proceed with implementation?