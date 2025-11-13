"""Unified processing interface for content summarization.

This module provides a single entry point for processing different types of content
(URLs, files, text) and routes to appropriate handlers.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional


def process_content(
    input_type: str,
    content: Any,
    words: int,
    api_key: str,
    script_module: str = "content_summarizer.youtube_slash_command"
) -> Dict[str, Any]:
    """Unified content processing interface.
    
    Args:
        input_type: One of "url", "file", "text"
        content: URL string, file object, or text string
        words: Target word count for summary
        api_key: GROQ_API_KEY for AI summarization
        script_module: Module path for CLI processor
        
    Returns:
        Dictionary with processing results:
        {
            'success': bool,
            'markdown': str (if saved),
            'takeaways': list,
            'summary': str,
            'transcript': str,
            'saved_path': str (if saved to file),
            'error': str (if failed)
        }
    """
    if input_type == "url":
        return _process_url(content, words, api_key, script_module)
    elif input_type == "file":
        return _process_file(content, words, api_key)
    elif input_type == "text":
        return _process_text(content, words, api_key)
    else:
        return {'success': False, 'error': f"Unknown input type: {input_type}"}


def _process_url(url: str, words: int, api_key: str, script_module: str) -> Dict[str, Any]:
    """Process URL using CLI module."""
    env = os.environ.copy()
    env['GROQ_API_KEY'] = api_key
    
    cmd = [
        "python3", "-m", script_module, url,
        "--format", "md",
        "--words", str(words),
        "--ai-provider", os.getenv("AI_PROVIDER", "groq"),
        "--ai-model", os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)
        output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        
        # Parse markdown file path
        match = re.search(r"Markdown document saved:\s*(.+)", output)
        if result.returncode == 0 and match:
            path = match.group(1).strip()
            
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    markdown = f.read()
                
                return {
                    'success': True,
                    'markdown': markdown,
                    'saved_path': path,
                    'output': output
                }
        
        return {
            'success': False,
            'error': output,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Processing timed out (>5 minutes)'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _process_file(uploaded_file, words: int, api_key: str) -> Dict[str, Any]:
    """Process uploaded file (audio/video/PDF).
    
    Note: This is a placeholder for the existing inline subprocess logic.
    Full refactor would extract the inline Python scripts to proper modules.
    """
    # This would contain the file processing logic
    # For now, keeping the existing implementation in app.py
    # Full refactor would extract subprocess scripts to proper functions
    return {
        'success': False,
        'error': 'File processing logic still in app.py (legacy compatibility)'
    }


def _process_text(text: str, words: int, api_key: str) -> Dict[str, Any]:
    """Process pasted text content.
    
    Note: This is a placeholder for the existing inline subprocess logic.
    Full refactor would extract the inline Python scripts to proper modules.
    """
    # This would contain the text processing logic
    # For now, keeping the existing implementation in app.py
    # Full refactor would extract subprocess scripts to proper functions
    return {
        'success': False,
        'error': 'Text processing logic still in app.py (legacy compatibility)'
    }


def parse_result_markers(output: str) -> Dict[str, Any]:
    """Parse TRANSCRIPT_START/END, TAKEAWAYS_START/END, SUMMARY_START/END markers.
    
    Args:
        output: Raw output from processing scripts
        
    Returns:
        Dictionary with parsed sections
    """
    result = {}
    
    # Parse transcript
    if "TRANSCRIPT_START" in output and "TRANSCRIPT_END" in output:
        result['transcript'] = output.split("TRANSCRIPT_START")[1].split("TRANSCRIPT_END")[0].strip()
    
    # Parse takeaways
    if "TAKEAWAYS_START" in output and "TAKEAWAYS_END" in output:
        takeaways_section = output.split("TAKEAWAYS_START")[1].split("TAKEAWAYS_END")[0]
        result['takeaways'] = [line.strip() for line in takeaways_section.strip().split('\n') if line.strip()]
    
    # Parse summary
    if "SUMMARY_START" in output and "SUMMARY_END" in output:
        result['summary'] = output.split("SUMMARY_START")[1].split("SUMMARY_END")[0].strip()
    
    # Parse saved path
    if "SAVED_TO:" in output:
        match = re.search(r"SAVED_TO:(.+)", output)
        if match:
            result['saved_path'] = match.group(1).strip()
    
    return result
