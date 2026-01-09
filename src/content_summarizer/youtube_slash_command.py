#!/usr/bin/env python3
"""
YouTube slash command handler.
Handles /youtube command with URL or search query.
Now also supports article URLs for content summarization.
"""
import sys
import json
import subprocess
import re
import argparse
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from enum import Enum
import concurrent.futures
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Try to import AI summarizer (optional)
try:
    from content_summarizer.ai_summarizer import AITranscriptSummarizer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Note: AI summarization not available. Install with: pip install -r requirements.txt", file=sys.stderr)

# Try to import article parsing libraries (optional)
try:
    from bs4 import BeautifulSoup
    import requests
    ARTICLE_SUPPORT = True
except ImportError:
    ARTICLE_SUPPORT = False

# Try to import Listen Notes integration (optional)
try:
    from content_summarizer.listen_notes_client import ListenNotesClient
    from content_summarizer.transcript_metrics import TranscriptMetrics
    LISTEN_NOTES_AVAILABLE = True
except ImportError:
    LISTEN_NOTES_AVAILABLE = False


class ContentType(Enum):
    """Type of content to process"""
    VIDEO = "video"
    ARTICLE = "article"
    PODCAST = "podcast"
    PODCAST_SEARCH = "podcast_search"
    TWITTER_VIDEO = "twitter_video"
    DIRECT_AUDIO = "direct_audio"  # Direct .mp3, .m4a, .wav, .ogg URLs
    X_ARTICLE = "x_article"  # X/Twitter long-form articles and text posts
    WEB_SEARCH = "web_search"  # Jina-powered web search and summarize


class NLTKHelper:
    """Centralized NLTK data management"""
    _initialized = False
    
    @classmethod
    def ensure_data(cls):
        """Ensure required NLTK data is downloaded (call once)"""
        if cls._initialized:
            return
        
        import nltk
        
        resources = {
            'tokenizers/punkt': 'punkt',
            'tokenizers/punkt_tab': 'punkt_tab',
            'corpora/stopwords': 'stopwords'
        }
        
        for path, package in resources.items():
            try:
                nltk.data.find(path)
            except LookupError:
                nltk.download(package, quiet=True)
        
        cls._initialized = True


def slugify(text, max_length=100):
    """Convert text to safe filename slug"""
    # Remove special characters, keep alphanumeric and spaces
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    # Replace spaces and multiple hyphens with single hyphen
    slug = re.sub(r'[-\s]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    return slug or 'untitled'


def extract_video_id(url_or_id):
    """Extract YouTube video ID from URL or return as-is if already an ID"""
    if "youtube.com/watch?v=" in url_or_id:
        parsed = urlparse(url_or_id)
        return parse_qs(parsed.query)["v"][0]
    elif "youtu.be/" in url_or_id:
        return url_or_id.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/live/" in url_or_id:
        # Handle YouTube Live URLs: youtube.com/live/VIDEO_ID
        live_part = url_or_id.split("youtube.com/live/")[1]
        return live_part.split("?")[0].split("/")[0]
    elif re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        # Already a video ID
        return url_or_id
    else:
        raise ValueError(f"Invalid YouTube URL or video ID format: {url_or_id}")


def is_direct_audio_url(url):
    """Check if URL is a direct audio file link."""
    url_lower = url.lower()
    # Direct audio file extensions
    audio_extensions = ('.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac')

    # Check file extension (handling query strings)
    parsed_path = urlparse(url).path.lower()
    if any(parsed_path.endswith(ext) for ext in audio_extensions):
        return True

    # Common podcast CDN patterns that serve audio
    audio_cdn_patterns = [
        'traffic.megaphone.fm',
        'dts.podtrac.com',
        'pdst.fm',
        'anchor.fm',
        'buzzsprout.com',
        'transistor.fm',
        'simplecast.com',
        'podbean.com',
        'spreaker.com',
        'libsyn.com',
        'soundcloud.com/tracks',
        'chtbl.com',  # Chartable redirect
        'prfx.byspotify.com',
    ]

    if any(cdn in url_lower for cdn in audio_cdn_patterns):
        return True

    return False


def is_x_article_url(url):
    """
    Check if URL is an X/Twitter article or long-form text post (not a video).

    X Articles are typically:
    - Posts with the /status/ pattern that contain substantial text
    - The new "Articles" feature on X

    We distinguish from TWITTER_VIDEO by checking for video indicators.
    For now, we route all X status URLs through this path and let the
    content fetcher determine if it's worth summarizing.

    Args:
        url: URL to check

    Returns:
        bool: True if this appears to be an X article/text post
    """
    url_lower = url.lower()

    # Must be X/Twitter domain
    if not ("twitter.com" in url_lower or "x.com" in url_lower):
        return False

    # Must have /status/ pattern (regular posts)
    # Note: /i/broadcasts/ are live streams, handled by TWITTER_VIDEO
    if "/status/" in url_lower:
        return True

    return False


def fetch_x_article_content(url, max_retries=2):
    """
    Fetch article content from X/Twitter using Jina Reader with fallback chain.

    Fallback chain:
    1. Jina Reader (r.jina.ai) - handles JS rendering, returns clean markdown
    2. Direct scraping with cloudscraper - may work for some X pages
    3. Raise error with guidance to use Text tab

    Args:
        url: X/Twitter URL to fetch
        max_retries: Max retries per method (default 2)

    Returns:
        tuple: (title, cleaned_text)

    Raises:
        ValueError: If content cannot be extracted
        ConnectionError: If all methods fail
    """
    import time
    import os

    errors = []

    # ==========================================================================
    # Method 1: Jina Reader (Primary - best for JS-heavy sites like X)
    # ==========================================================================
    print("  📖 Fetching X article via Jina Reader...")

    jina_api_key = os.environ.get('JINA_API_KEY', '')
    jina_url = f"https://r.jina.ai/{url}"

    for attempt in range(max_retries):
        try:
            headers = {
                'Accept': 'text/plain',
                'User-Agent': 'ContentSummarizer/1.0'
            }

            # Add API key if available (higher rate limits)
            if jina_api_key:
                headers['Authorization'] = f'Bearer {jina_api_key}'

            response = requests.get(jina_url, headers=headers, timeout=30)

            if response.status_code == 200:
                content = response.text.strip()

                # Jina returns markdown - extract title and content
                lines = content.split('\n')
                title = "X Post"
                text_lines = []

                for line in lines:
                    # Jina often returns title as first # heading
                    if line.startswith('# ') and title == "X Post":
                        title = line[2:].strip()
                    elif line.startswith('Title: ') and title == "X Post":
                        title = line[7:].strip()
                    else:
                        text_lines.append(line)

                full_text = '\n'.join(text_lines).strip()

                # Validate we got meaningful content
                if len(full_text) >= 100:
                    print(f"  ✓ Jina Reader success ({len(full_text)} chars)")
                    return (title, full_text)
                else:
                    errors.append(f"Jina returned too little content ({len(full_text)} chars)")

            elif response.status_code == 429:
                # Rate limited - wait and retry or move to fallback
                errors.append(f"Jina rate limited (429)")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1
                    print(f"  ⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            else:
                errors.append(f"Jina returned status {response.status_code}")

        except requests.exceptions.Timeout:
            errors.append("Jina request timed out")
        except Exception as e:
            errors.append(f"Jina error: {str(e)[:100]}")

        # Wait before retry
        if attempt < max_retries - 1:
            time.sleep(1)

    # ==========================================================================
    # Method 2: Direct scraping with cloudscraper (Fallback)
    # ==========================================================================
    print("  🔄 Jina failed, trying direct scraping...")

    try:
        # Try the existing fetch_article_content which uses cloudscraper
        title, content = fetch_article_content(url, max_retries=2)

        if len(content) >= 100:
            print(f"  ✓ Direct scraping success ({len(content)} chars)")
            return (title, content)
        else:
            errors.append(f"Direct scraping returned too little content ({len(content)} chars)")

    except Exception as e:
        errors.append(f"Direct scraping failed: {str(e)[:100]}")

    # ==========================================================================
    # Method 3: All methods failed - provide helpful error
    # ==========================================================================
    error_summary = "; ".join(errors[:3])  # First 3 errors

    raise ConnectionError(
        f"⚠️ Could not fetch X article content.\n\n"
        f"Attempted methods:\n"
        f"  1. Jina Reader (r.jina.ai)\n"
        f"  2. Direct scraping\n\n"
        f"Errors: {error_summary}\n\n"
        f"💡 Workarounds:\n"
        f"   1. Copy the post text and use the 'Text' tab to paste it\n"
        f"   2. If the post has a video, it may work better in the YouTube tab\n"
        f"   3. Try again later (X rate limits may be temporary)"
    )


def jina_fetch_url(url, timeout=30):
    """
    Fetch URL content using Jina Reader API.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        tuple: (title, content) or (None, None) if failed
    """
    import os

    jina_api_key = os.environ.get('JINA_API_KEY', '')
    jina_url = f"https://r.jina.ai/{url}"

    try:
        headers = {
            'Accept': 'text/plain',
            'User-Agent': 'ContentSummarizer/1.0'
        }

        if jina_api_key:
            headers['Authorization'] = f'Bearer {jina_api_key}'

        response = requests.get(jina_url, headers=headers, timeout=timeout)

        if response.status_code == 200:
            content = response.text.strip()

            # Parse title and content from Jina's markdown response
            lines = content.split('\n')
            title = None
            text_lines = []

            for line in lines:
                if line.startswith('# ') and title is None:
                    title = line[2:].strip()
                elif line.startswith('Title: ') and title is None:
                    title = line[7:].strip()
                else:
                    text_lines.append(line)

            full_text = '\n'.join(text_lines).strip()

            if len(full_text) >= 100:
                return (title or "Untitled", full_text)

        return (None, None)

    except Exception as e:
        print(f"  ⚠️ Jina fetch error: {str(e)[:100]}", file=sys.stderr)
        return (None, None)


def jina_search(query, num_results=5, timeout=60):
    """
    Search the web using Jina Search API and return content from top results.

    Args:
        query: Search query string
        num_results: Number of results to fetch (3, 5, or 10)
        timeout: Request timeout in seconds

    Returns:
        tuple: (combined_title, combined_content, sources_list) or raises exception
    """
    import os
    import urllib.parse

    jina_api_key = os.environ.get('JINA_API_KEY', '')
    encoded_query = urllib.parse.quote(query)
    jina_url = f"https://s.jina.ai/{encoded_query}"

    print(f"  🔍 Searching web for: {query}")

    try:
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'ContentSummarizer/1.0',
            'X-Retain-Images': 'none',
        }

        if jina_api_key:
            headers['Authorization'] = f'Bearer {jina_api_key}'

        response = requests.get(jina_url, headers=headers, timeout=timeout)

        if response.status_code == 200:
            # Jina search returns JSON with results
            try:
                data = response.json()
                results = data.get('data', [])[:num_results]
            except:
                # Fallback: parse as text if not JSON
                # s.jina.ai can return markdown format too
                content = response.text.strip()
                return (f"Search: {query}", content, [])

            if not results:
                raise ValueError(f"No search results found for: {query}")

            sources = []
            combined_parts = []

            for i, result in enumerate(results, 1):
                title = result.get('title', f'Result {i}')
                url = result.get('url', '')
                content = result.get('content', result.get('description', ''))

                sources.append({'title': title, 'url': url})

                # Add section for this result
                combined_parts.append(f"## Source {i}: {title}\n")
                if url:
                    combined_parts.append(f"URL: {url}\n")
                combined_parts.append(f"\n{content}\n")
                combined_parts.append("\n---\n")

            combined_content = '\n'.join(combined_parts)
            combined_title = f"Web Search: {query}"

            print(f"  ✓ Found {len(results)} results")
            return (combined_title, combined_content, sources)

        elif response.status_code == 429:
            raise ConnectionError("Jina API rate limited. Please try again later.")
        else:
            raise ConnectionError(f"Jina search failed with status {response.status_code}")

    except requests.exceptions.Timeout:
        raise ConnectionError("Search request timed out. Try a simpler query.")
    except Exception as e:
        if "rate limit" in str(e).lower():
            raise ConnectionError("Jina API rate limited. Please try again later.")
        raise


def jina_extract_pdf(file_path, timeout=60):
    """
    Extract text from PDF using Jina Reader API.

    Args:
        file_path: Path to PDF file
        timeout: Request timeout in seconds

    Returns:
        tuple: (title, content) or (None, None) if failed
    """
    import os

    jina_api_key = os.environ.get('JINA_API_KEY', '')

    try:
        # Jina supports PDF upload via POST
        jina_url = "https://r.jina.ai/"

        headers = {
            'User-Agent': 'ContentSummarizer/1.0'
        }

        if jina_api_key:
            headers['Authorization'] = f'Bearer {jina_api_key}'

        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(jina_url, headers=headers, files=files, timeout=timeout)

        if response.status_code == 200:
            content = response.text.strip()

            # Extract title from filename or content
            title = os.path.basename(file_path).rsplit('.', 1)[0]

            # Try to find title in content
            lines = content.split('\n')
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break

            if len(content) >= 100:
                print(f"  ✓ Jina PDF extraction success ({len(content)} chars)")
                return (title, content)

        return (None, None)

    except Exception as e:
        print(f"  ⚠️ Jina PDF extraction error: {str(e)[:100]}", file=sys.stderr)
        return (None, None)


def detect_content_type(query):
    """
    Detect whether query is a YouTube video, article, podcast URL, Twitter video,
    X article, direct audio file, web search, or podcast search.

    Returns:
        tuple: (ContentType, identifier) where identifier is video_id, article_url,
               podcast_url, twitter_url, x_article_url, audio_url, search_query, or web_search_data
    """
    # Check for web search queries (from UI)
    if query.startswith('WEBSEARCH:'):
        # Format: WEBSEARCH:{num_results}:{query}
        return (ContentType.WEB_SEARCH, query)

    # Check for Twitter/X patterns
    if "twitter.com" in query or "x.com" in query:
        # Live broadcasts are video content
        if "/i/broadcasts/" in query:
            return (ContentType.TWITTER_VIDEO, query)
        # Regular posts (status) are treated as articles - use Jina Reader
        # This handles tweets, threads, and X Articles feature
        if "/status/" in query:
            return (ContentType.X_ARTICLE, query)

    # Check for YouTube patterns (including live streams)
    if "youtube.com/watch" in query or "youtu.be/" in query or "youtube.com/live/" in query:
        try:
            video_id = extract_video_id(query)
            return (ContentType.VIDEO, video_id)
        except:
            pass

    # Check if it's an 11-char video ID
    if re.match(r'^[a-zA-Z0-9_-]{11}$', query):
        return (ContentType.VIDEO, query)

    # NEW: Check for DIRECT AUDIO URLs first (before podcast URL check)
    if query.startswith(('http://', 'https://')) and is_direct_audio_url(query):
        return (ContentType.DIRECT_AUDIO, query)

    # Check for PODCAST URL patterns
    # Apple Podcasts - both show and episode URLs
    if "podcasts.apple.com" in query:
        return (ContentType.PODCAST, query)

    # Spotify - episode URLs and show URLs
    if "spotify.com" in query and ("/episode/" in query or "/show/" in query):
        return (ContentType.PODCAST, query)

    # Neuecast.app - new podcast player
    if "neuecast.app" in query:
        return (ContentType.PODCAST, query)

    # RSS feed pattern
    if query.startswith('http') and (query.endswith('.rss') or query.endswith('.xml') or
                                      '/rss' in query.lower() or '/feed' in query.lower() or
                                      'feeds.' in query.lower()):
        return (ContentType.PODCAST, query)

    # Check if it's a valid http/https URL (article)
    if query.startswith(('http://', 'https://')):
        return (ContentType.ARTICLE, query)

    # Check if it's a podcast search query (not a URL)
    # Patterns: "Podcast Name - topic", "Podcast Name: topic", "Podcast Name latest"
    podcast_search_indicators = [' - ', ': ', ' latest', ' episode ', ' about ', ' on ', ' discussing']

    if any(indicator in query.lower() for indicator in podcast_search_indicators):
        # Likely a podcast search query
        return (ContentType.PODCAST_SEARCH, query)

    # Default to video (for search queries)
    return (ContentType.VIDEO, query)


def fetch_article_content(url, max_retries=3):
    """
    Fetch and parse article content from URL.

    Uses Jina Reader as primary method, falls back to cloudscraper/BeautifulSoup.

    Args:
        url: Article URL to fetch
        max_retries: Maximum number of retry attempts (default 3)

    Returns:
        tuple: (title, cleaned_text)

    Raises:
        ValueError: If content is too short or cannot be extracted
        ConnectionError: If URL cannot be reached
    """
    import time

    # ==========================================================================
    # Method 1: Jina Reader (Primary - handles JS-heavy sites)
    # ==========================================================================
    print(f"  📖 Fetching article via Jina Reader...")

    jina_title, jina_content = jina_fetch_url(url, timeout=30)

    if jina_content and len(jina_content) >= 200:
        print(f"  ✓ Jina Reader success ({len(jina_content)} chars)")
        return (jina_title or "Article", jina_content)

    print(f"  ⚠️ Jina Reader returned insufficient content, trying fallback...")

    # ==========================================================================
    # Method 2: Cloudscraper + BeautifulSoup (Fallback)
    # ==========================================================================
    if not ARTICLE_SUPPORT:
        raise ImportError(
            "Article support not available. Install dependencies: "
            "pip install beautifulsoup4 lxml"
        )

    response = None
    use_cloudscraper = False
    last_error = None

    # Try cloudscraper first (best for Cloudflare-protected sites)
    try:
        import cloudscraper
        use_cloudscraper = True
    except ImportError:
        pass

    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            if use_cloudscraper:
                scraper = cloudscraper.create_scraper()
                response = scraper.get(url, timeout=20, allow_redirects=True)
                response.raise_for_status()
            else:
                # Fallback to regular requests with enhanced headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                }

                response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
                response.raise_for_status()

            # Success - break out of retry loop
            break

        except Exception as e:
            last_error = e
            status_code = getattr(response, 'status_code', None) if response else None

            # Don't retry on permanent errors (404, etc.)
            if status_code in [404, 410]:
                break

            # Retry on temporary errors (403, 429, 500, 502, 503)
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + 0.5  # 1.5s, 2.5s, 4.5s
                time.sleep(wait_time)
                response = None  # Reset for next attempt
                continue

    # If we exhausted retries, handle the last error
    if last_error and (response is None or response.status_code >= 400):
        e = last_error
        # Handle various exception types
        error_name = type(e).__name__

        # Check for timeout
        if 'timeout' in error_name.lower() or 'timeout' in str(e).lower():
            raise ConnectionError(f"Request timed out: {url}")

        # Check for connection errors
        if 'connection' in error_name.lower():
            raise ConnectionError(f"Cannot reach URL: {url}")

        # Check for HTTP errors (including from cloudscraper)
        status_code = getattr(response, 'status_code', None) if response else None

        if 'httperror' in error_name.lower() or (response and status_code):
            if status_code == 403:
                raise ConnectionError(
                    f"⚠️ Access denied (403 Forbidden): {url}\n\n"
                    "This site has bot protection that blocks automated scrapers.\n\n"
                    "💡 Workarounds:\n"
                    "   1. Copy the article text and use the 'Paste Text' tab instead\n"
                    "   2. Try a reader mode URL if the site offers one\n"
                    "   3. Use a browser extension to extract clean article text"
                )
            if status_code:
                raise ConnectionError(f"Failed to fetch (status {status_code}): {url}")

        # Cloudscraper-specific errors
        if 'challenge' in error_name.lower() or 'cloudflare' in str(e).lower():
            raise ConnectionError(
                f"⚠️ Cloudflare challenge failed: {url}\n\n"
                "This site uses advanced bot protection.\n\n"
                "💡 Try copying the article text and using the 'Paste Text' tab instead."
            )

        # Generic error
        raise ConnectionError(f"Error fetching URL ({error_name}): {e}")

    # Parse HTML
    try:
        soup = BeautifulSoup(response.content, 'lxml')
    except:
        # Fallback to html.parser if lxml not available
        soup = BeautifulSoup(response.content, 'html.parser')

    # Extract title
    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.h1:
        title = soup.h1.get_text().strip()

    if not title:
        # Use domain as fallback
        parsed = urlparse(url)
        title = parsed.netloc.replace('www.', '')

    # Try multiple content selectors (sites use different structures) - FIND FIRST
    content_root = None
    for selector in ['article', '.entry-content', '.post-content', '.article-content', 'main', '.content']:
        if selector.startswith('.'):
            element = soup.select_one(selector)
        else:
            element = soup.find(selector)

        if element:
            content_root = element
            break

    # Fallback to body if nothing found
    if not content_root:
        content_root = soup.body if soup.body else soup

    # Now remove unwanted elements from within the content
    for element in content_root.find_all(['script', 'style', 'noscript', 'nav', 'footer', 'aside', 'header', 'iframe', 'form']):
        element.decompose()

    # Extract text from meaningful elements
    text_parts = []
    for element in content_root.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote']):
        text = element.get_text(separator=' ', strip=True)
        if text and len(text) > 20:  # Skip very short fragments
            text_parts.append(text)

    # Join with paragraph separators
    full_text = '\n\n'.join(text_parts)

    # Normalize whitespace (preserve paragraph breaks)
    full_text = re.sub(r'[^\S\n]+', ' ', full_text)  # Collapse spaces but NOT newlines
    full_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', full_text)  # Max 2 newlines
    full_text = full_text.strip()

    # Validate minimum content length
    if len(full_text) < 200:
        # Check if it's a known difficult site
        domain = urlparse(url).netloc.lower()
        difficult_sites = ['cnn.com', 'nytimes.com', 'wsj.com', 'washingtonpost.com', 'ft.com']

        error_msg = f"Article content too short ({len(full_text)} chars, minimum 200). "

        if any(site in domain for site in difficult_sites):
            error_msg += (
                f"\n\n⚠️  {domain} has strong bot protection that blocks automated scrapers.\n"
                "\n💡 Workarounds:"
                "\n   1. Copy the article text and use the 'Paste Text' tab instead"
                "\n   2. Try a reader mode URL (some sites offer simplified versions)"
                "\n   3. Use browser extensions that can extract clean article text"
            )
        else:
            error_msg += "URL may not contain readable article content."

        raise ValueError(error_msg)

    print(f"  ✓ Fallback scraping success ({len(full_text)} chars)")
    return (title, full_text)


def is_rss_feed(url):
    """Check if URL is already an RSS feed"""
    return (
        url.endswith('.rss') or 
        url.endswith('.xml') or
        '/rss' in url.lower() or
        '/feed' in url.lower() or
        'feeds.' in url.lower()
    )


def extract_rss_from_apple_podcasts(apple_url):
    """
    Extract RSS feed URL from Apple Podcasts page.
    Works by scraping HTML - no API key needed.
    
    Args:
        apple_url: Apple Podcasts URL
        
    Returns:
        str: RSS feed URL
        
    Raises:
        ValueError: If RSS feed cannot be found
    """
    if not ARTICLE_SUPPORT:
        raise ImportError("BeautifulSoup required for Apple Podcasts support")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(apple_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Apple includes RSS feed in HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for RSS link in meta tags
        rss_link = soup.find('link', {'type': 'application/rss+xml'})
        if rss_link and rss_link.get('href'):
            return rss_link['href']
        
        # Pattern 2: In HTML content (backup)
        rss_match = re.search(r'(https?://[^"\'<>\s]+\.rss[^"\'<>\s]*)', response.text)
        if rss_match:
            return rss_match.group(1)
        
        # Pattern 3: Common podcast RSS patterns
        rss_match = re.search(r'(https?://feeds\.[^"\'<>\s]+)', response.text)
        if rss_match:
            return rss_match.group(1)
        
        raise ValueError("Could not extract RSS feed from Apple Podcasts URL")
        
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to fetch Apple Podcasts page: {e}")


def extract_rss_from_spotify_free(spotify_url):
    """
    Try to extract RSS feed from Spotify using free web services.
    No API key required, but may not work for all podcasts.
    
    Args:
        spotify_url: Spotify podcast URL
        
    Returns:
        str: RSS feed URL
        
    Raises:
        ValueError: If RSS feed cannot be found
    """
    # Extract show/episode ID from Spotify URL
    spotify_id = None
    
    if "/show/" in spotify_url:
        spotify_id = spotify_url.split("/show/")[1].split("?")[0]
    elif "/episode/" in spotify_url:
        # For episode URLs, try to get show ID
        episode_id = spotify_url.split("/episode/")[1].split("?")[0]
        # Try to fetch episode page to get show ID
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(spotify_url, headers=headers, timeout=10)
            show_match = re.search(r'/show/([a-zA-Z0-9]+)', response.text)
            if show_match:
                spotify_id = show_match.group(1)
        except:
            pass
    
    if not spotify_id:
        raise ValueError("Could not extract Spotify show ID from URL")
    
    # Try free RSS conversion service
    service_url = f"https://spotifeed.timdorr.com/{spotify_id}"
    
    try:
        response = requests.head(service_url, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return service_url
    except:
        pass
    
    raise ValueError(
        "Could not access RSS feed for this Spotify podcast. "
        "This podcast may require Spotify API credentials or may be exclusive content."
    )


def parse_vtt_transcript(vtt_content):
    """Parse WebVTT format transcript (same as YouTube captions)"""
    lines = vtt_content.split('\n')
    transcript = []
    
    for line in lines:
        line = line.strip()
        # Skip VTT headers, timestamps, numbers, empty lines
        if (line and 
            not line.startswith('WEBVTT') and 
            not line.startswith('NOTE') and
            not '-->' in line and
            not line.isdigit()):
            # Remove VTT tags
            line = re.sub(r'<[^>]+>', '', line)
            transcript.append(line)
    
    return ' '.join(transcript)


def parse_srt_transcript(srt_content):
    """Parse SRT format transcript"""
    lines = srt_content.split('\n')
    transcript = []
    
    for line in lines:
        line = line.strip()
        # Skip numbers, timestamps, empty lines
        if (line and 
            not line.isdigit() and
            not '-->' in line):
            transcript.append(line)
    
    return ' '.join(transcript)


def parse_html_transcript(html_content):
    """Parse HTML transcript"""
    if not ARTICLE_SUPPORT:
        return html_content  # Return as-is if BeautifulSoup not available
    
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove scripts and styles
    for element in soup.find_all(['script', 'style']):
        element.decompose()
    return soup.get_text(separator=' ', strip=True)


def parse_json_transcript(json_content):
    """Parse JSON transcript format"""
    import json
    data = json.loads(json_content)
    
    # Common JSON formats
    if isinstance(data, list):
        # Array of segments
        texts = [item.get('text', '') for item in data if 'text' in item]
        return ' '.join(texts)
    elif 'segments' in data:
        texts = [seg.get('text', '') for seg in data['segments']]
        return ' '.join(texts)
    elif 'text' in data:
        return data['text']
    
    return str(data)


def auto_parse_transcript(content):
    """Try to auto-detect and parse transcript format"""
    # Try VTT first
    if 'WEBVTT' in content[:100]:
        return parse_vtt_transcript(content)
    # Try SRT
    elif '-->' in content[:500]:
        return parse_srt_transcript(content)
    # Try JSON
    elif content.strip().startswith('{') or content.strip().startswith('['):
        try:
            return parse_json_transcript(content)
        except:
            pass
    # Assume HTML/text
    return parse_html_transcript(content)


def extract_episode_title_from_url(podcast_url):
    """
    Extract episode title from podcast URL slug.
    Works for Apple Podcasts URLs.

    Args:
        podcast_url: Podcast URL

    Returns:
        Extracted title string or None
    """
    try:
        # For Apple Podcasts: title is in path before /id
        if 'podcasts.apple.com' in podcast_url:
            # Example: /podcast/essentials-how-to-exercise.../id1545953110?i=...
            match = re.search(r'/podcast/([^/]+)/id\d+', podcast_url)
            if match:
                slug = match.group(1)
                # Convert slug to readable title
                # Replace hyphens with spaces and capitalize
                title = slug.replace('-', ' ').title()
                return title

        # Could add Spotify and other platforms here

        return None
    except Exception as e:
        return None


class EpisodeNotFoundError(Exception):
    """Raised when a specific episode cannot be found."""
    pass


class PodcastScrapingError(Exception):
    """Raised when webpage scraping fails."""
    pass


def scrape_episode_metadata_from_webpage(podcast_url):
    """
    Scrape episode title and podcast name from podcast platform webpages.
    Supports Apple Podcasts, Spotify, and Neuecast.

    Phase 1: Webpage scraping for episode titles.

    Args:
        podcast_url: URL to Apple Podcasts, Spotify, or Neuecast episode page

    Returns:
        dict: {
            'podcast_name': str,
            'episode_title': str,
            'platform': str,  # 'apple', 'spotify', 'neuecast'
            'episode_id': str or None,
            'show_id': str or None
        }

    Raises:
        PodcastScrapingError: If scraping fails
    """
    if not ARTICLE_SUPPORT:
        raise PodcastScrapingError("BeautifulSoup required for webpage scraping")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                     'AppleWebKit/537.36 (KHTML, like Gecko) '
                     'Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        response = requests.get(podcast_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # ===== APPLE PODCASTS =====
        if 'podcasts.apple.com' in podcast_url:
            result = {'platform': 'apple', 'episode_id': None, 'show_id': None}

            # Extract IDs from URL
            id_match = re.search(r'/id(\d+)', podcast_url)
            if id_match:
                result['show_id'] = id_match.group(1)

            episode_match = re.search(r'\?i=(\d+)', podcast_url)
            if episode_match:
                result['episode_id'] = episode_match.group(1)

            # Try to get episode title from page
            # Method 1: Look for specific episode title element
            episode_elem = soup.find('span', class_='episode-details__title') or \
                          soup.find('h1', class_='headings__title') or \
                          soup.find('meta', property='og:title')

            if episode_elem:
                if episode_elem.name == 'meta':
                    result['episode_title'] = episode_elem.get('content', '').strip()
                else:
                    result['episode_title'] = episode_elem.get_text(strip=True)

            # Method 2: Use og:title meta tag (usually "Episode Name - Podcast Name")
            if not result.get('episode_title'):
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    title_text = og_title.get('content', '')
                    # Apple format: "Episode Title - Podcast Name"
                    if ' - ' in title_text:
                        parts = title_text.rsplit(' - ', 1)
                        result['episode_title'] = parts[0].strip()
                        result['podcast_name'] = parts[1].strip()

            # Get podcast name if not already found
            if not result.get('podcast_name'):
                # Try various selectors
                podcast_elem = soup.find('a', class_='link-action') or \
                              soup.find('span', class_='podcast-header__identity') or \
                              soup.find('h2', class_='product-header__identity')
                if podcast_elem:
                    result['podcast_name'] = podcast_elem.get_text(strip=True)

            # Fallback: try title tag
            if not result.get('episode_title') and soup.title:
                title_text = soup.title.string or ''
                # Remove common suffixes
                for suffix in [' on Apple Podcasts', ' - Apple Podcasts']:
                    if title_text.endswith(suffix):
                        title_text = title_text[:-len(suffix)]
                if ' - ' in title_text:
                    parts = title_text.rsplit(' - ', 1)
                    result['episode_title'] = parts[0].strip()
                    if not result.get('podcast_name'):
                        result['podcast_name'] = parts[1].strip()
                else:
                    result['episode_title'] = title_text.strip()

            if result.get('episode_title') or result.get('podcast_name'):
                print(f"  🍎 Scraped Apple Podcasts: {result.get('podcast_name', 'Unknown')} - {result.get('episode_title', 'Unknown')}")
                return result

            raise PodcastScrapingError("Could not extract episode info from Apple Podcasts page")

        # ===== SPOTIFY =====
        elif 'spotify.com' in podcast_url:
            result = {'platform': 'spotify', 'episode_id': None, 'show_id': None}

            # Extract IDs from URL
            episode_match = re.search(r'/episode/([a-zA-Z0-9]+)', podcast_url)
            if episode_match:
                result['episode_id'] = episode_match.group(1)

            show_match = re.search(r'/show/([a-zA-Z0-9]+)', podcast_url)
            if show_match:
                result['show_id'] = show_match.group(1)

            # Try og:title first (most reliable)
            og_title = soup.find('meta', property='og:title')
            if og_title:
                result['episode_title'] = og_title.get('content', '').strip()

            # Get podcast name from og:description or page elements
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                desc_text = og_desc.get('content', '')
                # Spotify descriptions often have "Listen to this episode from {Podcast Name}"
                podcast_match = re.search(r'from ([^.]+?)(?:\s+on Spotify|\.|$)', desc_text)
                if podcast_match:
                    result['podcast_name'] = podcast_match.group(1).strip()

            # Try to find podcast name in page structure
            if not result.get('podcast_name'):
                # Look for show link
                show_link = soup.find('a', href=re.compile(r'/show/'))
                if show_link:
                    result['podcast_name'] = show_link.get_text(strip=True)

            # Fallback: try title tag
            if not result.get('episode_title') and soup.title:
                title_text = soup.title.string or ''
                for suffix in [' | Podcast on Spotify', ' - song and lyrics by', ' - Spotify']:
                    if suffix in title_text:
                        title_text = title_text.split(suffix)[0]
                result['episode_title'] = title_text.strip()

            if result.get('episode_title') or result.get('podcast_name'):
                print(f"  🎵 Scraped Spotify: {result.get('podcast_name', 'Unknown')} - {result.get('episode_title', 'Unknown')}")
                return result

            raise PodcastScrapingError("Could not extract episode info from Spotify page")

        # ===== NEUECAST =====
        elif 'neuecast.app' in podcast_url:
            result = {'platform': 'neuecast', 'episode_id': None, 'show_id': None}

            # Extract IDs from URL
            episode_match = re.search(r'/episode/([a-zA-Z0-9_-]+)', podcast_url)
            if episode_match:
                result['episode_id'] = episode_match.group(1)

            podcast_match = re.search(r'/podcast/([a-zA-Z0-9_-]+)', podcast_url)
            if podcast_match:
                result['show_id'] = podcast_match.group(1)

            # Try og:title
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title_text = og_title.get('content', '').strip()
                # Neuecast format varies, try to parse
                if ' | ' in title_text:
                    parts = title_text.split(' | ')
                    result['episode_title'] = parts[0].strip()
                    if len(parts) > 1:
                        result['podcast_name'] = parts[1].strip()
                else:
                    result['episode_title'] = title_text

            # Try page title
            if not result.get('episode_title') and soup.title:
                title_text = soup.title.string or ''
                if ' | ' in title_text:
                    parts = title_text.split(' | ')
                    result['episode_title'] = parts[0].strip()
                    if len(parts) > 1:
                        result['podcast_name'] = parts[1].strip()
                else:
                    result['episode_title'] = title_text.strip()

            # Try h1/h2 for episode title
            if not result.get('episode_title'):
                h1 = soup.find('h1')
                if h1:
                    result['episode_title'] = h1.get_text(strip=True)

            if result.get('episode_title') or result.get('podcast_name'):
                print(f"  📻 Scraped Neuecast: {result.get('podcast_name', 'Unknown')} - {result.get('episode_title', 'Unknown')}")
                return result

            raise PodcastScrapingError("Could not extract episode info from Neuecast page")

        else:
            raise PodcastScrapingError(f"Unsupported platform for URL: {podcast_url}")

    except requests.exceptions.RequestException as e:
        raise PodcastScrapingError(f"Failed to fetch webpage: {e}")
    except Exception as e:
        if isinstance(e, PodcastScrapingError):
            raise
        raise PodcastScrapingError(f"Scraping failed: {e}")


def find_episode_by_title(feed_entries, target_title, threshold=0.6):
    """
    Find episode in feed by fuzzy title matching.
    
    Args:
        feed_entries: List of RSS feed entries
        target_title: Title to search for
        threshold: Minimum similarity score (0.0-1.0)
        
    Returns:
        Best matching entry or None
    """
    if not target_title or not feed_entries:
        return None
    
    from difflib import SequenceMatcher
    
    best_match = None
    best_score = 0
    
    target_lower = target_title.lower()
    target_words = set(target_lower.split())
    
    for entry in feed_entries:
        entry_title = entry.get('title', '').lower()
        
        # Method 1: Check if target title is substring (very confident match)
        if target_lower in entry_title or entry_title in target_lower:
            print(f"  🎯 Exact match found: {entry.get('title')}")
            return entry
        
        # Method 2: Word overlap scoring
        entry_words = set(entry_title.split())
        common_words = target_words & entry_words
        if len(common_words) > 0:
            overlap = len(common_words) / max(len(target_words), len(entry_words))
            if overlap > best_score:
                best_score = overlap
                best_match = entry
        
        # Method 3: Sequence similarity (catches typos and reordering)
        similarity = SequenceMatcher(None, target_lower, entry_title).ratio()
        if similarity > best_score:
            best_score = similarity
            best_match = entry
    
    if best_score >= threshold:
        print(f"  🎯 Matched episode: {best_match.get('title')} (confidence: {best_score:.0%})")
        return best_match
    
    return None


def fetch_transcript_from_rss(rss_url, episode_url=None):
    """
    Fetch transcript from podcast RSS feed using Podcasting 2.0 namespace.
    
    Args:
        rss_url: RSS feed URL
        episode_url: Optional specific episode URL to find
        
    Returns:
        tuple: (episode_title, transcript_text) or (episode_title, None) if no transcript
    """
    try:
        import feedparser
    except ImportError:
        raise ImportError("feedparser required for podcast support. Install with: pip install feedparser")
    
    try:
        # Parse RSS feed
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            raise ValueError("RSS feed contains no episodes")
        
        # Find target episode
        target_episode = None
        
        if episode_url:
            # Method 1: Try direct URL matching (for direct RSS links)
            for entry in feed.entries:
                if episode_url in entry.get('link', '') or episode_url in entry.get('id', ''):
                    target_episode = entry
                    print(f"  ✓ Found episode by URL match")
                    break
            
            # Method 2: Extract title from URL and fuzzy match (for Apple/Spotify)
            if not target_episode:
                url_title = extract_episode_title_from_url(episode_url)
                if url_title:
                    print(f"  🔍 Searching RSS for: {url_title}")
                    target_episode = find_episode_by_title(feed.entries, url_title)
        
        # Fallback: Use most recent episode
        if not target_episode:
            print(f"  ℹ️  Using latest episode from RSS feed")
            target_episode = feed.entries[0]
        
        episode_title = target_episode.get('title', 'Unknown Episode')
        
        # Check for Podcasting 2.0 transcript tags
        transcript_url = None
        transcript_type = None
        
        # Method 1: Direct transcript tag (most common)
        if hasattr(target_episode, 'podcast_transcript'):
            transcript_info = target_episode.podcast_transcript
            if isinstance(transcript_info, list):
                transcript_info = transcript_info[0]
            transcript_url = transcript_info.get('url') or transcript_info.get('href')
            transcript_type = transcript_info.get('type')
        
        # Method 2: Check in enclosures or links
        if not transcript_url:
            for link in target_episode.get('links', []):
                if 'transcript' in link.get('type', '').lower():
                    transcript_url = link.get('href')
                    transcript_type = link.get('type')
                    break
        
        # If no transcript found, return None
        if not transcript_url:
            return episode_title, None
        
        # Download and parse transcript
        print(f"  📥 Downloading transcript from RSS feed...")
        response = requests.get(transcript_url, timeout=15)
        response.raise_for_status()
        
        # Parse based on type
        if transcript_type and 'vtt' in transcript_type.lower():
            transcript_text = parse_vtt_transcript(response.text)
        elif transcript_type and 'srt' in transcript_type.lower():
            transcript_text = parse_srt_transcript(response.text)
        elif transcript_type and 'html' in transcript_type.lower():
            transcript_text = parse_html_transcript(response.text)
        elif transcript_type and 'json' in transcript_type.lower():
            transcript_text = parse_json_transcript(response.text)
        else:
            # Try to auto-detect format
            transcript_text = auto_parse_transcript(response.text)
        
        return episode_title, transcript_text
        
    except Exception as e:
        print(f"  ⚠️ Could not extract transcript from RSS: {e}")
        return None, None


def extract_show_notes_from_rss(rss_url, episode_url=None):
    """
    Extract show notes, description, and chapters from RSS feed.
    Phase 1 fallback method.
    
    Args:
        rss_url: RSS feed URL
        episode_url: Optional episode URL
        
    Returns:
        tuple: (title, show_notes_text, has_chapters) or (None, None, False)
    """
    try:
        import feedparser
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            return None, None, False
        
        # Find target episode
        target_episode = None
        
        if episode_url:
            # Method 1: Direct URL matching
            for entry in feed.entries:
                if episode_url in entry.get('link', '') or episode_url in entry.get('id', ''):
                    target_episode = entry
                    break
            
            # Method 2: Title-based fuzzy matching
            if not target_episode:
                url_title = extract_episode_title_from_url(episode_url)
                if url_title:
                    target_episode = find_episode_by_title(feed.entries, url_title)
        
        # Fallback: Use most recent episode
        if not target_episode:
            target_episode = feed.entries[0]
        
        title = target_episode.get('title', 'Unknown Episode')
        
        # Extract description/summary
        description = target_episode.get('description', '') or target_episode.get('summary', '')
        
        # Clean HTML if present
        if description:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(description, 'html.parser')
                description = soup.get_text(separator='\n', strip=True)
            except:
                pass
        
        # Extract Podcasting 2.0 chapters if available
        chapters_text = ""
        has_chapters = False
        
        if hasattr(target_episode, 'podcast_chapters'):
            chapters = target_episode.podcast_chapters
            if chapters:
                has_chapters = True
                chapters_text = "\n\n=== Episode Chapters ===\n"
                if isinstance(chapters, list):
                    for ch in chapters:
                        start = ch.get('startTime', 'Unknown')
                        chapter_title = ch.get('title', 'Untitled')
                        chapters_text += f"\n{start}: {chapter_title}"
                else:
                    chapters_text += str(chapters)
        
        # Combine description and chapters
        full_text = description + chapters_text
        
        if len(full_text.strip()) < 100:
            return title, None, has_chapters
        
        return title, full_text, has_chapters
        
    except Exception as e:
        print(f"  ⚠️ Could not extract show notes: {e}")
        return None, None, False


def scrape_podcast_webpage(episode_url):
    """
    Scrape podcast episode webpage for transcript.
    Phase 2 fallback method.
    
    Args:
        episode_url: Episode webpage URL
        
    Returns:
        tuple: (title, transcript_text) or (None, None)
    """
    if not ARTICLE_SUPPORT:
        return None, None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(episode_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract title
        title = None
        if soup.title:
            title = soup.title.string.strip()
        
        # Look for transcript in common locations
        transcript_text = None
        
        # Pattern 1: div/section with "transcript" class or id
        transcript_elem = (
            soup.find('div', class_=re.compile(r'transcript', re.I)) or
            soup.find('section', class_=re.compile(r'transcript', re.I)) or
            soup.find('div', id=re.compile(r'transcript', re.I))
        )
        
        if transcript_elem:
            transcript_text = transcript_elem.get_text(separator='\n', strip=True)
        
        # Pattern 2: Look for "Transcript" heading followed by content
        if not transcript_text:
            for heading in soup.find_all(['h2', 'h3', 'h4']):
                if 'transcript' in heading.get_text().lower():
                    # Get all siblings until next heading
                    content_parts = []
                    for sibling in heading.find_next_siblings():
                        if sibling.name in ['h2', 'h3', 'h4']:
                            break
                        text = sibling.get_text(separator=' ', strip=True)
                        if text:
                            content_parts.append(text)
                    if content_parts:
                        transcript_text = '\n\n'.join(content_parts)
                        break
        
        # Validate minimum length
        if transcript_text and len(transcript_text) > 500:
            return title, transcript_text
        
        return title, None
        
    except Exception as e:
        print(f"  ⚠️ Could not scrape webpage: {e}")
        return None, None


def find_youtube_mirror(podcast_title, episode_title=None):
    """
    Search for podcast episode on YouTube.
    Phase 3 fallback method.
    
    Args:
        podcast_title: Podcast show name
        episode_title: Episode title
        
    Returns:
        str: YouTube video ID or None
    """
    try:
        # Build search query
        search_query = podcast_title if podcast_title else ""
        if episode_title:
            if search_query and episode_title.lower() != podcast_title.lower():
                search_query = f"{podcast_title} {episode_title}"
            elif not search_query:
                search_query = episode_title
        
        if not search_query:
            return None
        
        # Clean up common podcast patterns
        search_query = re.sub(r'Episode \d+', '', search_query)
        search_query = re.sub(r'#\d+', '', search_query)
        search_query = search_query.strip()
        
        # Debug: Show what we're searching for
        print(f"  🔍 YouTube search: \"{search_query}\"")
        
        # Search YouTube
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            f'ytsearch1:{search_query}',
            '--print-json',
            '--skip-download'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        
        if result.returncode != 0:
            return None
        
        video_data = json.loads(result.stdout.strip())
        video_id = video_data.get('id')
        video_title = video_data.get('title', '')
        
        if not video_title:
            return None
        
        print(f"  📺 Found: {video_title}")
        
        # Validate match - CRITICAL: Check podcast name first
        video_title_lower = video_title.lower()
        
        # If we have podcast name, it MUST appear in video title
        if podcast_title:
            # Remove common words that cause false matches
            podcast_core = podcast_title.lower()
            for common in ['podcast', 'the', 'show', 'with']:
                podcast_core = podcast_core.replace(common, '')
            podcast_core = podcast_core.strip()
            
            # Podcast name must be in video title
            if podcast_core and podcast_core not in video_title_lower:
                print(f"  ⚠️ YouTube video doesn't match podcast '{podcast_title}' - skipping")
                return None
        
        # If we have episode title, check word overlap
        if episode_title:
            episode_words = set(episode_title.lower().split())
            video_words = set(video_title_lower.split())
            
            # Remove very common words that cause false matches
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                           'of', 'with', 'by', 'from', 'how', 'why', 'what', 'dr', 'essentials',
                           'episode', 'part', 'vol', 'volume'}
            episode_words = episode_words - common_words
            video_words = video_words - common_words
            
            # Need at least 50% word overlap (increased from 40%)
            if len(episode_words) > 0:
                overlap = len(episode_words & video_words) / len(episode_words)
                
                if overlap < 0.5:
                    print(f"  ⚠️ YouTube video overlap too low: {overlap:.0%} - skipping")
                    return None
        
        print(f"  ✓ YouTube match validated")
        return video_id
        
    except Exception as e:
        print(f"  ⚠️ Could not find YouTube mirror: {e}")
        return None


def get_ai_cache_dir():
    """Get or create cache directory for AI responses"""
    cache_dir = Path.home() / ".cache" / "ai_summaries"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_ai_cache_key(content_text, operation, params):
    """Generate cache key for AI responses"""
    # Use first 2000 chars of content + operation + params for cache key
    data = f"{operation}:{content_text[:2000]}:{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(data.encode()).hexdigest()


def get_cached_ai_response(content_text, operation, params):
    """Check if AI response is cached"""
    try:
        cache_key = get_ai_cache_key(content_text, operation, params)
        cache_file = get_ai_cache_dir() / f"{cache_key}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                print(f"  💾 Using cached {operation}")
                return cached.get('result')
    except Exception as e:
        print(f"  ⚠️ Cache read failed: {e}", file=sys.stderr)
    
    return None


def save_ai_response(content_text, operation, params, result):
    """Save AI response to cache"""
    try:
        cache_key = get_ai_cache_key(content_text, operation, params)
        cache_file = get_ai_cache_dir() / f"{cache_key}.json"
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({'result': result, 'operation': operation, 'params': params}, f)
    except Exception as e:
        print(f"  ⚠️ Cache write failed: {e}", file=sys.stderr)


def download_podcast_audio(audio_url, output_path):
    """
    Download podcast audio using yt-dlp or direct download.

    Args:
        audio_url: URL to audio file
        output_path: Path to save audio

    Returns:
        bool: Success
    """
    from pathlib import Path
    output_path = Path(output_path)

    # Try direct download first (faster for direct MP3 URLs)
    try:
        import requests
        response = requests.get(audio_url, stream=True, timeout=30)
        if response.status_code == 200 and 'audio' in response.headers.get('content-type', ''):
            print(f"  📥 Direct downloading audio...")
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            if output_path.exists() and output_path.stat().st_size > 1000:
                return True
    except Exception as e:
        print(f"  ⚠️ Direct download failed: {e}")

    # Fallback to yt-dlp
    try:
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            audio_url,
            '-o', str(output_path),
            '--extract-audio',
            '--audio-format', 'mp3',
            '--no-playlist'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        return result.returncode == 0 and output_path.exists()

    except Exception as e:
        print(f"  ⚠️ Audio download failed: {e}")
        return False


def search_youtube_for_podcast(podcast_name, episode_title):
    """
    Search YouTube for a podcast episode mirror.
    Many podcasts are uploaded to YouTube with transcripts.

    Args:
        podcast_name: Name of the podcast
        episode_title: Title of the episode

    Returns:
        tuple: (video_id, video_title) or (None, None) if not found
    """
    import json

    # Build search query
    search_query = f"{podcast_name} {episode_title}"
    # Limit query length
    if len(search_query) > 100:
        search_query = search_query[:100]

    print(f"  🔍 Searching YouTube for: {search_query[:50]}...")

    try:
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            f'ytsearch3:{search_query}',
            '--print-json',
            '--skip-download',
            '--no-warnings'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return None, None

        # Parse results (one JSON per line)
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                video_data = json.loads(line)
                video_title = video_data.get('title', '').lower()
                channel = video_data.get('uploader', '').lower()

                # Check if this looks like the right podcast
                podcast_lower = podcast_name.lower()
                if podcast_lower in video_title or podcast_lower in channel:
                    video_id = video_data.get('id')
                    title = video_data.get('title')
                    print(f"  ✓ Found YouTube mirror: {title[:50]}...")
                    return video_id, title
            except json.JSONDecodeError:
                continue

        print(f"  ℹ️ No YouTube mirror found")
        return None, None

    except subprocess.TimeoutExpired:
        print(f"  ⚠️ YouTube search timed out")
        return None, None
    except Exception as e:
        print(f"  ⚠️ YouTube search failed: {e}")
        return None, None


def is_ffmpeg_available():
    """Check if ffmpeg is available on the system."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def chunk_audio_for_transcription(audio_path, max_size_mb=20, output_dir=None):
    """
    Split audio file into chunks suitable for Groq Whisper API (25MB limit).
    Uses ffmpeg to split by duration.

    Args:
        audio_path: Path to audio file
        max_size_mb: Maximum size per chunk in MB (default 20 for safety margin)
        output_dir: Directory for chunks (default: same as audio file)

    Returns:
        list: List of chunk file paths, or empty list if chunking fails
    """
    from pathlib import Path
    import math

    audio_path = Path(audio_path)
    if not audio_path.exists():
        return []

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)

    # If file is small enough, no chunking needed
    if file_size_mb <= max_size_mb:
        return [audio_path]

    # Check if ffmpeg is available
    if not is_ffmpeg_available():
        print(f"  ⚠️ ffmpeg not installed - cannot chunk large audio files")
        print(f"  ℹ️ File is {file_size_mb:.1f}MB but limit is {max_size_mb}MB")
        print(f"  💡 Add 'ffmpeg' to packages.txt for Streamlit Cloud")
        return []

    if output_dir is None:
        output_dir = audio_path.parent

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  ✂️ Audio is {file_size_mb:.1f}MB, splitting into chunks...")

    # Get audio duration using ffprobe
    try:
        duration_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_path)
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=10)
        total_duration = float(duration_result.stdout.strip())
    except Exception:
        # Estimate duration from file size (assume 128kbps MP3)
        total_duration = (file_size_mb * 1024 * 8) / 128  # seconds
        print(f"  ⚠️ Could not detect duration, estimating: {total_duration/60:.1f} minutes")

    # Calculate chunk duration to stay under size limit
    # Aim for chunks that are ~20MB
    bytes_per_second = (file_size_mb * 1024 * 1024) / total_duration
    chunk_duration = int((max_size_mb * 1024 * 1024) / bytes_per_second)
    chunk_duration = min(chunk_duration, 600)  # Max 10 minutes per chunk

    num_chunks = math.ceil(total_duration / chunk_duration)
    print(f"  📦 Creating {num_chunks} chunks of ~{chunk_duration/60:.1f} minutes each")

    chunks = []
    for i in range(num_chunks):
        start_time = i * chunk_duration
        chunk_path = output_dir / f"chunk_{i:03d}.mp3"

        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', str(audio_path),
                '-ss', str(start_time),
                '-t', str(chunk_duration),
                '-acodec', 'libmp3lame',
                '-ab', '64k',  # Lower bitrate to reduce file size
                '-ar', '16000',  # 16kHz sample rate (good for speech)
                '-ac', '1',  # Mono
                str(chunk_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if chunk_path.exists() and chunk_path.stat().st_size > 1000:
                chunks.append(chunk_path)
            else:
                print(f"  ⚠️ Failed to create chunk {i}")

        except Exception as e:
            print(f"  ⚠️ Chunk {i} failed: {e}")

    print(f"  ✓ Created {len(chunks)} audio chunks")
    return chunks


def transcribe_audio_huggingface(audio_path, api_token=None):
    """
    Transcribe audio using Hugging Face Inference API (free).
    Uses the Whisper large-v3 model.

    Args:
        audio_path: Path to audio file
        api_token: Hugging Face API token (or uses HF_TOKEN env var)

    Returns:
        tuple: (transcript_text, 'huggingface') or raises exception
    """
    import os
    import requests
    from pathlib import Path

    api_token = api_token or os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')
    if not api_token:
        raise ValueError("Hugging Face API token not set. Set HF_TOKEN environment variable.")

    audio_path = Path(audio_path)
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)

    if file_size_mb > 10:
        raise ValueError(f"Audio file too large for HF API ({file_size_mb:.1f}MB > 10MB limit)")

    print(f"  🤗 Transcribing with Hugging Face API ({file_size_mb:.1f}MB)...")

    API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
    headers = {"Authorization": f"Bearer {api_token}"}

    with open(audio_path, "rb") as f:
        data = f.read()

    try:
        response = requests.post(API_URL, headers=headers, data=data, timeout=300)
        response.raise_for_status()

        result = response.json()
        if isinstance(result, dict) and 'text' in result:
            transcript = result['text'].strip()
            print(f"  ✓ HuggingFace transcription complete ({len(transcript)} chars)")
            return transcript, 'huggingface'
        else:
            raise ValueError(f"Unexpected response format: {result}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 503:
            raise ValueError("HuggingFace model is loading, try again in ~20 seconds")
        raise ValueError(f"HuggingFace API error: {e}")
    except Exception as e:
        raise ValueError(f"HuggingFace transcription failed: {e}")


def transcribe_podcast_full(audio_path, episode_title=""):
    """
    Full podcast transcription pipeline.
    Tries multiple methods in order: Groq chunking → HuggingFace fallback.

    Args:
        audio_path: Path to downloaded audio file
        episode_title: Episode title for logging

    Returns:
        tuple: (transcript_text, method_used) or raises exception
    """
    import os
    from pathlib import Path
    import tempfile

    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise ValueError(f"Audio file not found: {audio_path}")

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    print(f"  📊 Audio file: {file_size_mb:.1f}MB")

    # Method 1: Groq Whisper with chunking
    if os.getenv('GROQ_API_KEY'):
        try:
            print(f"  🎯 Attempting Groq Whisper transcription...")

            # Chunk the audio if needed
            temp_dir = Path(tempfile.mkdtemp())
            chunks = chunk_audio_for_transcription(audio_path, max_size_mb=20, output_dir=temp_dir)

            if not chunks:
                raise ValueError("Audio chunking failed")

            transcripts = []
            for i, chunk_path in enumerate(chunks):
                print(f"  🎤 Transcribing chunk {i+1}/{len(chunks)}...")
                try:
                    chunk_transcript, _ = transcribe_audio_groq(chunk_path)
                    transcripts.append(chunk_transcript)
                except Exception as e:
                    print(f"  ⚠️ Chunk {i+1} failed: {e}")
                    # Continue with other chunks

            # Cleanup chunks
            for chunk in chunks:
                try:
                    if chunk != audio_path:  # Don't delete original
                        chunk.unlink()
                except:
                    pass
            try:
                temp_dir.rmdir()
            except:
                pass

            if transcripts:
                full_transcript = " ".join(transcripts)
                print(f"  ✓ Groq transcription complete ({len(full_transcript)} chars from {len(transcripts)} chunks)")
                return full_transcript, f'groq_chunked_{len(chunks)}'

        except Exception as e:
            print(f"  ⚠️ Groq transcription failed: {e}")
            print(f"  🔄 Trying HuggingFace fallback...")

    # Method 2: HuggingFace (for smaller files or as fallback)
    hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')
    if hf_token:
        try:
            # HuggingFace has 10MB limit, need to chunk
            temp_dir = Path(tempfile.mkdtemp())
            chunks = chunk_audio_for_transcription(audio_path, max_size_mb=8, output_dir=temp_dir)

            if not chunks:
                raise ValueError("Audio chunking for HF failed")

            transcripts = []
            for i, chunk_path in enumerate(chunks):
                print(f"  🤗 HF transcribing chunk {i+1}/{len(chunks)}...")
                try:
                    chunk_transcript, _ = transcribe_audio_huggingface(chunk_path, hf_token)
                    transcripts.append(chunk_transcript)
                except Exception as e:
                    print(f"  ⚠️ HF chunk {i+1} failed: {e}")

            # Cleanup
            for chunk in chunks:
                try:
                    if chunk != audio_path:
                        chunk.unlink()
                except:
                    pass

            if transcripts:
                full_transcript = " ".join(transcripts)
                print(f"  ✓ HuggingFace transcription complete ({len(full_transcript)} chars)")
                return full_transcript, f'huggingface_chunked_{len(chunks)}'

        except Exception as e:
            print(f"  ⚠️ HuggingFace transcription failed: {e}")

    # No methods worked - provide helpful error message
    if not is_ffmpeg_available():
        raise ValueError(
            "Transcription failed: ffmpeg is required for large audio files. "
            "Add 'ffmpeg' to packages.txt for Streamlit Cloud deployment."
        )
    raise ValueError(
        "All transcription methods failed. "
        "Ensure GROQ_API_KEY is set (and optionally HF_TOKEN as backup)."
    )


def get_youtube_transcript_for_podcast(video_id):
    """
    Get transcript from YouTube video (podcast mirror).

    Args:
        video_id: YouTube video ID

    Returns:
        str: Transcript text or None
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # Try to get transcript
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Prefer manual captions over auto-generated
        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
        except:
            try:
                transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
            except:
                pass

        if transcript:
            transcript_data = transcript.fetch()
            full_text = " ".join([item['text'] for item in transcript_data])
            return full_text

        return None

    except Exception as e:
        print(f"  ⚠️ Could not get YouTube transcript: {e}")
        return None


def download_twitter_video(twitter_url):
    """
    Download video from Twitter/X URL using yt-dlp.
    
    Args:
        twitter_url: Twitter/X status URL
        
    Returns:
        tuple: (video_path, title) or (None, None) if failed
    """
    import tempfile
    from pathlib import Path
    
    try:
        temp_dir = Path(tempfile.mkdtemp())
        output_template = str(temp_dir / "twitter_video.%(ext)s")
        
        print(f"  📥 Downloading Twitter video...")
        
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            twitter_url,
            '-o', output_template,
            '--format', 'best[ext=mp4]/best',  # Prefer MP4
            '--no-playlist',
            '--quiet',
            '--no-warnings'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            # Find the downloaded file
            video_files = list(temp_dir.glob("twitter_video.*"))
            if video_files:
                video_path = video_files[0]
                print(f"  ✓ Video downloaded: {video_path.name}")
                
                # Try to get title
                title_cmd = [
                    sys.executable, '-m', 'yt_dlp',
                    twitter_url,
                    '--get-title',
                    '--no-warnings'
                ]
                title_result = subprocess.run(title_cmd, capture_output=True, text=True, timeout=10)
                title = title_result.stdout.strip() if title_result.returncode == 0 else "Twitter Video"
                
                return (str(video_path), title)
        
        print(f"  ⚠️ Download failed: {result.stderr}")
        return (None, None)
        
    except subprocess.TimeoutExpired:
        print(f"  ⚠️ Download timed out")
        return (None, None)
    except Exception as e:
        print(f"  ⚠️ Download error: {e}")
        return (None, None)


def transcribe_audio_groq(audio_path, max_file_size_mb=25):
    """
    Transcribe audio using Groq's Whisper API.
    Best for cloud deployment (Streamlit Cloud, etc.)

    Args:
        audio_path: Path to audio file
        max_file_size_mb: Maximum file size in MB (Groq limit is 25MB)

    Returns:
        tuple: (transcript_text, 'groq') or raises exception
    """
    import os
    from pathlib import Path

    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not set")

    audio_path = Path(audio_path)
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)

    if file_size_mb > max_file_size_mb:
        raise ValueError(f"Audio file too large ({file_size_mb:.1f}MB > {max_file_size_mb}MB limit)")

    print(f"  🎤 Transcribing with Groq Whisper API ({file_size_mb:.1f}MB)...")

    try:
        import openai

        client = openai.OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )

        with open(audio_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                response_format="text"
            )

        transcript = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
        print(f"  ✓ Groq transcription complete ({len(transcript)} chars)")
        return transcript, 'groq'

    except Exception as e:
        raise Exception(f"Groq Whisper API failed: {e}")


def transcribe_audio_whisper(audio_path, mode='full', max_duration_minutes=60):
    """
    Transcribe audio using Groq Whisper API (primary) or faster-whisper (fallback).
    Phase 4 fallback method.

    Args:
        audio_path: Path to audio file
        mode: 'full' or 'gist' (gist = first 10 minutes + samples)
        max_duration_minutes: Maximum duration to transcribe in full mode

    Returns:
        tuple: (transcript_text, actual_mode_used)
    """
    import os
    from pathlib import Path

    audio_path = Path(audio_path)

    # Try Groq Whisper API first (best for cloud deployment)
    if os.getenv('GROQ_API_KEY'):
        try:
            return transcribe_audio_groq(audio_path)
        except Exception as e:
            print(f"  ⚠️ Groq Whisper failed: {e}")
            print(f"  🔄 Falling back to local Whisper...")

    # Fallback to local faster-whisper
    try:
        from faster_whisper import WhisperModel

        # Initialize model (small model for speed/resource balance)
        print(f"  🤖 Loading local Whisper model...")
        model = WhisperModel("base", device="cpu", compute_type="int8")
        
        # Get audio duration
        import subprocess
        duration_cmd = [
            'ffprobe', '-v', 'error', 
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_path)
        ]
        
        try:
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=10)
            duration_seconds = float(duration_result.stdout.strip())
            duration_minutes = duration_seconds / 60
        except:
            duration_minutes = max_duration_minutes  # Assume max if can't detect
        
        # Decide on mode
        actual_mode = mode
        if mode == 'full' and duration_minutes > max_duration_minutes:
            print(f"  ⚠️ Episode is {duration_minutes:.1f} minutes (limit: {max_duration_minutes} min)")
            print(f"  🔄 Switching to Gist mode (first 10 minutes)")
            actual_mode = 'gist'
        
        # Transcribe
        if actual_mode == 'gist':
            print(f"  🎤 Transcribing (Gist mode: first 10 minutes)...")
            # Transcribe with 10-minute limit
            segments, info = model.transcribe(
                str(audio_path),
                beam_size=5,
                language='en',
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Collect segments up to 10 minutes
            transcript_parts = []
            total_duration = 0
            for segment in segments:
                if total_duration >= 600:  # 10 minutes
                    break
                transcript_parts.append(segment.text)
                total_duration = segment.end
            
            transcript = ' '.join(transcript_parts)
            
        else:
            print(f"  🎤 Transcribing (Full mode: {duration_minutes:.1f} minutes)...")
            segments, info = model.transcribe(
                str(audio_path),
                beam_size=5,
                language='en',
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            transcript_parts = [segment.text for segment in segments]
            transcript = ' '.join(transcript_parts)
        
        return transcript, actual_mode
        
    except ImportError:
        raise ImportError(
            "faster-whisper not available. Install with: pip install faster-whisper"
        )
    except Exception as e:
        raise Exception(f"Whisper transcription failed: {e}")


def try_webpage_fallback(episode_url):
    """Try webpage scraping fallback"""
    if not episode_url:
        return None
    try:
        webpage_title, webpage_transcript = scrape_podcast_webpage(episode_url)
        if webpage_transcript:
            return ('webpage', webpage_title, webpage_transcript)
    except:
        pass
    return None


def try_youtube_fallback(episode_title, podcast_name=None):
    """Try YouTube mirror fallback"""
    if not episode_title:
        return None
    try:
        youtube_id = find_youtube_mirror(podcast_name, episode_title)
        if youtube_id:
            youtube_transcript = fetch_transcript(youtube_id)
            if youtube_transcript:
                return ('youtube', episode_title, youtube_transcript)
    except:
        pass
    return None


def parse_podcast_search_query(query):
    """
    Parse podcast search query into podcast name and topic.

    Supported formats:
      - "Podcast Name - topic"
      - "Podcast Name -- topic" (double dash)
      - "Podcast Name: topic"
      - "Podcast Name episode about topic"
      - "Podcast Name latest"
      - "Podcast Name topic" (fallback)

    Returns:
        tuple: (podcast_name, topic) or (None, None)
    """
    query = query.strip()

    # Normalize multiple dashes to single dash with spaces
    # "All IN -- latest" -> "All IN - latest"
    query = re.sub(r'\s*-{2,}\s*', ' - ', query)

    # Pattern 1: "Podcast Name - topic"
    if ' - ' in query:
        parts = query.split(' - ', 1)
        return parts[0].strip(), parts[1].strip()
    
    # Pattern 2: "Podcast Name: topic"
    if ': ' in query:
        parts = query.split(': ', 1)
        return parts[0].strip(), parts[1].strip()
    
    # Pattern 3: "Podcast Name episode about topic"
    if ' episode ' in query.lower():
        parts = query.lower().split(' episode ', 1)
        podcast_name = parts[0].strip()
        topic = parts[1].replace('about ', '').strip()
        return podcast_name, topic
    
    # Pattern 4: "Podcast Name latest"
    if query.lower().endswith(' latest'):
        podcast_name = query[:-7].strip()
        return podcast_name, 'latest'
    
    # Pattern 5: Try to split by common words
    keywords = ['about', 'on', 'discussing']
    for keyword in keywords:
        if f' {keyword} ' in query.lower():
            parts = query.lower().split(f' {keyword} ', 1)
            return parts[0].strip(), parts[1].strip()
    
    # Fallback: assume last 1-2 words are topic
    words = query.split()
    if len(words) >= 3:
        # Take last 1-2 words as topic
        if len(words[-1]) > 3:  # Meaningful word
            podcast_name = ' '.join(words[:-1])
            topic = words[-1]
            return podcast_name, topic
    
    # Can't parse - return whole query as podcast name, "latest" as topic
    return query, 'latest'


def find_episode_by_keyword(episodes, keyword):
    """
    Find episode matching keyword in title or description.
    
    Args:
        episodes: List of episode dicts from Listen Notes
        keyword: Keyword to search for
        
    Returns:
        Episode dict or None
    """
    if keyword.lower() == 'latest':
        return episodes[0] if episodes else None
    
    keyword_lower = keyword.lower()
    
    # Try exact match first
    for episode in episodes:
        title = episode.get('title', '').lower()
        description = episode.get('description', '').lower()
        
        if keyword_lower in title or keyword_lower in description:
            return episode
    
    # Try word-based matching
    keyword_words = set(keyword_lower.split())
    
    best_match = None
    best_score = 0
    
    for episode in episodes:
        title = episode.get('title', '').lower()
        description = episode.get('description', '').lower()
        
        title_words = set(title.split())
        desc_words = set(description.split())
        
        # Calculate overlap
        title_overlap = len(keyword_words & title_words)
        desc_overlap = len(keyword_words & desc_words)
        
        score = title_overlap * 2 + desc_overlap  # Weight title more
        
        if score > best_score:
            best_score = score
            best_match = episode
    
    # Return if reasonable match
    if best_score >= len(keyword_words) * 0.5:  # At least 50% word overlap
        return best_match

    return None


def handle_direct_audio(audio_url):
    """
    Handle direct audio file URL (MP3, M4A, WAV, etc.).
    Downloads the audio and transcribes it directly.

    Args:
        audio_url: Direct URL to audio file

    Returns:
        tuple: (title, transcript_text, source_label)
    """
    import time
    import tempfile
    from pathlib import Path

    print(f"🎵 Processing direct audio URL...")
    print(f"  📎 URL: {audio_url[:80]}{'...' if len(audio_url) > 80 else ''}")

    # Extract title from URL path
    parsed_url = urlparse(audio_url)
    path_parts = parsed_url.path.split('/')
    filename = path_parts[-1] if path_parts else 'audio'

    # Clean up filename for title
    title = filename
    for ext in ['.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac']:
        title = title.replace(ext, '')
    title = title.replace('-', ' ').replace('_', ' ').strip()
    if not title:
        title = "Audio File"

    print(f"  📝 Title: {title}")

    # Create temp directory for download
    temp_dir = Path(tempfile.mkdtemp())

    # Determine file extension from URL
    ext = '.mp3'  # Default
    for audio_ext in ['.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac']:
        if audio_ext in audio_url.lower():
            ext = audio_ext
            break

    audio_path = temp_dir / f"direct_audio{ext}"

    try:
        # Download audio file
        print(f"  📥 Downloading audio...")
        start_time = time.time()

        if not download_podcast_audio(audio_url, audio_path):
            raise ValueError("Failed to download audio file")

        download_time = time.time() - start_time
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Downloaded {file_size_mb:.1f} MB in {download_time:.1f}s")

        # Transcribe using full pipeline (Groq → HuggingFace fallback)
        print(f"  🎤 Transcribing audio...")
        start_time = time.time()

        transcript, mode_used = transcribe_podcast_full(audio_path, title)

        if not transcript:
            raise ValueError("Transcription failed - no transcript returned")

        transcribe_time = time.time() - start_time
        print(f"  ✓ Transcription complete ({mode_used}) in {transcribe_time:.1f}s")
        print(f"  📊 Transcript: {len(transcript):,} characters")

        # Cleanup
        try:
            audio_path.unlink()
            temp_dir.rmdir()
        except:
            pass

        label = f"Direct Audio ({mode_used.replace('_', ' ').title()})"
        return title, transcript, label

    except Exception as e:
        # Cleanup on error
        try:
            if audio_path.exists():
                audio_path.unlink()
            temp_dir.rmdir()
        except:
            pass
        raise ValueError(f"Failed to process audio: {e}")


def handle_podcast_content(podcast_url):
    """
    Handle podcast URL with episode-specific search.

    Phase 3: Updated processing flow that searches for the SPECIFIC episode
    from the URL, not just the latest episode.

    Args:
        podcast_url: Podcast URL (Spotify, Apple, Neuecast, or RSS)

    Returns:
        tuple: (title, transcript_text, source_label)
    """
    import time

    print(f"🎙️  Processing podcast URL...")

    # Initialize metrics tracker
    metrics = TranscriptMetrics() if LISTEN_NOTES_AVAILABLE else None

    # Track what we know about the episode
    audio_url = None
    episode_title = None
    podcast_title = None
    scraped_metadata = None
    specific_episode_found = False

    # =================================================================
    # PHASE 1: Scrape webpage to get podcast name and episode title
    # =================================================================
    if not is_rss_feed(podcast_url):
        print("  🔍 [Phase 1] Scraping webpage for episode metadata...")
        try:
            scraped_metadata = scrape_episode_metadata_from_webpage(podcast_url)
            if scraped_metadata:
                episode_title = scraped_metadata.get('episode_title')
                podcast_title = scraped_metadata.get('podcast_name')
                print(f"  ✓ Extracted: '{episode_title}' from '{podcast_title}'")
        except PodcastScrapingError as e:
            print(f"  ⚠️ Webpage scraping failed: {e}")
        except Exception as e:
            print(f"  ⚠️ Unexpected scraping error: {e}")

    # =================================================================
    # PHASE 2: Use Listen Notes to search for the SPECIFIC episode
    # =================================================================
    if LISTEN_NOTES_AVAILABLE and episode_title and podcast_title:
        print("  🔍 [Phase 2] Searching Listen Notes for specific episode...")

        start_time = time.time()
        try:
            listen_notes_client = ListenNotesClient()
            result = listen_notes_client.search_episode_by_title(podcast_title, episode_title)
            duration = time.time() - start_time

            if result and result.get('audio_url'):
                audio_url = result['audio_url']
                episode_title = result.get('title', episode_title)
                podcast_title = result.get('podcast_title', podcast_title)
                specific_episode_found = True

                match_confidence = result.get('match_confidence', 0)
                print(f"  ✓ Found specific episode via Listen Notes! (confidence: {match_confidence:.0%})")

                if metrics:
                    metrics.record('listen_notes_episode_search', podcast_url, True, duration)

                # Show quota status
                ln_metrics = listen_notes_client.get_metrics()
                if ln_metrics.get('quota_remaining'):
                    print(f"  📊 Listen Notes quota: {ln_metrics['requests_made']} used | {ln_metrics['quota_remaining']} remaining")
            else:
                print(f"  ℹ️ Listen Notes: Could not find specific episode")
                if metrics:
                    metrics.record('listen_notes_episode_search', podcast_url, False, duration)

        except Exception as e:
            duration = time.time() - start_time
            print(f"  ⚠️ Listen Notes search error: {e}")
            if metrics:
                metrics.record('listen_notes_episode_search', podcast_url, False, duration)

    # =================================================================
    # PHASE 3: Get RSS feed URL for fallback methods
    # =================================================================
    print("  🔄 [Phase 3] Setting up RSS fallback methods...")

    rss_url = None
    episode_url = None

    if is_rss_feed(podcast_url):
        print("  ✓ Direct RSS feed detected")
        rss_url = podcast_url

    elif "podcasts.apple.com" in podcast_url:
        print("  🍎 Apple Podcasts detected")
        print("  📡 Extracting RSS feed from Apple Podcasts...")
        try:
            rss_url = extract_rss_from_apple_podcasts(podcast_url)
            print(f"  ✓ RSS feed found!")
            episode_url = podcast_url
        except Exception as e:
            if not specific_episode_found:
                raise ValueError(f"Could not extract RSS feed from Apple Podcasts: {e}")
            print(f"  ⚠️ RSS extraction failed, but we have episode from Listen Notes")

    elif "spotify.com" in podcast_url:
        print("  🎵 Spotify podcast detected")
        print("  📡 Attempting to find RSS feed (free method)...")
        try:
            rss_url = extract_rss_from_spotify_free(podcast_url)
            print(f"  ✓ RSS feed found!")
            episode_url = podcast_url
        except Exception as e:
            if not specific_episode_found:
                print(f"  ⚠️ {e}")
                raise ValueError(
                    "This Spotify podcast cannot be accessed via free methods. "
                    "You can try entering the direct RSS feed URL if you have it."
                )
            print(f"  ⚠️ RSS extraction failed, but we have episode from Listen Notes")

    elif "neuecast.app" in podcast_url:
        print("  📻 Neuecast detected")
        episode_url = podcast_url
        # Neuecast doesn't have direct RSS, rely on Listen Notes or other methods
        if not specific_episode_found:
            print("  ⚠️ Neuecast requires Listen Notes API for episode lookup")

    else:
        if not specific_episode_found:
            raise ValueError(f"Unsupported podcast URL format: {podcast_url}")

    # =================================================================
    # PHASE 4: Try RSS transcript with improved episode matching
    # =================================================================
    if rss_url:
        print("  🔍 [Phase 4] Checking RSS feed for transcript...")
        start_time = time.time()

        # Pass scraped episode title for better RSS matching
        rss_episode_title = episode_title if episode_title else None
        title, transcript = fetch_transcript_from_rss_enhanced(
            rss_url,
            episode_url=episode_url,
            target_episode_title=rss_episode_title
        )

        if transcript:
            duration = time.time() - start_time
            if specific_episode_found or rss_episode_title:
                print(f"  ✓ Transcript found for SPECIFIC episode in RSS!")
            else:
                print(f"  ⚠️ WARNING: Using latest episode (specific episode not found)")
            if metrics:
                metrics.record('rss_transcript', podcast_url, True, duration)
            return title, transcript, "Podcast Transcript (RSS)"

        print(f"  ℹ️ No transcript in RSS feed")

        # Get show notes and podcast name from RSS
        show_title, show_notes, has_chapters = extract_show_notes_from_rss(rss_url, episode_url)

        if not episode_title:
            episode_title = show_title

        # Extract podcast name from RSS if not already known
        if not podcast_title:
            try:
                import feedparser
                feed = feedparser.parse(rss_url)
                podcast_title = feed.feed.get('title', '')
                if podcast_title:
                    print(f"  📻 Podcast: {podcast_title}")
            except:
                pass

    # =================================================================
    # PHASE 5: Try webpage and YouTube fallbacks in parallel
    # =================================================================
    print("  ⚡ [Phase 5] Running parallel fallback attempts...")

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_webpage = executor.submit(try_webpage_fallback, episode_url)
        future_youtube = executor.submit(try_youtube_fallback, episode_title, podcast_title)

        for future in concurrent.futures.as_completed([future_webpage, future_youtube]):
            result = future.result()
            if result:
                duration = time.time() - start_time
                source, result_title, result_transcript = result

                if source == 'webpage':
                    print(f"  ✓ Transcript found on webpage!")
                    if metrics:
                        metrics.record('webpage', podcast_url, True, duration)
                    return result_title or episode_title, result_transcript, "Podcast Transcript (Webpage)"
                elif source == 'youtube':
                    print(f"  ✓ YouTube version found!")
                    if metrics:
                        metrics.record('youtube_mirror', podcast_url, True, duration)
                    return result_title, result_transcript, "Podcast Transcript (YouTube Mirror)"

    print("  ℹ️ No transcript found via fast methods")

    # =================================================================
    # PHASE 6: Download audio + transcribe with Whisper
    # =================================================================
    print("  🎤 [Phase 6] Audio transcription with Whisper...")

    # If we don't have audio URL from Listen Notes, get from RSS
    if not audio_url and rss_url:
        print("  📥 Getting audio URL from RSS feed...")
        import feedparser
        feed = feedparser.parse(rss_url)

        target_episode = None

        # Try to find specific episode in RSS
        if episode_title:
            target_episode = find_episode_by_title(feed.entries, episode_title, threshold=0.5)
            if target_episode:
                print(f"  ✓ Found specific episode in RSS: {target_episode.get('title', '')[:50]}...")

        # Also try URL matching
        if not target_episode and episode_url:
            for entry in feed.entries:
                if episode_url in entry.get('link', '') or episode_url in entry.get('id', ''):
                    target_episode = entry
                    print(f"  ✓ Found episode by URL match")
                    break

        # Fallback to latest with WARNING
        if not target_episode and feed.entries:
            print(f"  ⚠️ WARNING: Could not find specific episode, using LATEST episode")
            print(f"     Expected: {episode_title}")
            print(f"     Using: {feed.entries[0].get('title', 'Unknown')}")
            target_episode = feed.entries[0]

        if target_episode:
            # Update episode title from RSS
            if not episode_title:
                episode_title = target_episode.get('title', 'Unknown Episode')

            # Get audio enclosure
            for enclosure in target_episode.get('enclosures', []):
                if 'audio' in enclosure.get('type', ''):
                    audio_url = enclosure.get('href') or enclosure.get('url')
                    break

    if not audio_url:
        raise EpisodeNotFoundError(
            f"Could not find audio URL for episode: '{episode_title}'\n"
            f"Podcast: '{podcast_title}'\n"
            "This specific episode may not be available or the podcast doesn't provide direct audio access."
        )

    # Download audio
    print(f"  📥 Downloading podcast audio...")
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    audio_path = temp_dir / "podcast_audio.mp3"

    if not download_podcast_audio(audio_url, audio_path):
        raise ValueError("Audio download failed. Please check the podcast URL and try again.")

    print(f"  ✓ Audio downloaded")

    # Full transcription pipeline (Groq chunking → HuggingFace fallback)
    start_time = time.time()
    try:
        transcript, mode_used = transcribe_podcast_full(audio_path, episode_title or "Unknown")
        duration = time.time() - start_time

        if transcript:
            print(f"  ✓ Full transcription complete ({mode_used})!")

            if metrics:
                metrics.record(mode_used, podcast_url, True, duration)

            # Cleanup
            try:
                audio_path.unlink()
                temp_dir.rmdir()
            except:
                pass

            label = f"Podcast Transcript ({mode_used.replace('_', ' ').title()})"
            return episode_title or "Unknown Episode", transcript, label

    except Exception as e:
        duration = time.time() - start_time
        print(f"  ❌ Transcription failed: {e}")
        if metrics:
            metrics.record('transcription_failed', podcast_url, False, duration)

        # Cleanup on failure
        try:
            audio_path.unlink()
            temp_dir.rmdir()
        except:
            pass

    raise ValueError(
        "Transcription failed. Ensure GROQ_API_KEY is set. "
        "For backup, you can also set HF_TOKEN (Hugging Face token)."
    )


def fetch_transcript_from_rss_enhanced(rss_url, episode_url=None, target_episode_title=None):
    """
    Enhanced RSS transcript fetching with better episode matching.

    Phase 4: Improved RSS fallback matching.

    Args:
        rss_url: RSS feed URL
        episode_url: Optional specific episode URL to find
        target_episode_title: Optional episode title to search for (from webpage scraping)

    Returns:
        tuple: (episode_title, transcript_text) or (episode_title, None) if no transcript
    """
    try:
        import feedparser
    except ImportError:
        raise ImportError("feedparser required for podcast support. Install with: pip install feedparser")

    try:
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            raise ValueError("RSS feed contains no episodes")

        # Find target episode using multiple methods
        target_episode = None
        match_method = None

        # Method 1: Direct URL matching (highest confidence)
        if episode_url:
            for entry in feed.entries:
                entry_link = entry.get('link', '')
                entry_id = entry.get('id', '')
                if episode_url in entry_link or episode_url in entry_id:
                    target_episode = entry
                    match_method = "URL match"
                    print(f"  🎯 Found episode by URL match: {entry.get('title', '')[:50]}...")
                    break

        # Method 2: Title matching from scraped metadata (high confidence)
        if not target_episode and target_episode_title:
            print(f"  🔍 Searching RSS for episode: '{target_episode_title[:50]}...'")
            target_episode = find_episode_by_title(feed.entries, target_episode_title, threshold=0.5)
            if target_episode:
                match_method = "title match"

        # Method 3: Extract title from URL slug and fuzzy match
        if not target_episode and episode_url:
            url_title = extract_episode_title_from_url(episode_url)
            if url_title:
                print(f"  🔍 Searching RSS by URL slug: '{url_title}'")
                target_episode = find_episode_by_title(feed.entries, url_title, threshold=0.5)
                if target_episode:
                    match_method = "URL slug match"

        # Fallback: Use most recent episode with WARNING
        if not target_episode:
            print(f"  ⚠️ Could not find specific episode in RSS feed")
            print(f"     Using LATEST episode as fallback")
            target_episode = feed.entries[0]
            match_method = "latest fallback"
        else:
            print(f"  ✓ Episode matched via: {match_method}")

        episode_title = target_episode.get('title', 'Unknown Episode')

        # Check for Podcasting 2.0 transcript tags
        transcript_url = None
        transcript_type = None

        if hasattr(target_episode, 'podcast_transcript'):
            transcript_info = target_episode.podcast_transcript
            if isinstance(transcript_info, list):
                transcript_info = transcript_info[0]
            transcript_url = transcript_info.get('url') or transcript_info.get('href')
            transcript_type = transcript_info.get('type')

        # Check in enclosures or links
        if not transcript_url:
            for link in target_episode.get('links', []):
                if 'transcript' in link.get('type', '').lower():
                    transcript_url = link.get('href')
                    transcript_type = link.get('type')
                    break

        if not transcript_url:
            return episode_title, None

        # Download and parse transcript
        print(f"  📥 Downloading transcript from RSS feed...")
        response = requests.get(transcript_url, timeout=15)
        response.raise_for_status()

        # Parse based on type
        if transcript_type and 'vtt' in transcript_type.lower():
            transcript_text = parse_vtt_transcript(response.text)
        elif transcript_type and 'srt' in transcript_type.lower():
            transcript_text = parse_srt_transcript(response.text)
        elif transcript_type and 'html' in transcript_type.lower():
            transcript_text = parse_html_transcript(response.text)
        elif transcript_type and 'json' in transcript_type.lower():
            transcript_text = parse_json_transcript(response.text)
        else:
            transcript_text = auto_parse_transcript(response.text)

        return episode_title, transcript_text

    except Exception as e:
        print(f"  ⚠️ Could not extract transcript from RSS: {e}")
        return None, None


def handle_podcast_search(search_query):
    """
    Handle podcast search query using Listen Notes.
    
    Args:
        search_query: String like "Huberman Lab - exercise" or "The Daily elections"
        
    Returns:
        tuple: (title, transcript_text, source_label)
    """
    import time
    
    print(f"🔍 Processing podcast search query...")
    
    # Parse search query
    podcast_name, topic = parse_podcast_search_query(search_query)
    
    if not podcast_name:
        raise ValueError("Could not parse podcast search query")
    
    print(f"  📻 Podcast: {podcast_name}")
    print(f"  🎯 Topic: {topic}")
    
    # Initialize metrics
    metrics = TranscriptMetrics() if LISTEN_NOTES_AVAILABLE else None
    
    if not LISTEN_NOTES_AVAILABLE:
        raise ValueError("Listen Notes API required for podcast search. Please set LISTEN_NOTES_API_KEY.")
    
    try:
        from content_summarizer.listen_notes_client import ListenNotesClient

        client = ListenNotesClient()

        # Step 1: Search for podcast
        print(f"  🔍 Searching Listen Notes for: {podcast_name}")
        start_time = time.time()
        
        podcasts = client.search_podcast(podcast_name, limit=5)

        if not podcasts:
            raise ValueError(f"Podcast '{podcast_name}' not found on Listen Notes")

        # Show all matching podcasts for debugging
        print(f"  📋 Search results:")
        for i, p in enumerate(podcasts[:3], 1):
            print(f"     {i}. {p['title']} ({p['total_episodes']} episodes)")

        # Find best match by name similarity using fuzzy matching
        from difflib import SequenceMatcher

        def fuzzy_match_score(title, search):
            """
            Calculate fuzzy match score using multiple techniques.
            Returns score 0-100 where 100 is perfect match.
            """
            title_lower = title.lower().strip()
            search_lower = search.lower().strip()

            # Exact match
            if search_lower == title_lower:
                return 100

            # Calculate base similarity using SequenceMatcher
            base_ratio = SequenceMatcher(None, search_lower, title_lower).ratio()

            # Bonus for substring match
            substring_bonus = 0
            if search_lower in title_lower:
                substring_bonus = 25
            elif title_lower.startswith(search_lower):
                substring_bonus = 20

            # Word overlap bonus
            search_words = set(search_lower.split())
            title_words = set(title_lower.split())
            if search_words:
                word_overlap = len(search_words & title_words) / len(search_words)
                word_bonus = word_overlap * 15
            else:
                word_bonus = 0

            # Combine scores
            final_score = (base_ratio * 60) + substring_bonus + word_bonus

            return min(100, int(final_score))

        # Score and sort podcasts
        scored = [(p, fuzzy_match_score(p['title'], podcast_name)) for p in podcasts]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Show scores for debugging
        print(f"  📊 Match scores:")
        for p, score in scored[:3]:
            print(f"     • {p['title'][:40]}{'...' if len(p['title']) > 40 else ''} → {score}%")

        podcast = scored[0][0]
        match_score = scored[0][1]
        podcast_id = podcast['id']

        # Warn if match score is low
        if match_score < 50:
            print(f"  ⚠️  Low confidence match ({match_score}%) - results may not be accurate")

        print(f"  ✓ Selected: {podcast['title']} (score: {match_score}%)")
        print(f"  📊 {podcast['total_episodes']} episodes available")
        
        # Step 2: Get recent episodes
        print(f"  📥 Fetching recent episodes...")
        episodes = client.get_podcast_episodes(podcast_id, limit=20)
        
        if not episodes:
            raise ValueError("No episodes found for this podcast")
        
        print(f"  ✓ Retrieved {len(episodes)} episodes")
        
        # Step 3: Find episode matching topic
        print(f"  🎯 Searching for episodes about: {topic}")
        
        matched_episode = find_episode_by_keyword(episodes, topic)
        
        if not matched_episode:
            # Use latest episode if no match
            print(f"  ℹ️  No specific match, using latest episode")
            matched_episode = episodes[0]
        else:
            print(f"  ✓ Matched: {matched_episode['title'][:60]}...")
        
        duration = time.time() - start_time
        
        if metrics:
            metrics.record('listen_notes_api', search_query, True, duration)
        
        # Show API usage
        ln_metrics = client.get_metrics()
        if ln_metrics.get('quota_remaining'):
            print(f"  📊 Listen Notes quota: {ln_metrics['requests_made']} used | {ln_metrics['quota_remaining']} remaining")
        
        # Step 4: Get episode metadata
        audio_url = matched_episode.get('audio_url')
        episode_title = matched_episode['title']

        # Step 5: Try YouTube mirror first (free, fast, high quality)
        print(f"  📺 Checking for YouTube mirror...")
        yt_video_id, yt_title = search_youtube_for_podcast(podcast['title'], episode_title)

        if yt_video_id:
            yt_transcript = get_youtube_transcript_for_podcast(yt_video_id)
            if yt_transcript and len(yt_transcript) > 500:
                print(f"  ✓ Got transcript from YouTube!")
                if metrics:
                    metrics.record('youtube_mirror', search_query, True, time.time() - start_time)
                return episode_title, yt_transcript, "Podcast Transcript (YouTube Mirror)"

        # Step 6: Download audio and transcribe with full pipeline
        if not audio_url:
            raise ValueError("No audio URL available for this episode and no YouTube mirror found.")

        print(f"  ✓ Audio URL obtained")
        print(f"  📥 Downloading podcast audio...")

        import tempfile
        from pathlib import Path

        temp_dir = Path(tempfile.mkdtemp())
        audio_path = temp_dir / "podcast_audio.mp3"

        if not download_podcast_audio(audio_url, audio_path):
            raise ValueError("Audio download failed. Please try again later.")

        print(f"  ✓ Audio downloaded")

        # Full transcription pipeline (Groq chunking → HuggingFace)
        # NO description fallback - we want real transcripts
        start_time = time.time()
        try:
            transcript, mode_used = transcribe_podcast_full(audio_path, episode_title)
            duration = time.time() - start_time

            if transcript:
                print(f"  ✓ Full transcription complete ({mode_used})!")

                if metrics:
                    metrics.record('whisper', search_query, True, duration)

                # Cleanup
                try:
                    audio_path.unlink()
                    temp_dir.rmdir()
                except:
                    pass
                
                label = f"Podcast Transcript ({mode_used.replace('_', ' ').title()})"
                return episode_title, transcript, label

        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Transcription failed: {e}")
            if metrics:
                metrics.record('transcription_failed', search_query, False, duration)

            # Cleanup on failure
            try:
                audio_path.unlink()
                temp_dir.rmdir()
            except:
                pass

        # NO description fallback - raise error with helpful message
        raise ValueError(
            "Transcription failed. Ensure GROQ_API_KEY is set. "
            "For backup, you can also set HF_TOKEN (Hugging Face token)."
        )

    except Exception as e:
        print(f"  ❌ Error: {e}")
        raise


def is_url(text):
    """Check if text looks like a URL"""
    return text.startswith(('http://', 'https://', 'youtu.be'))


def search_youtube(query):
    """Search YouTube using yt-dlp and return video metadata"""
    try:
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            f'ytsearch1:{query}',
            '--print-json',
            '--skip-download'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"Error searching YouTube: {result.stderr}", file=sys.stderr)
            return None
        
        # Parse JSON output
        try:
            video_data = json.loads(result.stdout.strip())
            return {
                'id': video_data.get('id'),
                'title': video_data.get('title'),
                'url': video_data.get('webpage_url'),
                'uploader': video_data.get('uploader'),
                'duration': video_data.get('duration')
            }
        except json.JSONDecodeError as e:
            print(f"Error parsing search results: {e}", file=sys.stderr)
            return None
            
    except subprocess.TimeoutExpired:
        print("Error: Search timed out", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("Error: yt-dlp not found. Install with: pip install yt-dlp", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        return None


def fetch_transcript_ytdlp(video_id):
    """Fallback method: fetch transcript using yt-dlp"""
    import tempfile
    import os
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd = [
                sys.executable, '-m', 'yt_dlp',
                f'https://www.youtube.com/watch?v={video_id}',
                '--write-auto-subs',
                '--write-subs',
                '--sub-lang', 'en',
                '--skip-download',
                '--output', f'{temp_dir}/subtitle',
                '--convert-subs', 'vtt'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Look for subtitle files
            subtitle_files = []
            for ext in ['.en.vtt', '.vtt']:
                for filename in os.listdir(temp_dir):
                    if filename.endswith(ext):
                        subtitle_files.append(os.path.join(temp_dir, filename))
            
            if not subtitle_files:
                return None
            
            # Read and parse VTT file
            with open(subtitle_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract text from VTT format
            lines = content.split('\n')
            transcript_lines = []
            prev_line = None
            for line in lines:
                line = line.strip()
                # Skip VTT headers, timestamps, and empty lines
                if (line and 
                    not line.startswith('WEBVTT') and 
                    not line.startswith('Kind:') and
                    not line.startswith('Language:') and
                    not '-->' in line and
                    not line.isdigit()):
                    # Remove VTT tags like <c> </c>
                    line = re.sub(r'<[^>]+>', '', line)
                    # Skip duplicate consecutive lines (VTT format issue)
                    if line != prev_line:
                        transcript_lines.append(line)
                        prev_line = line
            
            return ' '.join(transcript_lines)
            
    except Exception as e:
        print(f"yt-dlp fallback failed: {e}", file=sys.stderr)
        return None


def fetch_transcript(video_id):
    """Fetch transcript using enhanced multi-method approach with retry"""
    max_retries = 3
    retry_count = 0
    base_delay = 30
    
    while retry_count < max_retries:
        try:
            # Method 1: youtube-transcript-api
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            full_transcript = " ".join([item['text'] for item in transcript_data])
            return full_transcript
            
        except AttributeError:
            # Try newer API method
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Try to find English transcript first
                try:
                    transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
                    transcript_data = transcript.fetch()
                except:
                    # Use first available transcript or auto-generated
                    available = list(transcript_list)
                    if not available:
                        raise NoTranscriptFound(video_id)
                    
                    transcript = available[0]
                    transcript_data = transcript.fetch()
                
                full_transcript = " ".join([item['text'] for item in transcript_data])
                return full_transcript
                
            except Exception as e:
                raise Exception(f"Alternative method failed: {e}")

        except TranscriptsDisabled:
            # Try yt-dlp fallback before giving up
            print("Transcripts marked as disabled, trying yt-dlp fallback...", file=sys.stderr)
            fallback_transcript = fetch_transcript_ytdlp(video_id)
            if fallback_transcript:
                return fallback_transcript
            raise Exception("Transcripts are disabled for this video")
        except NoTranscriptFound:
            # Try yt-dlp fallback before giving up
            print("No transcript found via API, trying yt-dlp fallback...", file=sys.stderr)
            fallback_transcript = fetch_transcript_ytdlp(video_id)
            if fallback_transcript:
                return fallback_transcript
            raise Exception("No transcript found for this video (may not have captions)")
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error
            if '429' in error_str or 'Too Many Requests' in error_str.lower():
                retry_count += 1
                if retry_count < max_retries:
                    delay = base_delay * retry_count
                    print(f"Rate limited (429), retrying in {delay}s (attempt {retry_count}/{max_retries})...", file=sys.stderr)
                    import time
                    time.sleep(delay)
                    continue
                else:
                    print("Max retries reached, trying yt-dlp fallback...", file=sys.stderr)
                    fallback_transcript = fetch_transcript_ytdlp(video_id)
                    if fallback_transcript:
                        return fallback_transcript
                    raise Exception("Rate limited: All methods exhausted. Try again later or use VPN.")

            # For other errors (like XML parsing), try yt-dlp fallback immediately
            print(f"Primary method failed ({error_str}), trying yt-dlp fallback...", file=sys.stderr)
            fallback_transcript = fetch_transcript_ytdlp(video_id)
            if fallback_transcript:
                return fallback_transcript
            raise Exception(f"Error fetching transcript: {e}")

    raise Exception("Failed to fetch transcript after multiple retries")


def fetch_transcript_with_timestamps(video_id):
    """
    Fetch transcript with timestamp data for highlights generation.

    Returns:
        tuple: (full_transcript_text, timestamp_data) where timestamp_data is a list of
               dicts with 'text', 'start' (seconds), 'duration' keys.
               Returns (transcript, None) if timestamps unavailable.
    """
    max_retries = 3
    retry_count = 0
    base_delay = 30

    while retry_count < max_retries:
        try:
            # Method 1: youtube-transcript-api
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            full_transcript = " ".join([item['text'] for item in transcript_data])
            return full_transcript, transcript_data

        except AttributeError:
            # Try newer API method
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

                # Try to find English transcript first
                try:
                    transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
                    transcript_data = transcript.fetch()
                except:
                    # Use first available transcript or auto-generated
                    available = list(transcript_list)
                    if not available:
                        raise NoTranscriptFound(video_id)

                    transcript = available[0]
                    transcript_data = transcript.fetch()

                full_transcript = " ".join([item['text'] for item in transcript_data])
                return full_transcript, transcript_data

            except Exception as e:
                raise Exception(f"Alternative method failed: {e}")

        except TranscriptsDisabled:
            # Try yt-dlp fallback before giving up
            print("Transcripts marked as disabled, trying yt-dlp fallback...", file=sys.stderr)
            fallback_transcript = fetch_transcript_ytdlp(video_id)
            if fallback_transcript:
                return fallback_transcript, None  # No timestamps from yt-dlp
            raise Exception("Transcripts are disabled for this video")
        except NoTranscriptFound:
            # Try yt-dlp fallback before giving up
            print("No transcript found via API, trying yt-dlp fallback...", file=sys.stderr)
            fallback_transcript = fetch_transcript_ytdlp(video_id)
            if fallback_transcript:
                return fallback_transcript, None  # No timestamps from yt-dlp
            raise Exception("No transcript found for this video (may not have captions)")
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error
            if '429' in error_str or 'Too Many Requests' in error_str.lower():
                retry_count += 1
                if retry_count < max_retries:
                    delay = base_delay * retry_count
                    print(f"Rate limited (429), retrying in {delay}s (attempt {retry_count}/{max_retries})...", file=sys.stderr)
                    import time
                    time.sleep(delay)
                    continue
                else:
                    print("Max retries reached, trying yt-dlp fallback...", file=sys.stderr)
                    fallback_transcript = fetch_transcript_ytdlp(video_id)
                    if fallback_transcript:
                        return fallback_transcript, None  # No timestamps from yt-dlp
                    raise Exception("Rate limited: All methods exhausted. Try again later or use VPN.")

            # For other errors, try yt-dlp fallback immediately
            print(f"Primary method failed ({error_str}), trying yt-dlp fallback...", file=sys.stderr)
            fallback_transcript = fetch_transcript_ytdlp(video_id)
            if fallback_transcript:
                return fallback_transcript, None  # No timestamps from yt-dlp
            raise Exception(f"Error fetching transcript: {e}")

    raise Exception("Failed to fetch transcript after multiple retries")


def assess_content_quality(text, content_type="video"):
    """
    Assess content quality and return warnings.
    
    Args:
        text: Content text to assess
        content_type: "video" or "article"
    
    Returns:
        list: Warning messages (empty if no issues)
    """
    warnings = []
    word_count = len(text.split())
    
    # Check for music video (mostly lyrics)
    music_count = text.count('♪') + text.count('[Music]') + text.count('(Music)')
    music_ratio = music_count / max(word_count, 1)
    if music_ratio > 0.3 or music_count > 50:
        warnings.append("⚠️ Music video detected - transcript is primarily lyrics, not spoken content")
    
    # Check for very short content
    if word_count < 100:
        warnings.append("⚠️ Very short content - may not generate meaningful insights")
    
    # Check for highly conversational content (lots of filler)
    if content_type == "video":
        filler_words = ['um', 'uh', 'like', 'you know', 'so basically']
        filler_count = sum(text.lower().count(w) for w in filler_words)
        filler_ratio = filler_count / max(word_count, 1)
        if filler_ratio > 0.15:
            warnings.append("💬 Highly conversational content - key takeaways may be limited")
    
    return warnings


def clean_transcript(transcript_text):
    """
    Clean and normalize transcript text.
    
    Removes:
        - Music notation (♪♫🎵🎶)
        - Sound effects ([Music], [Applause])
        - HTML tags and entities
        
    Fixes:
        - Punctuation spacing
        - Multiple whitespace
        
    Args:
        transcript_text: Raw transcript string
        
    Returns:
        str: Cleaned and normalized text
    """
    
    # Remove music notation
    text = re.sub(r'[♪♫🎵🎶]+', '', transcript_text)
    
    # Remove sound effect markers
    text = re.sub(r'\[.*?\]', '', text)  # [Music], [Applause], [Laughter]
    text = re.sub(r'\(.*?music.*?\)', '', text, flags=re.IGNORECASE)
    
    # Remove HTML tags and entities
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[^;]+;', '', text)
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,!?])', r'\1', text)  # Remove space before punctuation
    text = re.sub(r'([.,!?])(\w)', r'\1 \2', text)  # Add space after punctuation
    
    # Normalize whitespace (collapse multiple spaces)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_key_takeaways(transcript, count=5):
    """Extract genuine insights without mangling sentences"""
    try:
        import nltk
        from nltk.tokenize import sent_tokenize
        
        # Ensure NLTK data is available
        NLTKHelper.ensure_data()
        
        sentences = sent_tokenize(transcript)
        if len(sentences) < 5:
            return []
        
        # Score sentences by insight quality
        scored = []
        for sent in sentences:
            words = sent.split()
            if len(words) < 8 or len(words) > 45:
                continue
            
            sent_lower = sent.lower()
            score = 1  # Start with base score so all valid sentences are considered
            
            # POSITIVE signals for insights
            if re.search(r'\d+%|\d+ times?|\d+x', sent):  # Statistics
                score += 3
            if any(w in sent_lower for w in ['because', 'therefore', 'results in', 'leads to', 'causes']):
                score += 2
            if any(w in sent_lower for w in ['important', 'key', 'critical', 'essential', 'main']):
                score += 2
            if sent.split()[0] in ['Use', 'Try', 'Avoid', 'Remember', 'Consider', 'Implement']:
                score += 2
            
            # Boost score for informative patterns
            if any(w in sent_lower for w in ['allows', 'enables', 'provides', 'offers', 'supports']):
                score += 1
            if any(w in sent_lower for w in ['can', 'will', 'helps', 'makes', 'creates']):
                score += 1
            
            # NEGATIVE signals (filter out)
            if any(phrase in sent_lower for phrase in ['this video', 'this tutorial', 'i\'m going', 'we\'re going', 'click subscribe', 'don\'t forget to']):
                score -= 10
            if sent_lower.strip().startswith(('okay', 'so', 'um', 'uh', 'well', 'alright', 'and um', 'so um')):
                score -= 5
            
            # Only include sentences with positive score
            if score > 0:
                scored.append((sent.strip(), score))
        
        # If we have too few high-scoring sentences, be more lenient
        if len(scored) < count:
            # Add more sentences with lower standards
            for sent in sentences:
                words = sent.split()
                if len(words) >= 8 and len(words) <= 50:
                    sent_lower = sent.lower()
                    # Skip if already included or is meta-commentary
                    if any(s[0].lower() == sent.lower() for s in scored):
                        continue
                    if any(phrase in sent_lower for phrase in ['this video', 'this article', 'click', 'subscribe']):
                        continue
                    scored.append((sent.strip(), 0.5))
        
        # Sort by score and return top insights
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return clean sentences with deduplication
        takeaways = []
        seen = set()  # Track what we've already added
        
        for sent, _ in scored:
            # Normalize for comparison (lowercase, strip whitespace)
            normalized = sent.lower().strip()
            
            if normalized not in seen:
                seen.add(normalized)
                
                # Add emoji based on content
                if any(w in sent.lower() for w in ['avoid', 'don\'t', 'never', 'warning']):
                    takeaways.append(f"⚠️ {sent}")
                elif any(w in sent.lower()[:20] for w in ['use', 'try', 'implement']):
                    takeaways.append(f"🎯 {sent}")
                else:
                    takeaways.append(f"💡 {sent}")
                
                if len(takeaways) >= count:
                    break
        
        return takeaways
        
    except Exception as e:
        print(f"Warning: Could not extract key takeaways: {e}", file=sys.stderr)
        return []


def summarize_transcript(transcript, word_count=150):
    """Create a proper executive summary that captures main themes and key points"""
    words = transcript.split()
    
    if len(words) <= word_count:
        return transcript
    
    # Try intelligent summarization first
    try:
        import nltk
        from nltk.tokenize import sent_tokenize, word_tokenize
        from nltk.corpus import stopwords
        
        # Ensure NLTK data is available
        NLTKHelper.ensure_data()
        
        sentences = sent_tokenize(transcript)
        if len(sentences) <= 3:
            return transcript
        
        # Group sentences into thematic clusters
        # Keywords that indicate different aspects of content
        intro_keywords = ['introduce', 'welcome', 'today', 'going to cover', 'learn', 'tutorial about']
        main_concept_keywords = ['important', 'key', 'main', 'essential', 'fundamental', 'core', 'critical']
        feature_keywords = ['feature', 'tool', 'function', 'capability', 'option', 'setting']
        process_keywords = ['step', 'process', 'workflow', 'how to', 'procedure', 'method']
        benefit_keywords = ['benefit', 'advantage', 'help', 'improve', 'enable', 'allow', 'make it']
        example_keywords = ['example', 'instance', 'demonstrate', 'show', 'such as', 'for instance']
        
        stop_words = set(stopwords.words('english'))
        
        # Categorize and score sentences
        intro_sentences = []
        concept_sentences = []
        feature_sentences = []
        process_sentences = []
        benefit_sentences = []
        example_sentences = []
        
        for sentence in sentences:
            if len(sentence.split()) < 10 or len(sentence.split()) > 60:
                continue
            
            sentence_lower = sentence.lower()
            
            # Skip pure filler sentences
            if sentence_lower.startswith(('okay', 'so okay', 'alright', 'um')):
                continue
            
            # Skip meta-commentary about the video
            if 'this video' in sentence_lower and 'going to' in sentence_lower:
                if any(kw in sentence_lower for kw in intro_keywords):
                    intro_sentences.append(sentence)
                continue
            
            # Categorize based on content type
            if any(kw in sentence_lower for kw in main_concept_keywords):
                concept_sentences.append(sentence)
            elif any(kw in sentence_lower for kw in feature_keywords):
                feature_sentences.append(sentence)
            elif any(kw in sentence_lower for kw in process_keywords):
                process_sentences.append(sentence)
            elif any(kw in sentence_lower for kw in benefit_keywords):
                benefit_sentences.append(sentence)
            elif any(kw in sentence_lower for kw in example_keywords):
                example_sentences.append(sentence)
        
        # Score sentences by information density
        def score_by_density(sentence):
            words = word_tokenize(sentence.lower())
            content_words = [w for w in words if w.isalnum() and w not in stop_words and len(w) > 2]
            return len(content_words) / max(len(words), 1)
        
        # Build summary by taking best from each category
        summary_parts = []
        
        # Start with best intro if available
        if intro_sentences:
            intro_sentences.sort(key=score_by_density, reverse=True)
            best_intro = intro_sentences[0]
            # Clean up the intro
            best_intro = best_intro.replace('This video is going to cover', 'This covers')
            best_intro = best_intro.replace('going to be', 'is')
            summary_parts.append(best_intro)
        
        # Add main concepts (most important)
        if concept_sentences:
            concept_sentences.sort(key=score_by_density, reverse=True)
            for sent in concept_sentences[:2]:  # Take top 2 concept sentences
                if len(' '.join(summary_parts).split()) + len(sent.split()) <= word_count:
                    summary_parts.append(sent)
        
        # Add key features or tools
        if feature_sentences:
            feature_sentences.sort(key=score_by_density, reverse=True)
            for sent in feature_sentences[:2]:
                if len(' '.join(summary_parts).split()) + len(sent.split()) <= word_count:
                    summary_parts.append(sent)
        
        # Add process/workflow information
        if process_sentences:
            process_sentences.sort(key=score_by_density, reverse=True)
            for sent in process_sentences[:1]:
                if len(' '.join(summary_parts).split()) + len(sent.split()) <= word_count:
                    summary_parts.append(sent)
        
        # Add benefits if space allows
        if benefit_sentences:
            benefit_sentences.sort(key=score_by_density, reverse=True)
            for sent in benefit_sentences[:1]:
                if len(' '.join(summary_parts).split()) + len(sent.split()) <= word_count:
                    summary_parts.append(sent)
        
        # If we still don't have enough content, add highest scoring general sentences
        if len(summary_parts) < 3:
            all_sentences = [s for s in sentences 
                           if len(s.split()) >= 10 and len(s.split()) <= 50
                           and not s.lower().startswith(('okay', 'so', 'um', 'uh'))
                           and 'going to' not in s.lower()[:30]]
            all_sentences.sort(key=score_by_density, reverse=True)
            
            for sent in all_sentences:
                if sent not in summary_parts:
                    if len(' '.join(summary_parts).split()) + len(sent.split()) <= word_count:
                        summary_parts.append(sent)
                        if len(summary_parts) >= 5:
                            break
        
        if summary_parts:
            # Clean up the summary
            summary = ' '.join(summary_parts)
            
            # Remove redundant phrases
            summary = summary.replace('I\'m going to', 'I will')
            summary = summary.replace('We\'re going to', 'We will')
            summary = summary.replace('You\'re going to', 'You will')
            summary = summary.replace('going to be', 'is')
            summary = summary.replace('kind of', '')
            summary = summary.replace('  ', ' ')
            
            return summary.strip()
        
        # If all else fails, use fallback
        raise Exception("Could not generate meaningful summary")
        
    except Exception as e:
        # Fallback to simple extraction
        pass
    
    # Simple fallback - take beginning of transcript
    summary_words = words[:word_count]
    for i in range(word_count - 1, max(word_count - 20, 0), -1):
        if summary_words[i].endswith(('.', '!', '?')):
            summary_words = summary_words[:i+1]
            break
    
    summary = ' '.join(summary_words)
    return summary + '...' if not summary.endswith(('.', '!', '?')) else summary


def _paragraphize(transcript_text, max_words_per_paragraph=120):
    """Split transcript into readable paragraphs by sentences with a soft word cap."""
    try:
        import nltk
        from nltk.tokenize import sent_tokenize
        NLTKHelper.ensure_data()
        sentences = sent_tokenize(transcript_text)
    except Exception:
        sentences = re.split(r'(?<=[.!?])\s+', transcript_text)

    paragraphs = []
    current = []
    word_count = 0
    for s in sentences:
        w = len(s.split())
        if word_count + w > max_words_per_paragraph and current:
            paragraphs.append(' '.join(current).strip())
            current = [s]
            word_count = w
        else:
            current.append(s)
            word_count += w
    if current:
        paragraphs.append(' '.join(current).strip())
    return '\n\n'.join(paragraphs)


def format_markdown_document(title, source_url, summary, takeaways, full_text,
                           content_label="Transcript", source_id=None, next_steps=None,
                           highlights=None):
    """
    Format a comprehensive markdown document for video or article.

    Args:
        title: Content title
        source_url: Original URL
        summary: Executive summary
        takeaways: List of key takeaways (with emojis)
        full_text: Full transcript or article text
        content_label: "Transcript" or "Article"
        source_id: Video ID (optional, for videos only)
        next_steps: Recommended next steps (optional)
        highlights: List of highlight strings with timestamps/quotes (optional)
    """
    from datetime import datetime
    doc = []

    # Header with better formatting
    doc.append(f"# {title}\n")
    if source_url:
        doc.append(f"**Source:** [{source_url}]({source_url})")
    else:
        doc.append(f"**Source:** Search result")

    if source_id:
        doc.append(f"**Video ID:** `{source_id}`")
    else:
        doc.append(f"**Type:** {content_label}")

    doc.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
    doc.append("\n" + "─" * 80 + "\n")

    # Key Insights (with emojis preserved)
    if takeaways:
        doc.append("\n## 🎯 Key Insights\n")
        for i, takeaway in enumerate(takeaways, 1):
            # Preserve emojis - they are now part of the insight
            doc.append(f"{i}. {takeaway}\n")
        doc.append("\n" + "─" * 80 + "\n")

    # Highlights (timestamps for video/podcast, quotes for articles)
    if highlights:
        doc.append("\n## ⭐ Highlights\n")
        for highlight in highlights:
            doc.append(f"- {highlight}\n")
        doc.append("\n" + "─" * 80 + "\n")

    # Executive Summary
    doc.append("\n## 📝 Executive Summary\n")
    doc.append(f"{summary}\n")
    doc.append("\n" + "─" * 80 + "\n")

    # Recommended Actions (if AI available)
    if next_steps:
        doc.append("\n## 🚀 Next Steps\n")
        for step in next_steps:
            doc.append(f"- [ ] {step}\n")
        doc.append("\n" + "─" * 80 + "\n")

    # Full Content
    word_count = len(full_text.split())
    read_time = word_count // 200  # Approx reading time
    doc.append(f"\n## 📄 Full {content_label}\n")
    doc.append(f"> {word_count:,} words • ~{read_time} min read\n\n")
    doc.append(f"{_paragraphize(full_text)}\n")

    return '\n'.join(doc)


def get_unique_filepath(base_dir, base_name, extension):
    """Generate unique filepath, adding numeric suffix if file exists"""
    filepath = base_dir / f"{base_name}.{extension}"
    if not filepath.exists():
        return filepath
    
    # Add numeric suffix
    counter = 1
    while True:
        filepath = base_dir / f"{base_name}_{counter}.{extension}"
        if not filepath.exists():
            return filepath
        counter += 1


def handle_youtube_command(args):
    """Handle /youtube command"""
    # Parse arguments
    parser = argparse.ArgumentParser(
        prog='/youtube',
        description='Summarize YouTube videos and articles'
    )
    parser.add_argument('query', help='YouTube URL, article URL, or search query')
    parser.add_argument('--words', type=int, default=500,
                       help='Target word count for summary (default: 500)')
    parser.add_argument('--format', choices=['md', 'txt'], default='md',
                       help='Output format: md (markdown, default) or txt (separate files)')
    parser.add_argument('--no-takeaways', action='store_true',
                       help='Skip key takeaways extraction')
    parser.add_argument('--takeaways-count', type=int, default=5,
                       help='Number of key takeaways to extract (default: 5)')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode: skip AI processing, use extraction only (2-3x faster)')
    parser.add_argument('--show-metrics', action='store_true',
                       help='Display transcript source metrics summary')
    # AI provider options
    if AI_AVAILABLE:
        parser.add_argument('--ai-provider', choices=['openai', 'anthropic', 'deepseek', 'ollama', 'openrouter', 'groq', 'none'],
                           default='ollama',
                           help='AI provider for enhanced summarization (default: ollama with Qwen 7B)')
        parser.add_argument('--ai-model', type=str,
                           help='Specific AI model to use (e.g., gpt-4, claude-3-sonnet, deepseek-chat)')
    else:
        parser.add_argument('--ai-provider', choices=['none'], default='none',
                           help='AI summarization not available (install requirements_ai.txt)')
    
    try:
        parsed_args = parser.parse_args(args)
    except SystemExit:
        return 1
    
    query = parsed_args.query
    word_count = parsed_args.words
    output_format = parsed_args.format
    skip_takeaways = parsed_args.no_takeaways
    takeaways_count = parsed_args.takeaways_count
    fast_mode = parsed_args.fast
    
    # AI provider settings
    ai_provider = getattr(parsed_args, 'ai_provider', 'none')
    ai_model = getattr(parsed_args, 'ai_model', None)

    # Fast mode overrides AI
    if fast_mode:
        ai_provider = 'none'
        print("⚡ Fast mode enabled - using extraction methods only")
    
    # Initialize AI summarizer if available and requested
    ai_summarizer = None
    if AI_AVAILABLE and ai_provider != 'none':
        try:
            ai_summarizer = AITranscriptSummarizer(provider=ai_provider, model=ai_model)
            if ai_summarizer.is_available():
                print(f"✓ Using {ai_provider} AI (model: {ai_summarizer.model}) for enhanced summarization")
            else:
                print(f"⚠ {ai_provider} not configured, falling back to extraction method")
                ai_summarizer = None
        except Exception as e:
            print(f"⚠ Could not initialize AI: {e}")
            ai_summarizer = None
    
    # Ensure output directory exists - use organized folder structure
    # Will determine subfolder (youtube/article/podcast) based on content type later
    base_output_dir = Path.home() / "Documents" / "zz. AI Content Summaries"
    base_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing: {query}\n")
    
    # Detect content type
    content_type, identifier = detect_content_type(query)
    
    if content_type == ContentType.ARTICLE:
        print(f"Detected content type: article")
        print(f"Fetching article from: {identifier}...\n")
    elif content_type == ContentType.X_ARTICLE:
        print(f"Detected content type: X/Twitter article")
        print(f"Fetching X article from: {identifier}...\n")
    elif content_type == ContentType.WEB_SEARCH:
        # Parse: WEBSEARCH:{num_results}:{query}
        parts = identifier.split(':', 2)
        search_query = parts[2] if len(parts) == 3 else identifier
        print(f"Detected content type: web search")
        print(f"Searching for: {search_query}...\n")
    elif content_type == ContentType.PODCAST:
        print(f"Detected content type: podcast (URL)")
    elif content_type == ContentType.PODCAST_SEARCH:
        print(f"Detected content type: podcast (search query)")
    elif content_type == ContentType.DIRECT_AUDIO:
        print(f"Detected content type: direct audio file")
    elif content_type == ContentType.TWITTER_VIDEO:
        print(f"Detected content type: Twitter/X video (live broadcast)")
    else:
        print(f"Detected content type: video")
    
    # Process based on content type
    content_text = None
    content_title = None
    source_url = None
    source_id = None
    content_label = "Transcript"
    timestamp_data = None  # Timestamp data for highlights (video only)
    
    if content_type == ContentType.ARTICLE:
        # Article pipeline
        try:
            content_title, content_text = fetch_article_content(identifier)
            source_url = identifier
            content_label = "Article"
            
            word_count_actual = len(content_text.split())
            print(f"✓ Article fetched ({len(content_text)} characters, {word_count_actual} words)")
            print(f"Title: {content_title}")
            
            # Assess content quality
            quality_warnings = assess_content_quality(content_text, "article")
            if quality_warnings:
                print("\nContent Quality Notes:")
                for warning in quality_warnings:
                    print(f"  {warning}")
            print()
            
        except (ConnectionError, ValueError, ImportError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error fetching article: {e}", file=sys.stderr)
            return 1

    elif content_type == ContentType.X_ARTICLE:
        # X/Twitter article pipeline (uses Jina Reader with fallbacks)
        try:
            content_title, content_text = fetch_x_article_content(identifier)
            source_url = identifier
            content_label = "Article"

            word_count_actual = len(content_text.split())
            print(f"✓ X article fetched ({len(content_text)} characters, {word_count_actual} words)")
            print(f"Title: {content_title}")

            # Assess content quality
            quality_warnings = assess_content_quality(content_text, "article")
            if quality_warnings:
                print("\nContent Quality Notes:")
                for warning in quality_warnings:
                    print(f"  {warning}")
            print()

        except (ConnectionError, ValueError, ImportError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error fetching X article: {e}", file=sys.stderr)
            return 1

    elif content_type == ContentType.WEB_SEARCH:
        # Web search pipeline (uses Jina Search API)
        try:
            # Parse: WEBSEARCH:{num_results}:{query}
            parts = identifier.split(':', 2)
            if len(parts) != 3:
                raise ValueError("Invalid web search format")

            num_results = int(parts[1])
            search_query = parts[2]

            content_title, content_text, sources = jina_search(search_query, num_results=num_results)
            source_url = f"search://{search_query}"
            content_label = "Article"

            word_count_actual = len(content_text.split())
            print(f"✓ Web search completed ({len(content_text)} characters, {word_count_actual} words)")
            print(f"Title: {content_title}")
            print(f"Sources: {len(sources)} articles")

            # Show sources
            if sources:
                print("\nSources:")
                for i, src in enumerate(sources, 1):
                    print(f"  {i}. {src.get('title', 'Untitled')}")
                    if src.get('url'):
                        print(f"     {src['url']}")

            # Assess content quality
            quality_warnings = assess_content_quality(content_text, "article")
            if quality_warnings:
                print("\nContent Quality Notes:")
                for warning in quality_warnings:
                    print(f"  {warning}")
            print()

        except (ConnectionError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error performing web search: {e}", file=sys.stderr)
            return 1

    elif content_type == ContentType.PODCAST:
        # Podcast pipeline (URL-based)
        try:
            content_title, content_text, content_label = handle_podcast_content(identifier)
            source_url = identifier
            source_id = None
            
            word_count_actual = len(content_text.split())
            print(f"✓ Podcast processed ({len(content_text)} characters, {word_count_actual} words)")
            print(f"Title: {content_title}")
            
            # Assess content quality
            quality_warnings = assess_content_quality(content_text, "podcast")
            if quality_warnings:
                print("\nContent Quality Notes:")
                for warning in quality_warnings:
                    print(f"  {warning}")
            print()
            
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            print("\nNote: Simple mode only works with podcasts that include transcripts in their RSS feed.", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error processing podcast: {e}", file=sys.stderr)
            return 1
    
    elif content_type == ContentType.PODCAST_SEARCH:
        # NEW: Podcast pipeline (search-based)
        try:
            content_title, content_text, content_label = handle_podcast_search(identifier)
            source_url = None
            source_id = None
            
            word_count_actual = len(content_text.split())
            print(f"✓ Podcast processed ({len(content_text)} characters, {word_count_actual} words)")
            print(f"Title: {content_title}")
            
            # Assess content quality
            quality_warnings = assess_content_quality(content_text, "podcast")
            if quality_warnings:
                print("\nContent Quality Notes:")
                for warning in quality_warnings:
                    print(f"  {warning}")
            print()
            
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error processing podcast search: {e}", file=sys.stderr)
            return 1

    elif content_type == ContentType.DIRECT_AUDIO:
        # Direct audio file pipeline
        try:
            content_title, content_text, content_label = handle_direct_audio(identifier)
            source_url = identifier
            source_id = None

            word_count_actual = len(content_text.split())
            print(f"✓ Audio processed ({len(content_text)} characters, {word_count_actual} words)")
            print(f"Title: {content_title}")

            # Assess content quality
            quality_warnings = assess_content_quality(content_text, "audio")
            if quality_warnings:
                print("\nContent Quality Notes:")
                for warning in quality_warnings:
                    print(f"  {warning}")
            print()

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error processing audio file: {e}", file=sys.stderr)
            return 1

    elif content_type == ContentType.TWITTER_VIDEO:
        # Twitter/X video pipeline
        try:
            # Download video
            video_path, video_title = download_twitter_video(identifier)
            
            if not video_path:
                print(f"Error: Failed to download Twitter video", file=sys.stderr)
                return 1
            
            # Transcribe
            print(f"🎤 Transcribing video with Whisper...")
            transcript, mode_used = transcribe_audio_whisper(video_path, mode='full', max_duration_minutes=120)
            
            if not transcript:
                print(f"Error: Transcription failed", file=sys.stderr)
                return 1
            
            word_count_actual = len(transcript.split())
            print(f"✓ Transcription complete ({len(transcript)} characters, {word_count_actual} words)")
            print(f"Title: {video_title}")
            
            content_text = transcript
            content_title = video_title
            source_url = identifier
            source_id = None
            content_label = "Transcript"
            
            # Assess content quality
            quality_warnings = assess_content_quality(content_text, "video")
            if quality_warnings:
                print("\nContent Quality Notes:")
                for warning in quality_warnings:
                    print(f"  {warning}")
            print()
            
            # Cleanup
            try:
                import os
                os.remove(video_path)
                os.rmdir(os.path.dirname(video_path))
            except:
                pass
                
        except Exception as e:
            print(f"Error processing Twitter video: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
    
    else:
        # Video pipeline (existing logic)
        video_id = None
        video_title = None
        
        if is_url(identifier) or re.match(r'^[a-zA-Z0-9_-]{11}$', identifier):
            # Extract video ID from URL or use directly
            try:
                video_id = extract_video_id(identifier)
                print(f"Video ID: {video_id}")
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1
        else:
            # Search for video
            print(f"Searching YouTube for: '{identifier}'...")
            video_data = search_youtube(identifier)
            
            if not video_data:
                print("Error: No results found", file=sys.stderr)
                return 1
            
            video_id = video_data['id']
            video_title = video_data['title']
            
            print(f"Found: {video_title}")
            print(f"URL: {video_data['url']}")
            print(f"Video ID: {video_id}\n")
        
        # Fetch transcript with timestamps for highlights
        print("Fetching transcript...")
        try:
            transcript_raw, timestamp_data = fetch_transcript_with_timestamps(video_id)

            # Assess content quality BEFORE cleaning (to detect music)
            quality_warnings = assess_content_quality(transcript_raw, "video")
            
            transcript = clean_transcript(transcript_raw)
            
            if len(transcript) < 50:
                print("Error: Transcript is too short or empty", file=sys.stderr)
                return 1
            
            print(f"✓ Transcript fetched ({len(transcript)} characters, {len(transcript.split())} words)")
            
            # Show quality warnings if any
            if quality_warnings:
                print("\nContent Quality Notes:")
                for warning in quality_warnings:
                    print(f"  {warning}")
            print()
            
            content_text = transcript
            content_title = video_title
            source_id = video_id
            source_url = f"https://www.youtube.com/watch?v={video_id}"
            content_label = "Transcript"
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    # Generate summary
    print(f"Generating summary (target: {word_count} words)...")
    
    # Use AI if available, otherwise fallback to extraction
    if ai_summarizer:
        # Check cache first
        cache_params = {'word_count': word_count, 'title': content_title or "Content"}
        cached_summary = get_cached_ai_response(content_text, 'summary', cache_params)

        if cached_summary:
            summary = cached_summary
        else:
            summary = ai_summarizer.generate_executive_summary(
                content_text, content_title or "Content", word_count
            )
            if summary:
                save_ai_response(content_text, 'summary', cache_params, summary)
            else:
                print("⚠ AI summary generation failed, using extraction method")
                summary = summarize_transcript(content_text, word_count)
    else:
        summary = summarize_transcript(content_text, word_count)
    
    summary_word_count = len(summary.split())
    print(f"✓ Summary generated ({summary_word_count} words)")
    
    # Extract key takeaways
    takeaways = []
    if not skip_takeaways:
        print(f"Extracting key insights (target: {takeaways_count})...")
        
        # Use AI if available
        if ai_summarizer:
            # Check cache first
            cache_params = {'count': takeaways_count, 'title': content_title or "Content"}
            cached_takeaways = get_cached_ai_response(content_text, 'takeaways', cache_params)

            if cached_takeaways:
                takeaways = cached_takeaways
            else:
                # Takeaways now come with emojis from the AI prompt
                takeaways = ai_summarizer.generate_key_takeaways(
                    content_text, content_title or "Content", takeaways_count
                )
                if takeaways:
                    save_ai_response(content_text, 'takeaways', cache_params, takeaways)
                else:
                    print("⚠ AI takeaway generation failed, using extraction method")
                    takeaways = extract_key_takeaways(content_text, takeaways_count)
        else:
            takeaways = extract_key_takeaways(content_text, takeaways_count)
        
        if takeaways:
            print(f"✓ Extracted {len(takeaways)} key insights")
        else:
            print("⚠ No key takeaways extracted")
    
    # Generate filename slug
    if content_title:
        slug = slugify(content_title)
    elif source_id:
        # For videos without title, try to fetch using yt-dlp
        try:
            cmd = [sys.executable, '-m', 'yt_dlp', '--print', 'title', '--skip-download',
                   f'https://www.youtube.com/watch?v={source_id}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                content_title = result.stdout.strip()
                slug = slugify(content_title)
            else:
                slug = source_id
                content_title = f"Video {source_id}"
        except:
            slug = source_id
            content_title = f"Video {source_id}"
    else:
        # For articles without title
        slug = "article"
        content_title = "Article"
    
    # Generate next steps if AI is available
    next_steps = []
    if ai_summarizer and takeaways:
        print("Generating recommended next steps...")

        # Check cache first
        cache_params = {'title': content_title, 'takeaways': takeaways[:3]}  # Use first 3 for cache key
        cached_next_steps = get_cached_ai_response(content_text, 'next_steps', cache_params)

        if cached_next_steps:
            next_steps = cached_next_steps
            print(f"✓ Generated {len(next_steps)} next steps")
        else:
            next_steps = ai_summarizer.generate_next_steps(content_text, content_title, takeaways)
            if next_steps:
                save_ai_response(content_text, 'next_steps', cache_params, next_steps)
                print(f"✓ Generated {len(next_steps)} next steps")

    # Generate highlights (timestamps for video/podcast, quotes for articles)
    highlights = []
    if ai_summarizer:
        print("Generating highlights...")

        # Determine content type for highlights
        if content_type in [ContentType.ARTICLE, ContentType.X_ARTICLE, ContentType.WEB_SEARCH]:
            hl_content_type = "article"
        elif content_type in [ContentType.PODCAST, ContentType.PODCAST_SEARCH]:
            hl_content_type = "podcast"
        else:
            hl_content_type = "video"

        # Check cache first
        cache_params = {'title': content_title, 'type': hl_content_type}
        cached_highlights = get_cached_ai_response(content_text, 'highlights', cache_params)

        if cached_highlights:
            highlights = cached_highlights
            print(f"✓ Generated {len(highlights)} highlights")
        else:
            # Use timestamp_data if available (set in video pipeline)
            highlights = ai_summarizer.generate_highlights(
                content_text,
                content_title,
                content_type=hl_content_type,
                timestamp_data=timestamp_data,
                count=7
            )
            if highlights:
                save_ai_response(content_text, 'highlights', cache_params, highlights)
                print(f"✓ Generated {len(highlights)} highlights")

    # Format transcript with bold/highlights if AI available
    formatted_content = content_text
    if ai_summarizer:
        print("Formatting transcript with highlights...")
        cache_params = {'title': content_title or "Content"}
        cached_formatted = get_cached_ai_response(content_text, 'formatted_transcript', cache_params)

        if cached_formatted:
            formatted_content = cached_formatted
            print("✓ Using cached formatted transcript")
        else:
            try:
                formatted_content = ai_summarizer.format_transcript(
                    content_text, content_title or "Content"
                )
                if formatted_content and formatted_content != content_text:
                    save_ai_response(content_text, 'formatted_transcript', cache_params, formatted_content)
                    print("✓ Transcript formatted with bold and highlights")
                else:
                    formatted_content = content_text
                    print("⚠ Transcript formatting skipped")
            except Exception as e:
                print(f"⚠ Transcript formatting failed: {e}")
                formatted_content = content_text

    # Save files based on format
    if output_format == 'md':
        # Save as single markdown file
        markdown_content = format_markdown_document(
            title=content_title,
            source_url=source_url,
            summary=summary,
            takeaways=takeaways,
            full_text=formatted_content,
            content_label=content_label,
            source_id=source_id,
            next_steps=next_steps,
            highlights=highlights
        )
        
        # Determine correct subfolder based on content type
        if content_type == ContentType.VIDEO or content_type == ContentType.TWITTER_VIDEO:
            output_dir = base_output_dir / "youtube"
        elif content_type in [ContentType.ARTICLE, ContentType.X_ARTICLE, ContentType.WEB_SEARCH]:
            output_dir = base_output_dir / "article"
        elif content_type in [ContentType.PODCAST, ContentType.PODCAST_SEARCH, ContentType.DIRECT_AUDIO]:
            output_dir = base_output_dir / "podcast"
        else:
            output_dir = base_output_dir / "youtube"  # Default fallback

        output_dir.mkdir(parents=True, exist_ok=True)

        md_file = get_unique_filepath(output_dir, slug, "md")
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"✓ Markdown document saved: {md_file}")
        
    else:
        # Save as separate text files (legacy format)
        # Determine correct subfolder based on content type
        if content_type == ContentType.VIDEO or content_type == ContentType.TWITTER_VIDEO:
            output_dir = base_output_dir / "youtube"
        elif content_type in [ContentType.ARTICLE, ContentType.X_ARTICLE, ContentType.WEB_SEARCH]:
            output_dir = base_output_dir / "article"
        elif content_type in [ContentType.PODCAST, ContentType.PODCAST_SEARCH, ContentType.DIRECT_AUDIO]:
            output_dir = base_output_dir / "podcast"
        else:
            output_dir = base_output_dir / "youtube"  # Default fallback

        output_dir.mkdir(parents=True, exist_ok=True)

        content_file = get_unique_filepath(output_dir, slug, f"{content_label.lower()}.txt")
        summary_file = get_unique_filepath(output_dir, slug, "summary.txt")
        
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content_text)
        print(f"✓ {content_label} saved: {content_file}")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"✓ Summary saved: {summary_file}")
    
    # Display key takeaways and summary
    print("\n" + "="*70)
    
    if takeaways:
        print("KEY INSIGHTS")
        print("="*70)
        for i, takeaway in enumerate(takeaways, 1):
            print(f"{i}. {takeaway}")
        print("\n" + "="*70)
    
    print("SUMMARY")
    print("="*70)
    print(summary)
    print("="*70)
    
    # Statistics
    content_words = len(content_text.split())
    reduction = round((1 - summary_word_count/content_words) * 100, 1)
    print(f"\nStatistics:")
    print(f"  Original: {content_words} words")
    print(f"  Summary: {summary_word_count} words")
    print(f"  Reduction: {reduction}%")
    if takeaways:
        print(f"  Key Takeaways: {len(takeaways)}")
    
    # Show metrics if requested
    if parsed_args.show_metrics and LISTEN_NOTES_AVAILABLE:
        metrics = TranscriptMetrics()
        metrics.print_summary()
    
    return 0


if __name__ == "__main__":
    sys.exit(handle_youtube_command(sys.argv[1:]))
