#!/usr/bin/env python3
"""
Enhanced YouTube Transcript Extractor with Multiple Fallback Methods
Handles rate limiting with intelligent retry and multiple extraction approaches
"""

import argparse
import sys
import time
import random
import re
from typing import Optional, Dict, List, Tuple
import requests

# Method 1: youtube-transcript-api
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    YOUTUBE_TRANSCRIPT_API_AVAILABLE = False

# Method 2: yt-dlp
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

# For summarization
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class RateLimitHandler:
    """Handles rate limiting with exponential backoff and jitter"""
    
    def __init__(self, max_retries=5, base_delay=60):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.attempt = 0
    
    def calculate_delay(self) -> int:
        """Calculate delay with exponential backoff and jitter"""
        if self.attempt == 0:
            return 0
        
        # Exponential backoff: base_delay * 2^(attempt-1)
        delay = self.base_delay * (2 ** (self.attempt - 1))
        # Add jitter: +/- 20%
        jitter = delay * 0.2 * (random.random() * 2 - 1)
        return int(delay + jitter)
    
    def should_retry(self) -> bool:
        """Check if we should retry"""
        return self.attempt < self.max_retries
    
    def wait(self):
        """Wait with countdown display"""
        delay = self.calculate_delay()
        if delay > 0:
            print(f"\n⏳ Waiting {delay} seconds before retry (attempt {self.attempt + 1}/{self.max_retries})...")
            for remaining in range(delay, 0, -1):
                print(f"\r   {remaining} seconds remaining...", end='', flush=True)
                time.sleep(1)
            print("\r" + " " * 50 + "\r", end='', flush=True)
        self.attempt += 1


class TranscriptExtractor:
    """Multi-method transcript extraction with fallbacks"""
    
    def __init__(self, video_url: str, max_retries: int = 5):
        self.video_url = video_url
        self.video_id = self._extract_video_id(video_url)
        self.max_retries = max_retries
        
        if not self.video_id:
            raise ValueError(f"Could not extract video ID from URL: {video_url}")
    
    @staticmethod
    def _extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def check_availability(self) -> Dict[str, bool]:
        """Check which extraction methods are available"""
        return {
            'youtube-transcript-api': YOUTUBE_TRANSCRIPT_API_AVAILABLE,
            'yt-dlp': YTDLP_AVAILABLE,
            'nltk': NLTK_AVAILABLE
        }
    
    def extract_method_1_youtube_api(self) -> Optional[str]:
        """Method 1: youtube-transcript-api with retry logic"""
        if not YOUTUBE_TRANSCRIPT_API_AVAILABLE:
            print("⚠️  Method 1 (youtube-transcript-api): Not available")
            return None
        
        print("🔍 Method 1: Trying youtube-transcript-api...")
        rate_limiter = RateLimitHandler(self.max_retries)
        
        while rate_limiter.should_retry():
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(self.video_id)
                transcript = ' '.join([entry['text'] for entry in transcript_list])
                print("✅ Method 1: Success!")
                return self._clean_transcript(transcript)
            
            except Exception as e:
                error_str = str(e).lower()
                
                if '429' in error_str or 'too many requests' in error_str:
                    print(f"⚠️  Rate limited (429). Attempt {rate_limiter.attempt + 1}/{self.max_retries}")
                    if rate_limiter.should_retry():
                        rate_limiter.wait()
                        continue
                    else:
                        print("❌ Method 1: Max retries exceeded")
                        return None
                
                elif 'could not retrieve' in error_str or 'transcript' in error_str:
                    print(f"❌ Method 1: Transcript not available - {e}")
                    return None
                
                else:
                    print(f"❌ Method 1: Error - {e}")
                    return None
        
        return None
    
    def extract_method_2_ytdlp(self) -> Optional[str]:
        """Method 2: yt-dlp with subtitle extraction"""
        if not YTDLP_AVAILABLE:
            print("⚠️  Method 2 (yt-dlp): Not available")
            return None
        
        print("🔍 Method 2: Trying yt-dlp...")
        rate_limiter = RateLimitHandler(self.max_retries, base_delay=90)
        
        while rate_limiter.should_retry():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': ['en'],
                    'skip_download': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={self.video_id}", download=False)
                    
                    # Try to get subtitles
                    subtitles = info.get('subtitles', {})
                    automatic_captions = info.get('automatic_captions', {})
                    
                    # Prefer manual subtitles over automatic
                    subs = subtitles.get('en') or automatic_captions.get('en')
                    
                    if subs:
                        # Get the subtitle URL
                        for sub in subs:
                            if sub.get('ext') in ['json3', 'srv3', 'srv2', 'srv1']:
                                sub_url = sub.get('url')
                                if sub_url:
                                    response = requests.get(sub_url)
                                    if response.status_code == 200:
                                        # Parse subtitle data
                                        transcript = self._parse_subtitle_data(response.text)
                                        if transcript:
                                            print("✅ Method 2: Success!")
                                            return self._clean_transcript(transcript)
                
                print("❌ Method 2: No subtitles found")
                return None
            
            except Exception as e:
                error_str = str(e).lower()
                
                if '429' in error_str or 'too many requests' in error_str:
                    print(f"⚠️  Rate limited (429). Attempt {rate_limiter.attempt + 1}/{self.max_retries}")
                    if rate_limiter.should_retry():
                        rate_limiter.wait()
                        continue
                    else:
                        print("❌ Method 2: Max retries exceeded")
                        return None
                else:
                    print(f"❌ Method 2: Error - {e}")
                    return None
        
        return None
    
    def _parse_subtitle_data(self, data: str) -> Optional[str]:
        """Parse subtitle data from various formats"""
        try:
            import json
            parsed = json.loads(data)
            
            if 'events' in parsed:
                texts = []
                for event in parsed['events']:
                    if 'segs' in event:
                        for seg in event['segs']:
                            if 'utf8' in seg:
                                texts.append(seg['utf8'])
                return ' '.join(texts)
        except:
            pass
        
        # Fallback: extract text with regex
        text_matches = re.findall(r'"text":"([^"]+)"', data)
        if text_matches:
            return ' '.join(text_matches)
        
        return None
    
    def _clean_transcript(self, transcript: str) -> str:
        """Clean and normalize transcript text"""
        # Remove multiple spaces
        transcript = re.sub(r'\s+', ' ', transcript)
        # Remove timestamp patterns
        transcript = re.sub(r'\[\d+:\d+:\d+\]|\(\d+:\d+\)', '', transcript)
        # Fix common caption artifacts
        transcript = re.sub(r'\[Music\]|\[Applause\]|\[Laughter\]', '', transcript, flags=re.IGNORECASE)
        return transcript.strip()
    
    def extract(self) -> Optional[str]:
        """Try all extraction methods in sequence"""
        print(f"\n📹 Extracting transcript for video: {self.video_id}")
        print(f"🔗 URL: {self.video_url}\n")
        
        # Check availability
        availability = self.check_availability()
        print("Available methods:")
        for method, available in availability.items():
            status = "✅" if available else "❌"
            print(f"  {status} {method}")
        print()
        
        # Try Method 1: youtube-transcript-api
        transcript = self.extract_method_1_youtube_api()
        if transcript:
            return transcript
        
        # Try Method 2: yt-dlp
        transcript = self.extract_method_2_ytdlp()
        if transcript:
            return transcript
        
        print("\n❌ All extraction methods failed")
        return None


class TranscriptSummarizer:
    """Summarize transcript using extractive methods"""
    
    def __init__(self):
        if NLTK_AVAILABLE:
            self._ensure_nltk_data()
    
    @staticmethod
    def _ensure_nltk_data():
        """Ensure required NLTK data is downloaded"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
    
    def summarize(self, text: str, target_words: int = 100) -> str:
        """Summarize text to approximately target_words"""
        if not NLTK_AVAILABLE:
            return self._simple_summarize(text, target_words)
        
        try:
            sentences = sent_tokenize(text)
            
            if len(sentences) <= 3:
                return text
            
            # Score sentences by word frequency
            stop_words = set(stopwords.words('english'))
            word_freq = {}
            
            for sentence in sentences:
                words = word_tokenize(sentence.lower())
                for word in words:
                    if word.isalnum() and word not in stop_words:
                        word_freq[word] = word_freq.get(word, 0) + 1
            
            # Score sentences
            sentence_scores = {}
            for sentence in sentences:
                words = word_tokenize(sentence.lower())
                score = sum(word_freq.get(word, 0) for word in words if word.isalnum())
                sentence_scores[sentence] = score / max(len(words), 1)
            
            # Select top sentences
            sorted_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
            
            summary_sentences = []
            word_count = 0
            
            for sentence, _ in sorted_sentences:
                sentence_words = len(sentence.split())
                if word_count + sentence_words <= target_words * 1.2:
                    summary_sentences.append(sentence)
                    word_count += sentence_words
                
                if word_count >= target_words:
                    break
            
            # Maintain original order
            summary_sentences.sort(key=lambda s: sentences.index(s))
            
            return ' '.join(summary_sentences)
        
        except Exception as e:
            print(f"⚠️  NLTK summarization failed: {e}")
            return self._simple_summarize(text, target_words)
    
    def _simple_summarize(self, text: str, target_words: int) -> str:
        """Simple word-count based summarization"""
        sentences = text.split('. ')
        
        if len(sentences) <= 3:
            return text
        
        # Take first and last sentences, then fill with middle content
        result = [sentences[0]]
        word_count = len(sentences[0].split())
        
        # Add middle sentences
        for sent in sentences[1:-1]:
            sent_words = len(sent.split())
            if word_count + sent_words <= target_words * 0.8:
                result.append(sent)
                word_count += sent_words
            else:
                break
        
        # Add last sentence if there's room
        if len(sentences) > 1:
            last_sent_words = len(sentences[-1].split())
            if word_count + last_sent_words <= target_words * 1.2:
                result.append(sentences[-1])
        
        return '. '.join(result)


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced YouTube Transcript Extractor with Multi-Method Fallback',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://youtu.be/VIDEO_ID
  %(prog)s https://youtu.be/VIDEO_ID --summarize 150
  %(prog)s VIDEO_ID --summarize 100 --output transcript.txt
  %(prog)s https://youtu.be/VIDEO_ID --retries 10
        """
    )
    
    parser.add_argument('video_url', help='YouTube video URL or video ID')
    parser.add_argument('--summarize', '-s', type=int, metavar='WORDS',
                        help='Summarize to approximately WORDS words')
    parser.add_argument('--output', '-o', metavar='FILE',
                        help='Save output to FILE')
    parser.add_argument('--retries', '-r', type=int, default=5,
                        help='Maximum retry attempts (default: 5)')
    
    args = parser.parse_args()
    
    # Extract transcript
    extractor = TranscriptExtractor(args.video_url, max_retries=args.retries)
    transcript = extractor.extract()
    
    if not transcript:
        print("\n❌ Failed to extract transcript. Possible reasons:")
        print("  • Rate limiting (wait 24+ hours or use different IP/VPN)")
        print("  • Video has no transcript/subtitles available")
        print("  • Video is private or age-restricted")
        print("  • Geographic restrictions")
        sys.exit(1)
    
    word_count = len(transcript.split())
    print(f"\n✅ Transcript extracted successfully!")
    print(f"📊 Word count: {word_count}")
    
    # Summarize if requested
    output_text = transcript
    if args.summarize:
        print(f"\n📝 Summarizing to ~{args.summarize} words...")
        summarizer = TranscriptSummarizer()
        output_text = summarizer.summarize(transcript, args.summarize)
        summary_words = len(output_text.split())
        print(f"✅ Summary created: {summary_words} words ({summary_words/word_count*100:.1f}% of original)")
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"\n💾 Saved to: {args.output}")
    else:
        print(f"\n{'='*80}")
        print(output_text)
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
