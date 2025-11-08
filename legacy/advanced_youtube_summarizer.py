#!/usr/bin/env python3
import sys
import argparse
from urllib.parse import urlparse, parse_qs
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Download NLTK data (only needed once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    if "youtube.com/watch?v=" in url:
        return parse_qs(urlparse(url).query)["v"][0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format")

def get_youtube_transcript(video_id):
    """Get transcript using youtube-transcript-api"""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine transcript segments
        full_transcript = " ".join([item['text'] for item in transcript])
        return full_transcript
        
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video")
        return None
    except NoTranscriptFound:
        print("No transcript found for this video")
        try:
            # Try to get auto-generated transcript
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            for transcript in transcript_list:
                if transcript.is_generated:
                    transcript_data = transcript.fetch()
                    return " ".join([item['text'] for item in transcript_data])
        except Exception as e:
            print(f"Error getting auto transcript: {e}")
        return None
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def preprocess_text(text):
    """Preprocess text for summarization"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def extractive_summarize(text, num_sentences=5):
    """Extractive summarization using TF-IDF scores"""
    try:
        # Tokenize text into sentences
        sentences = sent_tokenize(text)
        
        if len(sentences) <= num_sentences:
            return text
        
        # Calculate TF-IDF scores
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(sentences)
        
        # Calculate sentence similarity scores
        sentence_scores = np.array(tfidf_matrix.sum(axis=1)).flatten()
        
        # Get top sentences
        top_sentence_indices = sentence_scores.argsort()[-num_sentences:][::-1]
        top_sentence_indices = sorted(top_sentence_indices)  # Maintain chronological order
        
        # Generate summary
        summary = ' '.join([sentences[i] for i in top_sentence_indices])
        return summary
        
    except Exception as e:
        print(f"Error in extractive summarization: {e}")
        # Fallback to simple truncation
        sentences = sent_tokenize(text)
        if sentences:
            return ' '.join(sentences[:min(num_sentences, len(sentences))])
        return text[:500] + "..."

def summarize_transcript_simple(transcript, word_count=150):
    """Simple word-count based summary"""
    sentences = sent_tokenize(transcript)
    
    summary_sentences = []
    word_total = 0
    
    for sentence in sentences:
        sentence_words = len(word_tokenize(sentence))
        if word_total + sentence_words <= word_count:
            summary_sentences.append(sentence)
            word_total += sentence_words
        else:
            break
    
    return ' '.join(summary_sentences)

def main():
    parser = argparse.ArgumentParser(description='Extract and summarize YouTube video transcripts')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--output', '-o', help='Output file for transcript')
    parser.add_argument('--summary', '-s', help='Output file for summary')
    parser.add_argument('--words', '-w', type=int, default=150, help='Target word count for summary')
    parser.add_argument('--sentences', '-n', type=int, default=5, help='Number of sentences for extractive summary')
    parser.add_argument('--method', '-m', choices=['simple', 'extractive'], default='extractive', 
                        help='Summarization method')
    
    args = parser.parse_args()
    
    try:
        # Extract video ID
        video_id = extract_video_id(args.url)
        print(f"Processing video ID: {video_id}")
        
        # Get transcript
        print("Fetching transcript...")
        transcript = get_youtube_transcript(video_id)
        
        if not transcript:
            print("Failed to get transcript. Please check the video URL.")
            sys.exit(1)
        
        print(f"Transcript length: {len(transcript)} characters")
        
        # Save transcript
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"Transcript saved to {args.output}")
        
        # Generate summary
        print("Generating summary...")
        if args.method == 'extractive':
            summary = extractive_summarize(transcript, args.sentences)
        else:
            summary = summarize_transcript_simple(transcript, args.words)
        
        # Save summary
        if args.summary:
            with open(args.summary, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"Summary saved to {args.summary}")
        
        # Display results
        print("\n" + "="*50)
        print("VIDEO SUMMARY")
        print("="*50)
        print(summary)
        print(f"\nOriginal: {len(transcript)} characters")
        print(f"Summary: {len(summary)} characters")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
