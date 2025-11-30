import yt_dlp
import os
import sys
import argparse

# Global flag for cancellation
cancel_download = False


def is_playlist_url(url):
    """Check if URL is a playlist"""
    return 'list=' in url or '/playlist?' in url


def download_youtube_video(url, output_path='.', format='mp4', quality='best', playlist_mode='all'):
    """
    Download a YouTube video or playlist using yt-dlp
    
    Args:
        url (str): YouTube video/playlist URL
        output_path (str): Directory to save the video
        format (str): Video format (mp4, webm, etc.)
        quality (str): Video quality (best, worst, etc.)
        playlist_mode (str): 'all' to download all, 'select' for interactive selection
    """
    global cancel_download
    cancel_download = False
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # Check if it's a playlist
        if is_playlist_url(url):
            download_playlist(url, output_path, format, quality, playlist_mode)
            return
        
        # Configure yt-dlp options for single video
        ydl_opts = {
            'format': f'{quality}[ext={format}]/{quality}' if format else quality,
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
            print_video_info(info)
            
            # Show available formats if in debug mode
            if '--debug' in sys.argv and 'formats' in info:
                print("\nAvailable formats:")
                for fmt in info['formats'][:10]:  # Show only first 10 formats
                    print(f"ID: {fmt.get('format_id')}, Resolution: {fmt.get('resolution')}, "
                          f"Extension: {fmt.get('ext')}, Size: {format_filesize(fmt.get('filesize_approx'))}")
            
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


def download_playlist(url, output_path, format, quality, mode):
    """
    Download a YouTube playlist
    
    Args:
        url (str): Playlist URL
        output_path (str): Directory to save videos
        format (str): Video format
        quality (str): Video quality
        mode (str): 'all' or 'select'
    """
    print(f"\n{'='*50}")
    print("PLAYLIST DETECTED")
    print(f"{'='*50}\n")
    
    # First, extract playlist info
    ydl_opts_extract = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts_extract) as ydl:
        playlist_info = ydl.extract_info(url, download=False)
    
    playlist_title = playlist_info.get('title', 'Unknown Playlist')
    entries = playlist_info.get('entries', [])
    
    print(f"Playlist: {playlist_title}")
    print(f"Total videos: {len(entries)}\n")
    
    # List all videos
    print("Videos in playlist:")
    print("-" * 50)
    for i, entry in enumerate(entries, 1):
        if entry:
            title = entry.get('title', f'Video {i}')
            print(f"{i:3}. {title[:60]}{'...' if len(title) > 60 else ''}")
    print("-" * 50)
    
    # Select videos based on mode
    if mode == 'select':
        selected_indices = interactive_select_videos(entries)
        if not selected_indices:
            print("No videos selected. Exiting.")
            return
        videos_to_download = [(i, entries[i-1]) for i in selected_indices if i <= len(entries)]
    else:  # mode == 'all'
        videos_to_download = [(i, entry) for i, entry in enumerate(entries, 1) if entry]
    
    print(f"\nDownloading {len(videos_to_download)} videos...")
    
    # Download selected videos
    successful = 0
    failed = 0
    
    for idx, (num, entry) in enumerate(videos_to_download, 1):
        if cancel_download:
            print("\nDownload cancelled by user.")
            break
        
        video_id = entry.get('id', entry.get('url', ''))
        video_url = f"https://www.youtube.com/watch?v={video_id}" if not video_id.startswith('http') else video_id
        title = entry.get('title', f'Video {num}')
        
        print(f"\n[{idx}/{len(videos_to_download)}] Downloading: {title}")
        
        ydl_opts = {
            'format': f'{quality}[ext={format}]/{quality}' if format else quality,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            successful += 1
            print(f" ✓ Completed")
        except Exception as e:
            failed += 1
            print(f" ✗ Failed: {str(e)[:50]}")
    
    # Summary
    print(f"\n{'='*50}")
    print("PLAYLIST DOWNLOAD SUMMARY")
    print(f"{'='*50}")
    print(f"Total: {len(videos_to_download)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")


def interactive_select_videos(entries):
    """
    Interactive video selection for playlists
    
    Returns:
        list: Selected video indices (1-based)
    """
    print("\nSelect videos to download:")
    print("  - Enter numbers separated by commas (e.g., 1,3,5)")
    print("  - Enter a range (e.g., 1-10)")
    print("  - Enter 'all' to download all")
    print("  - Enter 'q' to cancel\n")
    
    while True:
        selection = input("Your selection: ").strip().lower()
        
        if selection == 'q':
            return []
        
        if selection == 'all':
            return list(range(1, len(entries) + 1))
        
        try:
            indices = []
            parts = selection.replace(' ', '').split(',')
            
            for part in parts:
                if '-' in part:
                    start, end = part.split('-')
                    indices.extend(range(int(start), int(end) + 1))
                else:
                    indices.append(int(part))
            
            # Validate indices
            valid_indices = [i for i in indices if 1 <= i <= len(entries)]
            
            if not valid_indices:
                print("No valid video numbers. Please try again.")
                continue
            
            print(f"Selected {len(valid_indices)} videos.")
            return sorted(set(valid_indices))
            
        except ValueError:
            print("Invalid input. Please enter numbers, ranges, 'all', or 'q'.")


def print_video_info(info):
    """Print video metadata"""
    print(f"\n{'='*50}")
    print("VIDEO INFORMATION")
    print(f"{'='*50}")
    print(f"Title: {info.get('title', 'Unknown')}")
    print(f"Channel: {info.get('uploader', 'Unknown')}")
    print(f"Duration: {format_duration(info.get('duration', 0))}")
    print(f"Views: {format_views(info.get('view_count'))}")
    print(f"Upload Date: {info.get('upload_date', 'Unknown')}")
    
    # Estimate file size if available
    if 'filesize_approx' in info:
        print(f"Estimated Size: {format_filesize(info.get('filesize_approx'))}")
    elif 'formats' in info:
        # Try to get size from best format
        for fmt in reversed(info['formats']):
            size = fmt.get('filesize') or fmt.get('filesize_approx')
            if size:
                print(f"Estimated Size: ~{format_filesize(size)}")
                break
    
    print(f"{'='*50}\n")

def progress_hook(d):
    """
    Display download progress
    """
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'unknown')
        speed = d.get('_speed_str', 'unknown')
        eta = d.get('_eta_str', 'unknown')
        print(f"\rDownloading... {percent} at {speed}, ETA: {eta}        ", end='')
    
    elif d['status'] == 'finished':
        print(f"\nFinished downloading. Now processing...")


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


def format_views(views):
    """Format view count"""
    if not views:
        return "Unknown"
    if views >= 1000000000:
        return f"{views / 1000000000:.1f}B"
    if views >= 1000000:
        return f"{views / 1000000:.1f}M"
    if views >= 1000:
        return f"{views / 1000:.1f}K"
    return str(views)


def format_filesize(size):
    """Format filesize in bytes to human readable"""
    if not size:
        return "Unknown"
    if size >= 1073741824:
        return f"{size / 1073741824:.2f} GB"
    if size >= 1048576:
        return f"{size / 1048576:.2f} MB"
    if size >= 1024:
        return f"{size / 1024:.2f} KB"
    return f"{size} B"


def preview_video_info(url):
    """
    Preview video information without downloading
    """
    print(f"\nFetching video info for: {url}\n")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if is_playlist_url(url) or info.get('_type') == 'playlist':
                print(f"{'='*50}")
                print("PLAYLIST INFORMATION")
                print(f"{'='*50}")
                print(f"Title: {info.get('title', 'Unknown')}")
                print(f"Videos: {len(info.get('entries', []))}")
                print(f"{'='*50}\n")
            else:
                print_video_info(info)
                
                # Show available formats
                if 'formats' in info:
                    print("\nAvailable Formats:")
                    print("-" * 70)
                    print(f"{'ID':<10} {'Resolution':<15} {'Extension':<10} {'Size':<15}")
                    print("-" * 70)
                    
                    seen = set()
                    for fmt in info['formats']:
                        if fmt.get('vcodec') != 'none':
                            res = fmt.get('resolution', 'N/A')
                            if res in seen:
                                continue
                            seen.add(res)
                            
                            print(f"{fmt.get('format_id', 'N/A'):<10} "
                                  f"{res:<15} "
                                  f"{fmt.get('ext', 'N/A'):<10} "
                                  f"{format_filesize(fmt.get('filesize') or fmt.get('filesize_approx')):<15}")
                    print("-" * 70)
                    
    except Exception as e:
        print(f"Error fetching info: {str(e)}")

def parse_arguments():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Download YouTube videos using yt-dlp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://youtube.com/watch?v=VIDEO_ID"
  %(prog)s "https://youtube.com/playlist?list=PLAYLIST_ID" --playlist select
  %(prog)s -o ./downloads -f webm -q best "URL"
  %(prog)s --preview "URL"
        """
    )
    parser.add_argument('url', nargs='?', help='YouTube video or playlist URL')
    parser.add_argument('-o', '--output', default='F:\\temp\\New folder', help='Output directory')
    parser.add_argument('-f', '--format', default='mp4', help='Video format (mp4, webm, etc.)')
    parser.add_argument('-q', '--quality', default='best', help='Video quality (best, worst, etc.)')
    parser.add_argument('--playlist', choices=['all', 'select'], default='all',
                        help='Playlist mode: "all" downloads everything, "select" for interactive selection')
    parser.add_argument('--preview', action='store_true', help='Preview video info without downloading')
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
    
    # If preview mode
    if args.preview and cmd_url:
        preview_video_info(cmd_url)
        return
    
    # Interactive mode if no URL provided
    if not cmd_url:
        user_path = input("Enter download path (leave empty for default directory): ").strip()
        output_path = user_path if user_path else output_path
    
    # Loop to download multiple videos
    while True:
        # Get video URL
        if cmd_url:
            video_url = cmd_url
            print(f"Using URL from command line: {video_url}")
            cmd_url = None  # Clear to avoid reuse
        else:
            video_url = input("\nEnter YouTube video/playlist URL (or 'q' to quit): ").strip()
            
            if video_url.lower() == 'q':
                print("Thank you for using YouTube Downloader!")
                break
            
            if not video_url:
                video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                print(f"Using default URL for testing: {video_url}")
        
        # Check if user wants to preview
        if video_url.startswith('preview ') or video_url.startswith('info '):
            preview_video_info(video_url.split(' ', 1)[1])
            continue
        
        # Download the video/playlist
        download_youtube_video(video_url, output_path, args.format, args.quality, args.playlist)
        
        # If URL was from command line, exit after download
        if args.url:
            break
        
        print("\n" + "-"*50)


if __name__ == "__main__":
    main()