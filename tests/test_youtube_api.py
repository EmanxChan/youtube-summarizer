from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    if "youtube.com/watch?v=" in url:
        return parse_qs(urlparse(url).query)["v"][0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format")

def test_video(video_id):
    """Test what transcripts are available for a video"""
    print(f"\n=== Testing Video: {video_id} ===")
    
    try:
        # List all available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        print(f"Available transcript count: {len(list(transcript_list))}")
        
        # Display transcript info
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            print(f"Language: {transcript.language_code} ({transcript.language}) - Generated: {transcript.is_generated}")
            
        # Try to fetch transcript
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-gb'])
            print("\nFetching English transcript...")
            data = transcript.fetch()
            print(f"Transcript segments: {len(data)}")
            
            if len(data) > 0:
                print(f"First segment: {data[0]}")
                print(f"Last segment: {data[-1]}")
                print(f"Total text length: {sum(len(item['text']) for item in data)} characters")
            
        except Exception as e:
            print(f"Error fetching English transcript: {e}")
            
            # Try any transcript
            try:
                any_transcript = list(transcript_list)[0]
                print(f"\nTrying {any_transcript.language_code} transcript...")
                data = any_transcript.fetch()
                print(f"Transcript segments: {len(data)}")
                
                if len(data) > 0:
                    print(f"First segment: {data[0]}")
                    print(f"Total text length: {sum(len(item['text']) for item in data)} characters")
                    
            except Exception as e2:
                print(f"Error fetching any transcript: {e2}")
        
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video")
    except NoTranscriptFound:
        print("No transcript found for this video")
    except Exception as e:
        print(f"General error: {e}")

# Test both videos
test_video("mgiC05hLOck")  # User's video
test_video("pxiP-HJLCx0")   # Example TED talk that should have transcripts
