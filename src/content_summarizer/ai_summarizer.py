#!/usr/bin/env python3
"""
AI-powered summarization module for YouTube transcripts.
Supports OpenAI, Anthropic Claude, and Ollama.
"""

import os
import json
import sys
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import tiktoken


class AITranscriptSummarizer:
    """AI-powered summarization for YouTube transcripts"""
    
    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        """
        Initialize AI summarizer with specified provider.
        
        Args:
            provider: One of 'openai', 'anthropic', 'deepseek', 'ollama', or 'none'
            model: Specific model to use (optional)
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = None
        self.client = None
        
        # Initialize based on provider
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "deepseek":
            self._init_deepseek()
        elif self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "ollama":
            self._init_ollama()
        elif self.provider == "groq":
            self._init_groq()
        elif self.provider != "none":
            raise ValueError(f"Unknown provider: {provider}")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            
            # Try to get API key from environment or config
            self.api_key = os.getenv('OPENAI_API_KEY')
            
            if not self.api_key:
                # Try to load from config file
                config_path = Path.home() / '.youtube_summarizer' / 'config.json'
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        self.api_key = config.get('openai_api_key')
            
            if not self.api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            
            self.client = openai.OpenAI(api_key=self.api_key)
            self.model = self.model or "gpt-4o-mini"  # Default to cheaper, faster model
            
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
    
    def _init_deepseek(self):
        """Initialize DeepSeek client (OpenAI-compatible)"""
        try:
            import openai
            
            # Try to get API key from environment or config
            self.api_key = os.getenv('DEEPSEEK_API_KEY')
            
            if not self.api_key:
                # Try to load from config file
                config_path = Path.home() / '.youtube_summarizer' / 'config.json'
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        self.api_key = config.get('deepseek_api_key')
            
            if not self.api_key:
                raise ValueError("DeepSeek API key not found. Set DEEPSEEK_API_KEY environment variable.")
            
            # DeepSeek uses OpenAI-compatible API with custom base URL
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
            self.model = self.model or "deepseek-chat"  # Default model
            
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
    
    def _init_anthropic(self):
        """Initialize Anthropic Claude client"""
        try:
            import anthropic
            
            self.api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not self.api_key:
                config_path = Path.home() / '.youtube_summarizer' / 'config.json'
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        self.api_key = config.get('anthropic_api_key')
            
            if not self.api_key:
                raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")
            
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = self.model or "claude-3-haiku-20240307"  # Cheaper, faster model
            
        except ImportError:
            raise ImportError("Anthropic library not installed. Run: pip install anthropic")
    
    def _init_ollama(self):
        """Initialize Ollama client for local models"""
        try:
            import requests
            self.base_url = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            self.model = self.model or "llama3.2:3b"  # Default to Llama 3.2 for testing
            # Test connection
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=2)
                if response.status_code != 200:
                    raise ConnectionError("Cannot connect to Ollama. Make sure Ollama.app is running.")
            except requests.exceptions.RequestException:
                raise ConnectionError("Ollama not running. Please launch Ollama.app from Applications.")
        except ImportError:
            raise ImportError("Requests library not installed. Run: pip install requests")
    
    def _init_groq(self):
        """Initialize Groq client (OpenAI-compatible API)"""
        try:
            import openai
            
            # Try to get API key from environment or config
            self.api_key = os.getenv('GROQ_API_KEY')
            
            if not self.api_key:
                # Try to load from config file
                config_path = Path.home() / '.youtube_summarizer' / 'config.json'
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        self.api_key = config.get('groq_api_key')
            
            if not self.api_key:
                raise ValueError("Groq API key not found. Set GROQ_API_KEY environment variable.")
            
            # Groq uses OpenAI-compatible API with custom base URL
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model = self.model or "llama-3.1-8b-instant"  # Default to fast model
            
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text for rate limiting"""
        if self.provider in ["openai", "deepseek", "groq"]:
            try:
                encoder = tiktoken.encoding_for_model(self.model)
            except:
                encoder = tiktoken.get_encoding("cl100k_base")
            return len(encoder.encode(text))
        else:
            # Rough estimate for other providers
            return len(text.split()) * 1.3
    
    def generate_key_takeaways(self, transcript: str, video_title: str, 
                               count: int = 5) -> List[str]:
        """
        Generate high-level conceptual insights from transcript.
        
        Returns:
            List of insight strings
        """
        # Limit transcript to avoid token limits
        max_chars = 12000  # Roughly 3000 tokens
        if len(transcript) > max_chars:
            transcript = transcript[:max_chars]
        
        prompt = f"""You are a world-class analyst who extracts profound, non-obvious insights from educational content. Your insights reveal deeper patterns, tradeoffs, and strategic implications that most people miss.

Title: {video_title}
Content: {transcript}

Generate exactly {count} insights that capture the deepest concepts, principles, and strategic implications from this content.

CRITICAL REQUIREMENTS - Each insight MUST:

1. **Reveal underlying mechanisms** - Explain WHY something works at a fundamental level, not just WHAT happens
2. **Include tradeoffs or limitations** - Show the costs, constraints, or boundaries (nothing is universally good)
3. **Provide non-obvious implications** - Surface surprising consequences or counterintuitive aspects
4. **Use specific examples** - Reference concrete situations or scenarios from the content
5. **Be memorable and distinctive** - Should stick in someone's mind, not be generic
6. **Show strategic context** - Explain when/where this matters and when it doesn't

LENGTH: 30-40 words per insight (2-3 sentences)

AVOID AT ALL COSTS:
- Generic truisms ("X improves Y", "Using Z helps achieve better results")
- Obvious statements anyone would know
- Action verbs (Learn, Master, Implement, Use)
- Vague platitudes without specifics
- Surface-level descriptions

QUALITY TEST:
Ask yourself: "Would an expert in this field find this insight valuable, or would they say 'obviously'?"
Only include insights that pass this test.

EXAMPLES OF EXCELLENT INSIGHTS:

BAD (Generic):
"Planning with AI is more efficient than jumping straight to coding for complex features."

GOOD (Insightful):
"AI code assistants front-load cognitive work—requiring extensive upfront context through research strategies—because they lack the implicit codebase understanding developers build through daily immersion, creating a fundamental inversion where setup investment determines long-term leverage rather than immediate productivity."

---

BAD (Generic):
"Eight research strategies help an AI learn patterns and preferences in a codebase."

GOOD (Insightful):
"Multiple research strategies exist because no single approach captures both explicit patterns (what the code does) and implicit taste (how the team prefers to do it), requiring AI systems to triangulate understanding through complementary lenses much like anthropologists studying a culture through multiple methodologies."

---

BAD (Generic):
"Continually refining and expanding the AI's knowledge base improves its performance over time."

GOOD (Insightful):
"AI code assistants demonstrate a compound learning curve where initial context-gathering creates diminishing returns on individual queries but exponential improvements in decision quality over time, inverting the typical tool learning curve where early investment yields immediate payoff."

---

Now generate {count} insights that match this EXCELLENT quality standard. Each insight should be profound enough that an expert would pause and think "I hadn't considered it that way."

Return ONLY the {count} insights, one per line, without numbers or bullet points."""

        try:
            if self.provider in ["openai", "deepseek", "groq"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a world-class analyst who reveals profound insights and non-obvious patterns."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,
                    max_tokens=800
                )
                content = response.choices[0].message.content
                
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.6
                )
                content = response.content[0].text
                
            elif self.provider == "ollama":
                import requests
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                content = response.json()["response"]
            
            else:
                return []
            
            # Parse the response into individual takeaways
            raw_lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
            
            # Clean up and format
            cleaned_takeaways = []
            for line in raw_lines:
                # Remove leading numbers, bullets, asterisks, etc.
                takeaway = line.lstrip('0123456789.-•* \t')
                # Also handle formats like "1)" or "1."
                import re
                takeaway = re.sub(r'^\d+[\.\)]\s*', '', takeaway)
                if takeaway and len(takeaway) > 10:  # Skip empty or too-short lines
                    cleaned_takeaways.append(takeaway)
                if len(cleaned_takeaways) >= count:
                    break
            
            return cleaned_takeaways[:count]
            
        except Exception as e:
            print(f"Error generating takeaways: {e}", file=sys.stderr)
            return []
    
    def generate_executive_summary(self, transcript: str, video_title: str, 
                                  word_count: int = 200) -> str:
        """
        Generate a coherent executive summary of the video.
        
        Returns:
            Executive summary string
        """
        # Limit transcript to avoid token limits
        max_chars = 12000
        if len(transcript) > max_chars:
            # Take beginning, middle, and end for better coverage
            third = max_chars // 3
            transcript = transcript[:third] + " [...] " + \
                        transcript[len(transcript)//2 - third//2:len(transcript)//2 + third//2] + \
                        " [...] " + transcript[-third:]
        
        # Calculate words per paragraph for guidance
        words_per_paragraph = word_count // 4
        
        prompt = f"""You are an expert at creating executive summaries for educational and technical content.

Video Title: {video_title}
Transcript: {transcript}

Create an executive summary that delivers AT LEAST {word_count} words in four cohesive paragraphs (approximately {words_per_paragraph} words per paragraph). Do not stop early; add detail until the minimum word count is reached.

Structure your summary with these four paragraphs:

1. **Introduction** (~{words_per_paragraph} words): Open with what this content teaches and why it matters. Provide context and the core value proposition.

2. **Core Themes** (~{words_per_paragraph} words): Explain the 3-4 main concepts, techniques, or arguments covered. Add supporting details and examples to reach the target length.

3. **Practical Applications** (~{words_per_paragraph} words): Describe the practical applications, benefits, and real-world implications. Include specific use cases or outcomes.

4. **Closing Recommendation** (~{words_per_paragraph} words): Conclude with who would benefit most from this content and what they will gain. Summarize the key value.

CRITICAL REQUIREMENTS:
- Write AT LEAST {word_count} words total - do not stop short
- Use four cohesive paragraphs with smooth transitions
- Focus on concepts and value, NOT play-by-play actions
- Do not mention "the video" or "the speaker" - write as if describing the topic directly
- Use clear, professional language with sufficient detail to reach the word count
- Make it informative enough that someone could decide whether to watch based on your summary

Return ONLY the summary text with paragraph breaks, no headers or labels."""

        try:
            if self.provider in ["openai", "deepseek", "groq"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert technical writer."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=word_count * 2  # Tokens != words, give some buffer
                )
                return response.choices[0].message.content.strip()
                
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=word_count * 2,
                    temperature=0.7
                )
                return response.content[0].text.strip()
                
            elif self.provider == "ollama":
                import requests
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                return response.json()["response"].strip()
            
            else:
                return ""
                
        except Exception as e:
            print(f"Error generating summary: {e}", file=sys.stderr)
            return ""
    
    def generate_next_steps(self, transcript: str, video_title: str, 
                           takeaways: List[str]) -> List[str]:
        """
        Generate actionable next steps based on the video content.
        
        Returns:
            List of next step strings
        """
        # Use takeaways to inform next steps
        takeaways_text = "\n".join(f"- {t}" for t in takeaways) if takeaways else "N/A"
        
        prompt = f"""Based on this educational content, suggest 3 specific next steps for the viewer.

Video Title: {video_title}
Key Takeaways:
{takeaways_text}

Generate 3 actionable next steps that:
1. Build on what was learned in the video
2. Include specific resources, tools, or exercises
3. Have clear success metrics or outcomes

Format as actionable tasks, one per line.

Examples:
- "Practice Cursor shortcuts for 15 minutes daily using the built-in tutorial mode"
- "Build a sample TODO app using the AI-assisted workflow demonstrated"
- "Join the Cursor Discord community to share your first AI-coded project"

Return ONLY the 3 next steps, one per line."""

        try:
            if self.provider in ["openai", "deepseek", "groq"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=200
                )
                content = response.choices[0].message.content
                
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.7
                )
                content = response.content[0].text
                
            elif self.provider == "ollama":
                import requests
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                content = response.json()["response"]
            
            else:
                return []
            
            # Parse response
            steps = [line.strip().lstrip('0123456789.-•* \t') 
                    for line in content.strip().split('\n') 
                    if line.strip()]
            
            return steps[:3]
            
        except Exception as e:
            print(f"Error generating next steps: {e}", file=sys.stderr)
            return []
    
    def is_available(self) -> bool:
        """Check if AI provider is properly configured and available"""
        if self.provider == "none":
            return False
        return self.client is not None or self.provider == "ollama"


def test_summarizer():
    """Test the AI summarizer with a sample transcript"""
    sample_transcript = """
    This video is about learning to use Cursor IDE for AI-assisted coding.
    First, we'll cover the basic interface and how to set up your workspace.
    Then I'll show you the keyboard shortcuts that will make you much faster.
    The AI features include code completion, refactoring, and debugging assistance.
    You can use natural language to describe what you want to build.
    The AI will generate the code for you, but you should always review it.
    Common mistakes include not being specific enough in your prompts.
    By the end, you'll be able to build applications much faster than before.
    """
    
    try:
        summarizer = AITranscriptSummarizer(provider="openai")
        
        print("Testing AI Summarizer...")
        print("-" * 50)
        
        # Test key takeaways
        takeaways = summarizer.generate_key_takeaways(
            sample_transcript, 
            "Cursor IDE Tutorial", 
            count=3
        )
        print("Key Takeaways:")
        for i, takeaway in enumerate(takeaways, 1):
            print(f"{i}. {takeaway}")
        
        print("\n" + "-" * 50)
        
        # Test executive summary
        summary = summarizer.generate_executive_summary(
            sample_transcript,
            "Cursor IDE Tutorial",
            word_count=100
        )
        print("Executive Summary:")
        print(summary)
        
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    test_summarizer()
