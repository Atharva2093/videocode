import yt_dlp
import os
import sys
import argparse

def download_youtube_video(url, output_path='.', format='mp4', quality='best'):
    """
    Download a YouTube video using yt-dlp
    
    Args:
        url (str): YouTube video URL
        output_path (str): Directory to save the video
        format (str): Video format (mp4, webm, etc.)
        quality (str): Video quality (best, worst, etc.)
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': f'{quality}[ext={format}]' if format else quality,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,
        }
        
        # For debugging
        if '--debug' in sys.argv:
            ydl_opts['verbose'] = True
        
        print(f"Downloading video from: {url}")
        print(f"Output directory: {os.path.abspath(output_path)}")
        print(f"Format: {format}, Quality: {quality}")
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            print(f"\nVideo title: {info.get('title')}")
            print(f"Duration: {format_duration(info.get('duration', 0))}")
            
            # Show available formats if in debug mode
            if '--debug' in sys.argv and 'formats' in info:
                print("\nAvailable formats:")
                for fmt in info['formats'][:10]:  # Show only first 10 formats
                    print(f"ID: {fmt.get('format_id')}, Resolution: {fmt.get('resolution')}, "
                          f"Extension: {fmt.get('ext')}, Size: {fmt.get('filesize_approx', 'unknown')}")
            
            # Download the video
            print("\nStarting download...")
            ydl.download([url])
            
            print("\nDownload completed successfully!")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Make sure the video is not private")
        print("3. Try a different video URL")
        print("4. For detailed error information, run with --debug flag")
        
        if '--debug' in sys.argv:
            import traceback
            print("\nDetailed error information:")
            traceback.print_exc()

def progress_hook(d):
    """
    Display download progress
    """
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'unknown')
        speed = d.get('_speed_str', 'unknown')
        eta = d.get('_eta_str', 'unknown')
        print(f"\rDownloading... {percent} at {speed}, ETA: {eta}", end='')
    
    elif d['status'] == 'finished':
        print(f"\nFinished downloading. Now converting...")    

def format_duration(seconds):
    """
    Format duration in seconds to HH:MM:SS
    """
    if not seconds:
        return "Unknown"
        
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def parse_arguments():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='Download YouTube videos using yt-dlp')
    parser.add_argument('url', nargs='?', help='YouTube video URL')
    parser.add_argument('-o', '--output', default='F:\\temp\\New folder', help='Output directory')
    parser.add_argument('-f', '--format', default='mp4', help='Video format (mp4, webm, etc.)')
    parser.add_argument('-q', '--quality', default='best', help='Video quality (best, worst, etc.)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Check for debug mode
    if args.debug:
        print("Running in debug mode - detailed information will be shown")
    
    # Store command line URL if provided
    cmd_url = args.url
    
    # Get output directory
    output_path = args.output
    if output_path == 'F:\\temp\\New folder' and not cmd_url:  # Only prompt if not provided via command line
        user_path = input("Enter download path (leave empty for default directory): ").strip()
        output_path = user_path if user_path else 'F:\\temp\\New folder'
    
    # Loop to download multiple videos
    while True:
        # Get video URL
        if cmd_url:
            video_url = cmd_url
            print(f"Using URL from command line: {video_url}")
            # Clear command line URL to avoid reusing it in the next iteration
            cmd_url = None
        else:
            # Get YouTube URL from user
            video_url = input("Enter YouTube video URL: ").strip()
            
            # Provide a default URL if empty (for testing)
            if not video_url:
                video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley video
                print(f"Using default URL for testing: {video_url}")
        
        # Download the video
        download_youtube_video(video_url, output_path, args.format, args.quality)
        
        # Ask if user wants to download another video
        continue_download = input("\nDo you want to download another video? (y/n): ").strip().lower()
        if continue_download != 'y' and continue_download != 'yes':
            print("Thank you for using YouTube Downloader!")
            break
        
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    main()