#!/usr/bin/env python3
"""
AI-powered summarization module for YouTube transcripts.
Supports OpenAI, Anthropic Claude, and Ollama.
"""

import os
import json
import sys
import time
import re
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import tiktoken


# Groq model fallback chain (largest to smallest)
GROQ_MODEL_FALLBACK_CHAIN = [
    "llama-3.3-70b-versatile",      # Best quality, highest token usage
    "llama-3.1-70b-versatile",      # Fallback large model
    "llama-3.1-8b-instant",         # Fast, low token usage
    "llama-3.2-3b-preview",         # Smallest, emergency fallback
]


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    def __init__(self, message, retry_after=None, model=None):
        super().__init__(message)
        self.retry_after = retry_after  # Seconds to wait
        self.model = model


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
            self.model = self.model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

            # Track original model and fallback state
            self.original_model = self.model
            self.using_fallback = False
            self.fallback_model = None

        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")

    def _groq_api_call_with_fallback(self, messages, temperature=0.7, max_tokens=800):
        """
        Make Groq API call with automatic rate limit handling and model fallback.

        When rate limit is hit:
        1. Log the error clearly
        2. Try smaller models in the fallback chain
        3. If all models fail, raise the error

        Args:
            messages: List of message dicts for chat completion
            temperature: Sampling temperature
            max_tokens: Max tokens in response

        Returns:
            Response content string

        Raises:
            RateLimitError: If all fallback models are also rate limited
        """
        import openai

        # Build list of models to try (current model + smaller fallbacks)
        models_to_try = [self.model]

        # Add fallback models that are smaller than current
        try:
            current_idx = GROQ_MODEL_FALLBACK_CHAIN.index(self.model)
            models_to_try.extend(GROQ_MODEL_FALLBACK_CHAIN[current_idx + 1:])
        except ValueError:
            # Current model not in chain, add all fallbacks
            models_to_try.extend(GROQ_MODEL_FALLBACK_CHAIN)

        # Remove duplicates while preserving order
        seen = set()
        models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

        last_error = None

        for model in models_to_try:
            try:
                if model != self.model:
                    print(f"  ⚠️ RATE LIMIT: Switching from {self.model} to fallback model: {model}", file=sys.stderr)
                    self.using_fallback = True
                    self.fallback_model = model

                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                if model != self.original_model:
                    print(f"  ✓ Fallback model {model} succeeded", file=sys.stderr)

                return response.choices[0].message.content

            except openai.RateLimitError as e:
                last_error = e
                error_msg = str(e)

                # Parse retry time from error message
                retry_after = None
                retry_match = re.search(r'try again in (\d+)m?([\d.]+)?s?', error_msg, re.IGNORECASE)
                if retry_match:
                    minutes = int(retry_match.group(1)) if retry_match.group(1) else 0
                    seconds = float(retry_match.group(2)) if retry_match.group(2) else 0
                    retry_after = minutes * 60 + seconds

                print(f"  ⚠️ RATE LIMIT on {model}: {error_msg[:100]}...", file=sys.stderr)

                # If this is a daily limit, try next model
                if 'tokens per day' in error_msg.lower() or 'TPD' in error_msg:
                    print(f"  ℹ️ Daily token limit reached for {model}, trying smaller model...", file=sys.stderr)
                    continue

                # If it's a per-minute limit, wait briefly then try next model
                if 'tokens per minute' in error_msg.lower() or 'TPM' in error_msg:
                    if retry_after and retry_after < 30:
                        print(f"  ⏳ Waiting {retry_after:.0f}s for rate limit reset...", file=sys.stderr)
                        time.sleep(retry_after + 1)
                        # Retry same model after waiting
                        try:
                            response = self.client.chat.completions.create(
                                model=model,
                                messages=messages,
                                temperature=temperature,
                                max_tokens=max_tokens
                            )
                            return response.choices[0].message.content
                        except:
                            pass
                    continue

                # Unknown rate limit type, try next model
                continue

            except Exception as e:
                # Non-rate-limit error, don't try fallbacks
                raise

        # All models failed
        print(f"  ❌ All Groq models rate limited. Please wait or upgrade your plan.", file=sys.stderr)
        raise RateLimitError(
            f"All Groq models are rate limited. Last error: {last_error}",
            model=self.model
        )
    
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
                               count: int = 5, focus_area: str = None,
                               tone: str = None) -> List[str]:
        """
        Generate high-level conceptual insights from transcript.

        Args:
            transcript: The content transcript
            video_title: Title of the content
            count: Number of takeaways to generate
            focus_area: Optional focus area (General, Technical, Business, Learning, Quick Overview)
            tone: Optional tone (Professional, Casual, Academic, Bullet Points)

        Returns:
            List of insight strings
        """
        # Limit transcript to avoid token limits
        max_chars = 12000  # Roughly 3000 tokens
        if len(transcript) > max_chars:
            transcript = transcript[:max_chars]

        # =====================================================================
        # Build focus-specific and tone-specific instructions for takeaways
        # =====================================================================

        # Define focus-specific framing
        focus_framing = {
            "General": "Extract the most important conceptual insights.",
            "Technical": "Focus on technical insights: how things work, implementation details, tools, architectures, and technical tradeoffs.",
            "Business": "Focus on business insights: ROI implications, competitive advantages, market opportunities, and strategic value.",
            "Learning": "Focus on educational insights: key concepts to remember, learning progressions, and actionable skills.",
            "Quick Overview": "Focus only on the 3 most essential, high-impact points. Be extremely concise.",
        }

        # Define tone-specific style
        tone_style = {
            "Professional": "Use clear, professional language.",
            "Casual": "Use friendly, conversational language as if explaining to a colleague.",
            "Academic": "Use formal, precise academic language with appropriate hedging.",
            "Bullet Points": "Be ultra-concise. Short punchy sentences only.",
        }

        # Adjust count for Quick Overview
        actual_count = 3 if focus_area == "Quick Overview" else count

        # Get specific instructions
        focus_inst = focus_framing.get(focus_area, focus_framing["General"])
        tone_inst = tone_style.get(tone, tone_style["Professional"])

        # Determine length guideline based on tone
        if tone == "Bullet Points":
            length_guide = "Be ultra-concise (15-20 words max per insight)"
        elif tone == "Casual" or focus_area == "Quick Overview":
            length_guide = "Keep it brief (20-30 words per insight)"
        else:
            length_guide = "Use 30-40 words per insight"

        prompt = f"""You are a world-class analyst extracting insights from content.

FOCUS: {focus_inst}
STYLE: {tone_inst}

Title: {video_title}
Content: {transcript}

Generate exactly {actual_count} insights.

EMOJI REQUIREMENT - Start EACH insight with ONE relevant emoji:
🎯 Core concept | 💡 Revelation | ⚠️ Warning/tradeoff | 🔄 Process
📈 Growth | 🧠 Mental model | 💰 Value/ROI | 🔑 Key enabler | ✨ Opportunity

REQUIREMENTS:
1. Start with ONE emoji
2. Reveal WHY something works, not just WHAT
3. Be non-obvious and memorable
4. {length_guide}

AVOID: Generic truisms, obvious statements, vague platitudes.

Return ONLY {actual_count} insights, one per line. Format: EMOJI + space + insight."""

        try:
            if self.provider == "groq":
                # Use fallback-aware method for Groq
                content = self._groq_api_call_with_fallback(
                    messages=[
                        {"role": "system", "content": "You are a world-class analyst who reveals profound insights and non-obvious patterns."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.6,
                    max_tokens=800
                )

            elif self.provider in ["openai", "deepseek"]:
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
            import re
            raw_lines = [line.strip() for line in content.strip().split('\n') if line.strip()]

            # Clean up and format while preserving emojis
            cleaned_takeaways = []
            # Emoji pattern to detect if line starts with emoji
            emoji_pattern = r'^[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]'

            for line in raw_lines:
                # Remove leading numbers, bullets, asterisks but PRESERVE emojis
                # First check if line starts with emoji
                starts_with_emoji = re.match(emoji_pattern, line)

                if starts_with_emoji:
                    # Line already starts with emoji, just clean up any numbering after emoji
                    # e.g., "🎯 1. insight" -> "🎯 insight"
                    takeaway = re.sub(r'^([\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]+)\s*\d*[\.\)]*\s*', r'\1 ', line)
                else:
                    # No emoji, clean up numbering
                    takeaway = line.lstrip('0123456789.-•* \t')
                    takeaway = re.sub(r'^\d+[\.\)]\s*', '', takeaway)

                takeaway = takeaway.strip()
                if takeaway and len(takeaway) > 10:  # Skip empty or too-short lines
                    cleaned_takeaways.append(takeaway)
                if len(cleaned_takeaways) >= count:
                    break

            return cleaned_takeaways[:count]
            
        except Exception as e:
            print(f"Error generating takeaways: {e}", file=sys.stderr)
            return []
    
    def generate_executive_summary(self, transcript: str, video_title: str,
                                  word_count: int = 200, focus_area: str = None,
                                  tone: str = None) -> str:
        """
        Generate a coherent executive summary of the video.

        Args:
            transcript: The content transcript
            video_title: Title of the content
            word_count: Target word count for summary
            focus_area: Optional focus area (General, Technical, Business, Learning, Quick Overview)
            tone: Optional tone (Professional, Casual, Academic, Bullet Points)

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

        # =====================================================================
        # PROMPT SELECTION LOGIC
        # Each Focus Area + Tone combination should produce distinct output
        # =====================================================================

        # Quick Overview FOCUS - ultra concise (works with any tone)
        if focus_area == "Quick Overview":
            target_words = min(word_count, 150)
            if tone == "Bullet Points":
                prompt = f"""Title: {video_title}
Content: {transcript}

Create an ULTRA-BRIEF bullet summary (max {target_words} words):

## TL;DR
• [One sentence - the core message]

## 3 Key Points
• [Most important point]
• [Second most important]
• [Third most important]

Rules: Maximum {target_words} words total. No elaboration."""

            elif tone == "Casual":
                prompt = f"""Title: {video_title}
Content: {transcript}

Give me the quick version like you're texting a friend (max {target_words} words):

Basically, this is about [topic]. The main thing you need to know is [key insight].
Bottom line: [why it matters].

Keep it super casual and under {target_words} words. No fluff."""

            elif tone == "Academic":
                prompt = f"""Title: {video_title}
Content: {transcript}

Provide a concise abstract (max {target_words} words):

This work examines [topic]. The principal finding suggests [key insight].
These observations indicate [implication].

Formal language, {target_words} words maximum."""

            else:  # Professional
                prompt = f"""Title: {video_title}
Content: {transcript}

Create an executive brief in 3-4 sentences (max {target_words} words):
- Sentence 1: Core topic
- Sentence 2: Key insight
- Sentence 3: Value/implication
- Sentence 4 (optional): Target audience

Maximum {target_words} words. No elaboration."""

        # Technical FOCUS - emphasize how things work
        elif focus_area == "Technical":
            if tone == "Bullet Points":
                prompt = f"""Title: {video_title}
Content: {transcript}

Create a TECHNICAL bullet-point summary (~{word_count} words):

## Technical Overview
• [Core technology/methodology]

## Implementation Details
• [Technical detail 1 - specific tools, methods, or approaches]
• [Technical detail 2]
• [Technical detail 3]
• [Technical detail 4]

## Architecture/Process
• [How components interact]
• [Key technical decisions]

## Technical Considerations
• [Limitations or tradeoffs]
• [Performance considerations]
• [Prerequisites or dependencies]

Focus on HOW things work, not just WHAT. Be specific about tools, methods, and implementation."""

            elif tone == "Casual":
                words_per_section = word_count // 3
                prompt = f"""Title: {video_title}
Content: {transcript}

Explain the technical stuff like you're helping a colleague (~{word_count} words):

**Here's how it works** (~{words_per_section} words):
Walk them through the core technical concepts in plain language.

**The nitty-gritty** (~{words_per_section} words):
Specific tools, methods, and implementation details - but keep it approachable.

**Watch out for** (~{words_per_section} words):
Practical technical considerations, gotchas, and tips.

Make it technical but friendly - like pair programming with a friend."""

            elif tone == "Academic":
                words_per_section = word_count // 4
                prompt = f"""Title: {video_title}
Content: {transcript}

Compose a technical analysis (~{word_count} words):

**Methodology** (~{words_per_section} words): Describe the technical approach and frameworks employed.

**Implementation** (~{words_per_section} words): Detail the specific technologies, architectures, and processes.

**Technical Evaluation** (~{words_per_section} words): Analyze performance characteristics, scalability, and limitations.

**Technical Implications** (~{words_per_section} words): Discuss broader technical significance and future considerations.

Use precise technical terminology. Reference specific tools and methodologies."""

            else:  # Professional
                words_per_section = word_count // 4
                prompt = f"""Title: {video_title}
Content: {transcript}

Create a technical executive summary (~{word_count} words):

**Technical Context** (~{words_per_section} words): What technology/methodology is being discussed and why it matters.

**Core Technical Concepts** (~{words_per_section} words): The key technical details, tools, and approaches.

**Implementation Considerations** (~{words_per_section} words): How to apply this technically, including requirements and tradeoffs.

**Technical Recommendation** (~{words_per_section} words): Who should implement this and what they need to know.

Focus on technical specifics. Include tool names, methods, and implementation details."""

        # Business FOCUS - emphasize ROI and strategic value
        elif focus_area == "Business":
            if tone == "Bullet Points":
                prompt = f"""Title: {video_title}
Content: {transcript}

Create a BUSINESS-FOCUSED bullet summary (~{word_count} words):

## Executive Summary
• [One-line business value proposition]

## Business Impact
• [Revenue/cost implication]
• [Competitive advantage]
• [Market opportunity]

## Strategic Considerations
• [Key business decision point]
• [Resource requirements]
• [Risk factors]

## ROI Indicators
• [Measurable benefit 1]
• [Measurable benefit 2]

## Recommended Action
• [What business leaders should do]

Focus on business value, ROI, and strategic implications."""

            elif tone == "Casual":
                words_per_section = word_count // 3
                prompt = f"""Title: {video_title}
Content: {transcript}

Break down the business angle like you're chatting with a colleague (~{word_count} words):

**Why should we care?** (~{words_per_section} words):
The business opportunity in plain terms - money, growth, competitive edge.

**What's it gonna take?** (~{words_per_section} words):
Resources, investment, and realistic expectations.

**Bottom line** (~{words_per_section} words):
Should we do this? Who wins? What's the play?

Keep it business-savvy but conversational."""

            elif tone == "Academic":
                words_per_section = word_count // 4
                prompt = f"""Title: {video_title}
Content: {transcript}

Compose a business analysis (~{word_count} words):

**Market Context** (~{words_per_section} words): Situate within broader market dynamics and competitive landscape.

**Value Proposition Analysis** (~{words_per_section} words): Examine the economic rationale and strategic positioning.

**Implementation Economics** (~{words_per_section} words): Assess resource allocation, investment requirements, and projected returns.

**Strategic Implications** (~{words_per_section} words): Discuss long-term business trajectory and competitive implications.

Use business/economics terminology. Reference frameworks like ROI, TCO, competitive advantage."""

            else:  # Professional
                words_per_section = word_count // 4
                prompt = f"""Title: {video_title}
Content: {transcript}

Create a business executive summary (~{word_count} words):

**Business Opportunity** (~{words_per_section} words): What's the business value and why does it matter now?

**Strategic Value** (~{words_per_section} words): Competitive advantages, market positioning, and growth potential.

**Investment & Returns** (~{words_per_section} words): Resource requirements, timeline, and expected ROI.

**Executive Recommendation** (~{words_per_section} words): Clear recommendation with success metrics.

Focus on business outcomes, not technical details. Quantify where possible."""

        # Learning FOCUS - emphasize educational value
        elif focus_area == "Learning":
            if tone == "Bullet Points":
                prompt = f"""Title: {video_title}
Content: {transcript}

Create a LEARNING-FOCUSED bullet summary (~{word_count} words):

## What You'll Learn
• [Core concept 1]
• [Core concept 2]
• [Core concept 3]

## Key Concepts Explained
• [Concept]: [Brief explanation]
• [Concept]: [Brief explanation]
• [Concept]: [Brief explanation]

## Practice Exercises
• [How to apply concept 1]
• [How to apply concept 2]

## Prerequisites
• [What you should know first]

## Next Steps
• [What to learn next]
• [Resources for deeper learning]

Focus on teachable concepts and actionable learning."""

            elif tone == "Casual":
                words_per_section = word_count // 3
                prompt = f"""Title: {video_title}
Content: {transcript}

Break this down like a study buddy (~{word_count} words):

**Here's what you're gonna learn** (~{words_per_section} words):
The main concepts in friendly, memorable terms.

**Let me explain it simply** (~{words_per_section} words):
Key ideas broken down with examples you'll remember.

**Now try this** (~{words_per_section} words):
How to actually practice and apply what you learned.

Make it feel like helpful study notes, not a textbook."""

            elif tone == "Academic":
                words_per_section = word_count // 4
                prompt = f"""Title: {video_title}
Content: {transcript}

Compose an educational analysis (~{word_count} words):

**Learning Objectives** (~{words_per_section} words): Identify the core competencies and knowledge domains addressed.

**Conceptual Framework** (~{words_per_section} words): Explain the theoretical foundations and key constructs.

**Pedagogical Approach** (~{words_per_section} words): Analyze the instructional methods and learning progressions.

**Assessment & Application** (~{words_per_section} words): Describe how learners can demonstrate mastery and apply knowledge.

Use educational terminology. Reference learning theories where applicable."""

            else:  # Professional
                words_per_section = word_count // 4
                prompt = f"""Title: {video_title}
Content: {transcript}

Create an educational summary (~{word_count} words):

**Learning Objectives** (~{words_per_section} words): What skills or knowledge will be gained?

**Core Concepts** (~{words_per_section} words): The key ideas explained clearly with context.

**Practical Application** (~{words_per_section} words): How to apply this learning in real situations.

**Next Steps** (~{words_per_section} words): Recommended path for continued learning.

Focus on teaching and skill-building. Make concepts stick."""

        # General FOCUS with different tones
        else:  # General focus
            if tone == "Bullet Points":
                prompt = f"""Title: {video_title}
Content: {transcript}

Create a bullet-pointed summary (~{word_count} words):

## TL;DR
• [One sentence core message]

## Key Points
• [Point 1: specific insight]
• [Point 2: specific insight]
• [Point 3: specific insight]
• [Point 4: specific insight]
• [Point 5: specific insight]

## Main Takeaways
• [Actionable takeaway 1]
• [Actionable takeaway 2]
• [Actionable takeaway 3]

## Who Should Read This
• [Target audience 1]
• [Target audience 2]

Use bullet points throughout. Keep each bullet to 1-2 sentences."""

            elif tone == "Casual":
                words_per_section = word_count // 3
                prompt = f"""Title: {video_title}
Content: {transcript}

Write a casual summary like you're telling a friend (~{word_count} words):

**What's this about?** (~{words_per_section} words):
Hook them with why this is interesting and worth knowing.

**Here's the good stuff** (~{words_per_section} words):
Share the most interesting insights in a conversational way.

**What you can do with this** (~{words_per_section} words):
Practical takeaways in friendly language.

Use "you" and "we". Contractions are fine. Keep it real."""

            elif tone == "Academic":
                words_per_section = word_count // 4
                prompt = f"""Title: {video_title}
Content: {transcript}

Compose a formal academic summary (~{word_count} words):

**Abstract** (~{words_per_section} words): Overview of thesis and significance.

**Key Findings** (~{words_per_section} words): Principal arguments and evidence.

**Analysis** (~{words_per_section} words): Critical examination of contributions.

**Implications** (~{words_per_section} words): Broader significance and future directions.

Use formal language. Employ hedging where appropriate ("suggests", "indicates")."""

            else:  # Professional (default)
                words_per_paragraph = word_count // 4
                prompt = f"""Title: {video_title}
Content: {transcript}

Create an executive summary (~{word_count} words) in four paragraphs:

1. **Introduction** (~{words_per_paragraph} words): What this covers and why it matters.

2. **Core Themes** (~{words_per_paragraph} words): The 3-4 main concepts or arguments.

3. **Practical Applications** (~{words_per_paragraph} words): Real-world applications and implications.

4. **Recommendation** (~{words_per_paragraph} words): Who benefits and what they'll gain.

Professional language. Focus on value, not play-by-play."""

        try:
            if self.provider == "groq":
                # Use fallback-aware method for Groq
                content = self._groq_api_call_with_fallback(
                    messages=[
                        {"role": "system", "content": "You are an expert technical writer."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=word_count * 2
                )
                return content.strip()

            elif self.provider in ["openai", "deepseek"]:
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

        except RateLimitError as e:
            print(f"Rate limit error generating summary: {e}", file=sys.stderr)
            return ""
        except Exception as e:
            print(f"Error generating summary: {e}", file=sys.stderr)
            return ""

    def generate_highlights(self, transcript: str, video_title: str,
                           content_type: str = "video",
                           timestamp_data: List[Dict] = None,
                           count: int = 7) -> List[str]:
        """
        Generate key highlights with timestamps (video/podcast) or quotes (article).

        Args:
            transcript: The full transcript text
            video_title: Title of the content
            content_type: One of "video", "podcast", "article"
            timestamp_data: List of dicts with 'text', 'start' (seconds) for timed content
            count: Number of highlights to generate (default 7)

        Returns:
            List of highlight strings with timestamps or quotes
        """
        import re

        # Limit transcript
        max_chars = 15000
        if len(transcript) > max_chars:
            transcript = transcript[:max_chars]

        # Build timestamp context if available
        timestamp_context = ""
        if timestamp_data and content_type in ["video", "podcast"]:
            # Create a reference of timestamps for the AI
            timestamp_refs = []
            for item in timestamp_data[:100]:  # Limit to first 100 segments
                start_sec = item.get('start', 0)
                mins = int(start_sec // 60)
                secs = int(start_sec % 60)
                timestamp_refs.append(f"[{mins}:{secs:02d}] {item.get('text', '')[:50]}")
            timestamp_context = "\n".join(timestamp_refs[:50])

        if content_type in ["video", "podcast"]:
            prompt = f"""You are an expert content curator identifying the most impactful moments from this {content_type}.

Title: {video_title}
Content: {transcript}

{"Timestamp References (use these exact timestamps when possible):" + chr(10) + timestamp_context if timestamp_context else ""}

Identify exactly {count} HIGHLIGHTS - the most memorable, quotable, or significant moments.

REQUIREMENTS:
1. Each highlight should be a key moment, powerful quote, or critical insight
2. Format each as: [MM:SS] "Quote or description of moment"
3. Mix of ACTUAL QUOTES (in quotation marks) and moment descriptions
4. Spread highlights across the content (beginning, middle, end)
5. Prioritize moments that are surprising, actionable, or emotionally resonant

EXAMPLE FORMAT:
[2:15] "The biggest mistake people make is thinking they need permission to start"
[8:42] Key framework introduction: the 3-step process for decision making
[15:30] "If you're not embarrassed by the first version, you launched too late"
[23:18] Practical demonstration of the technique in action
[31:05] Summary of the core principles with real-world applications

Return ONLY {count} highlights, one per line. Use [MM:SS] format for timestamps."""

        else:  # article
            prompt = f"""You are an expert content curator identifying the most impactful passages from this article.

Title: {video_title}
Content: {transcript}

Identify exactly {count} HIGHLIGHTS - the most memorable quotes and key passages.

REQUIREMENTS:
1. Each highlight should be a powerful quote or critical insight
2. Mix of ACTUAL QUOTES (verbatim from text, in quotation marks) and paraphrased key points
3. For quotes: Use exact words from the article
4. For key points: Summarize in a compelling way
5. Spread highlights across the article
6. Prioritize passages that are surprising, actionable, or thought-provoking

EXAMPLE FORMAT:
> "Success is not final, failure is not fatal: it is the courage to continue that counts."
> Key insight: The author argues that consistency beats intensity in every measurable outcome
> "The difference between ordinary and extraordinary is that little extra"
> Framework: Three pillars of sustainable growth - patience, persistence, and adaptability

Return ONLY {count} highlights, one per line. Use > prefix for each."""

        try:
            if self.provider == "groq":
                # Use fallback-aware method for Groq
                content = self._groq_api_call_with_fallback(
                    messages=[
                        {"role": "system", "content": "You are an expert at identifying the most impactful moments and quotes from content."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    max_tokens=800
                )

            elif self.provider in ["openai", "deepseek"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at identifying the most impactful moments and quotes from content."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    max_tokens=800
                )
                content = response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.5
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

            # Parse highlights
            raw_lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
            highlights = []

            for line in raw_lines:
                # Clean up numbering but preserve [timestamps] and > quotes
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                cleaned = cleaned.strip()

                if cleaned and len(cleaned) > 5:
                    # Ensure proper formatting
                    if content_type in ["video", "podcast"]:
                        # Should start with [timestamp] or add placeholder
                        if not cleaned.startswith('['):
                            cleaned = "[--:--] " + cleaned
                    else:
                        # Should start with > for articles
                        if not cleaned.startswith('>'):
                            cleaned = "> " + cleaned

                    highlights.append(cleaned)

                if len(highlights) >= count:
                    break

            return highlights[:count]

        except Exception as e:
            print(f"Error generating highlights: {e}", file=sys.stderr)
            return []

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
            if self.provider == "groq":
                # Use fallback-aware method for Groq
                content = self._groq_api_call_with_fallback(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=200
                )

            elif self.provider in ["openai", "deepseek"]:
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

        except RateLimitError as e:
            print(f"Rate limit error generating next steps: {e}", file=sys.stderr)
            return []
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
