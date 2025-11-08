#!/usr/bin/env python3
"""
Unit tests for YouTube slash command functionality.
"""
import unittest
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_slash_command import (
    slugify,
    extract_video_id,
    is_url,
    clean_transcript,
    summarize_transcript,
    get_unique_filepath
)


class TestSlugify(unittest.TestCase):
    """Test filename slugification"""
    
    def test_basic_slugify(self):
        """Test basic text to slug conversion"""
        self.assertEqual(slugify("Hello World"), "hello-world")
        self.assertEqual(slugify("Machine Learning Tutorial"), "machine-learning-tutorial")
    
    def test_special_characters(self):
        """Test removal of special characters"""
        self.assertEqual(slugify("Hello, World!"), "hello-world")
        self.assertEqual(slugify("Test (Part 1) - Introduction"), "test-part-1-introduction")
        self.assertEqual(slugify("C++ Tutorial #1"), "c-tutorial-1")
    
    def test_max_length(self):
        """Test max length truncation"""
        long_text = "a" * 150
        result = slugify(long_text, max_length=50)
        self.assertEqual(len(result), 50)
    
    def test_empty_fallback(self):
        """Test fallback for empty input"""
        self.assertEqual(slugify("!!!"), "untitled")
        self.assertEqual(slugify(""), "untitled")


class TestExtractVideoId(unittest.TestCase):
    """Test video ID extraction"""
    
    def test_standard_url(self):
        """Test standard YouTube URL format"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")
    
    def test_short_url(self):
        """Test shortened youtu.be URL format"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")
    
    def test_url_with_params(self):
        """Test URL with additional parameters"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")
    
    def test_short_url_with_params(self):
        """Test short URL with parameters"""
        url = "https://youtu.be/dQw4w9WgXcQ?t=42"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")
    
    def test_video_id_passthrough(self):
        """Test passing video ID directly"""
        video_id = "dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(video_id), "dQw4w9WgXcQ")
    
    def test_invalid_url(self):
        """Test invalid URL format"""
        with self.assertRaises(ValueError):
            extract_video_id("https://example.com/video")
        with self.assertRaises(ValueError):
            extract_video_id("not a url or id")


class TestIsUrl(unittest.TestCase):
    """Test URL detection"""
    
    def test_http_urls(self):
        """Test HTTP and HTTPS URLs"""
        self.assertTrue(is_url("http://youtube.com"))
        self.assertTrue(is_url("https://youtube.com"))
    
    def test_short_urls(self):
        """Test youtu.be URLs"""
        self.assertTrue(is_url("youtu.be/abc123"))
    
    def test_non_urls(self):
        """Test non-URL strings"""
        self.assertFalse(is_url("machine learning"))
        self.assertFalse(is_url("python tutorial"))
        self.assertFalse(is_url("dQw4w9WgXcQ"))


class TestCleanTranscript(unittest.TestCase):
    """Test transcript cleaning"""
    
    def test_remove_tags(self):
        """Test removal of XML/HTML tags"""
        text = "Hello <b>world</b> this is a test"
        self.assertEqual(clean_transcript(text), "Hello world this is a test")
    
    def test_remove_entities(self):
        """Test removal of HTML entities"""
        text = "Hello &amp; goodbye &nbsp; test"
        self.assertEqual(clean_transcript(text), "Hello goodbye test")
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization"""
        text = "Hello    world\n\n  test  "
        self.assertEqual(clean_transcript(text), "Hello world test")
    
    def test_combined_cleaning(self):
        """Test combined cleaning operations"""
        text = "Hello <span>world</span>   &amp;   test\n\n"
        self.assertEqual(clean_transcript(text), "Hello world test")


class TestSummarizeTranscript(unittest.TestCase):
    """Test transcript summarization"""
    
    def test_short_transcript(self):
        """Test transcript shorter than word count"""
        text = "This is a short transcript."
        result = summarize_transcript(text, word_count=100)
        self.assertEqual(result, text)
    
    def test_exact_word_count(self):
        """Test summarization to exact word count"""
        words = ["word"] * 200
        text = " ".join(words)
        result = summarize_transcript(text, word_count=100)
        self.assertTrue(len(result.split()) <= 105)  # Allow small margin
    
    def test_sentence_boundary(self):
        """Test ending at sentence boundary"""
        text = " ".join(["word"] * 50) + ". " + " ".join(["word"] * 100)
        result = summarize_transcript(text, word_count=60)
        # Should end at the sentence boundary (50 words + period)
        self.assertTrue(result.endswith('.'))
    
    def test_ellipsis_added(self):
        """Test ellipsis added when no sentence boundary"""
        text = " ".join(["word"] * 200)
        result = summarize_transcript(text, word_count=100)
        self.assertTrue(result.endswith('...'))


class TestGetUniqueFilepath(unittest.TestCase):
    """Test unique filepath generation"""
    
    def setUp(self):
        """Create temporary directory for tests"""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir)
    
    def test_no_collision(self):
        """Test filepath when no file exists"""
        filepath = get_unique_filepath(self.temp_dir, "test", "txt")
        self.assertEqual(filepath, self.temp_dir / "test.txt")
    
    def test_single_collision(self):
        """Test filepath with one existing file"""
        # Create first file
        (self.temp_dir / "test.txt").touch()
        
        filepath = get_unique_filepath(self.temp_dir, "test", "txt")
        self.assertEqual(filepath, self.temp_dir / "test_1.txt")
    
    def test_multiple_collisions(self):
        """Test filepath with multiple existing files"""
        # Create multiple files
        (self.temp_dir / "test.txt").touch()
        (self.temp_dir / "test_1.txt").touch()
        (self.temp_dir / "test_2.txt").touch()
        
        filepath = get_unique_filepath(self.temp_dir, "test", "txt")
        self.assertEqual(filepath, self.temp_dir / "test_3.txt")


if __name__ == '__main__':
    unittest.main()
