from pytube import YouTube
import os
import re
import sys

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    # For standard YouTube URLs
    if 'youtube.com/watch' in url:
        video_id = re.search(r'v=([\w-]+)', url)
        if video_id:
            return video_id.group(1)
    
    # For YouTube Shorts
    elif 'youtube.com/shorts' in url:
        video_id = re.search(r'shorts/([\w-]+)', url)
        if video_id:
            return video_id.group(1)
    
    # For youtu.be short URLs
    elif 'youtu.be/' in url:
        video_id = re.search(r'youtu\.be/([\w-]+)', url)
        if video_id:
            return video_id.group(1)
    
    return None

def download_youtube_video(url, output_path='.'):
    try:
        # Extract video ID and create a clean URL
        video_id = extract_video_id(url)
        if not video_id:
            print(f"Could not extract video ID from URL: {url}")
            return
        
        clean_url = f'https://www.youtube.com/watch?v={video_id}'
        print(f"Using URL: {clean_url}")
        
        # Create YouTube object with additional options to avoid errors
        print("Initializing YouTube object...")
        yt = YouTube(
            clean_url,
            use_oauth=False,
            allow_oauth_cache=False,
            on_progress_callback=lambda stream, chunk, bytes_remaining: print(f"Downloaded {(1 - bytes_remaining / stream.filesize) * 100:.1f}%", end="\r")
        )
        
        # Print video information for debugging
        print(f"Video title: {yt.title}")
        print(f"Video length: {yt.length} seconds")
        
        # Get available streams
        print("Finding available streams...")
        streams = yt.streams.filter(progressive=True).order_by('resolution').desc()
        
        if not streams:
            print("No progressive streams found. Trying any available stream...")
            streams = yt.streams.order_by('resolution').desc()
        
        if not streams or len(streams) == 0:
            raise Exception("No available streams found for this video")
        
        # Print available streams for debugging
        print("\nAvailable streams:")
        for i, s in enumerate(streams[:5]):  # Show top 5 streams
            print(f"{i+1}. Resolution: {s.resolution}, Format: {s.mime_type}, Size: {s.filesize_mb:.1f}MB")
        
        # Select the highest resolution stream
        stream = streams.first()
        print(f"\nSelected stream: Resolution: {stream.resolution}, Format: {stream.mime_type}")
        
        # Download video
        print(f"\nDownloading: {yt.title}")
        output_file = stream.download(output_path)
        print(f"\nDownload completed! Saved to: {output_file}")
    
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Make sure the video is not age-restricted or private")
        print("3. Try updating pytube: py -m pip install --upgrade pytube")
        print("4. Try a different video URL")
        print("5. For detailed error information, run with debug flag: py youtube_downloader.py --debug")
        
        # Print detailed error information if debug flag is set
        if '--debug' in sys.argv:
            import traceback
            print("\nDetailed error information:")
            traceback.print_exc()

if __name__ == "__main__":
    # Check for debug flag
    debug_mode = '--debug' in sys.argv
    if debug_mode:
        print("Running in debug mode - detailed error information will be shown")
    
    # Set default download path
    default_download_path = 'F:\\temp\\New folder'
    
    # Ask for download path once at the beginning
    download_path = input("Enter download path (leave empty for default directory): ").strip()
    download_path = download_path if download_path else default_download_path
    
    # Loop to download multiple videos
    while True:
        # Check if URL was provided as command line argument (only for the first run)
        if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
            video_url = sys.argv[1]
            print(f"Using URL from command line: {video_url}")
            # Clear command line args to avoid reusing them in the next iteration
            sys.argv = [sys.argv[0]] + [arg for arg in sys.argv[1:] if arg.startswith('--')]
        else:
            # Get YouTube URL from user
            video_url = input("Enter YouTube video URL: ").strip()
            
            # Provide a default URL if empty (for testing)
            if not video_url:
                video_url = "https://youtu.be/s208Qs94V0g?feature=shared"  # Rick Astley video
                print(f"Using default URL for testing: {video_url}")
        
        # Download the video
        download_youtube_video(video_url, download_path)
        
        # Ask if user wants to download another video
        continue_download = input("\nDo you want to download another video? (y/n): ").strip().lower()
        if continue_download != 'y' and continue_download != 'yes':
            print("Thank you for using YouTube Downloader!")
            break
        
        print("\n" + "-"*50 + "\n")