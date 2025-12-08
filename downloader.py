#!/usr/bin/env python3
"""
YouTube Video Downloader - Simple CLI
Fast, local-only YouTube downloader with maximum speed optimization

Usage:
    python downloader.py
"""

import os
import sys
from pathlib import Path

try:
    from simple_downloader import (
        get_mp4_formats,
        download_video,
        is_aria2c_available,
        sanitize_filename,
    )
    from exceptions import (
        InvalidURLError,
        NoMP4FormatsError,
        DRMProtectedError,
        VideoUnavailableError,
        NetworkError,
        InvalidPathError,
    )
except ImportError as e:
    print(f"ERROR: Missing required module: {e}")
    print("\nPlease install dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)


def print_header():
    """Print application header"""
    print("\n" + "=" * 70)
    print("  YOUTUBE VIDEO DOWNLOADER - Ultra-Fast CLI")
    print("=" * 70)
    
    # Show speed status
    if is_aria2c_available():
        print("  [SPEED MODE] aria2c detected - Maximum speed enabled!")
    else:
        print("  [STANDARD MODE] Install aria2c for 5-15x faster downloads")
    
    print("=" * 70 + "\n")


def get_user_input(prompt: str) -> str:
    """Get user input with proper encoding"""
    try:
        return input(prompt).strip()
    except (UnicodeDecodeError, UnicodeEncodeError):
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
        return input(prompt).strip()


def get_youtube_url() -> str:
    """
    Get and validate YouTube URL from user
    
    Returns:
        Valid YouTube URL
    """
    while True:
        print("Enter YouTube URL:")
        url = get_user_input("> ")
        
        if not url:
            print("[ERROR] No URL provided. Please try again.\n")
            continue
        
        # Basic validation
        if 'youtube.com' in url or 'youtu.be' in url:
            return url
        
        print("[ERROR] Invalid YouTube URL. Please enter a valid URL.\n")
        print("Supported formats:")
        print("  - https://youtube.com/watch?v=VIDEO_ID")
        print("  - https://youtu.be/VIDEO_ID")
        print("  - https://youtube.com/shorts/VIDEO_ID\n")


def display_formats(formats: list, title: str, duration: int):
    """
    Display video information and available formats
    
    Args:
        formats: List of format dictionaries
        title: Video title
        duration: Video duration in seconds
    """
    print(f"\n[VIDEO TITLE] {title}")
    
    if duration > 0:
        mins, secs = divmod(duration, 60)
        print(f"[DURATION] {mins}m {secs}s")
    
    print("\nAvailable MP4 qualities:")
    print("-" * 70)
    
    for idx, fmt in enumerate(formats, 1):
        height = fmt['height']
        format_id = fmt['format_id']
        filesize = fmt.get('filesize', 0)
        has_audio = fmt.get('has_audio', False)
        
        size_str = f"{filesize / (1024 * 1024):.1f} MB" if filesize > 0 else "Unknown size"
        audio_str = "[with audio]" if has_audio else "[video only]"
        
        print(f"  {idx}) {height}p {audio_str:15} (ID: {format_id:6}) - {size_str}")
    
    print(f"  {len(formats) + 1}) Best quality available")
    print("-" * 70)


def select_quality(formats: list) -> str:
    """
    Let user select video quality
    
    Args:
        formats: List of available formats
        
    Returns:
        Selected format ID or None for best
    """
    while True:
        choice = get_user_input("\nChoose quality number: ")
        
        if not choice.isdigit():
            print("[ERROR] Please enter a valid number")
            continue
        
        choice_num = int(choice)
        
        if choice_num == len(formats) + 1:
            print("[SELECTED] Best quality available")
            return None
        
        if 1 <= choice_num <= len(formats):
            selected = formats[choice_num - 1]
            print(f"[SELECTED] {selected['height']}p")
            return selected['format_id']
        
        print(f"[ERROR] Please enter a number between 1 and {len(formats) + 1}")


def get_download_folder() -> str:
    """
    Get download folder from user
    
    Returns:
        Valid download folder path
    """
    print("\nEnter download folder path:")
    print("(Leave empty to use current directory)")
    
    while True:
        folder = get_user_input("> ")
        
        # Use current directory if empty
        if not folder:
            folder = str(Path.cwd())
            print(f"[USING] Current directory: {folder}")
            return folder
        
        # Expand user home directory
        folder = os.path.expanduser(folder)
        
        # Try to create folder if it doesn't exist
        try:
            folder_path = Path(folder)
            
            # Check if parent exists (for validation)
            if not folder_path.parent.exists():
                print(f"[ERROR] Parent directory does not exist: {folder_path.parent}")
                print("Please enter a valid path:\n")
                continue
            
            # Create the folder
            folder_path.mkdir(parents=True, exist_ok=True)
            
            # Verify we can write to it
            test_file = folder_path / ".test_write"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception:
                print(f"[ERROR] Cannot write to folder: {folder}")
                print("Please enter a different path:\n")
                continue
            
            print(f"[USING] Download folder: {folder}")
            return str(folder_path)
            
        except Exception as e:
            print(f"[ERROR] Invalid folder path: {e}")
            print("Please enter a valid path:\n")


def main():
    """Main application flow"""
    try:
        # Show header
        print_header()
        
        # Step 1: Get YouTube URL
        url = get_youtube_url()
        
        # Step 2: Fetch video metadata
        print("\n[FETCHING] Getting video information...")
        
        try:
            title, duration, formats = get_mp4_formats(url)
        except InvalidURLError:
            print("\n[ERROR] Invalid YouTube URL")
            print("Please check the URL and try again.")
            return 1
        except NoMP4FormatsError:
            print("\n[ERROR] No MP4 formats available for this video")
            print("This video may not have compatible formats.")
            return 1
        except DRMProtectedError:
            print("\n[ERROR] Video is DRM-protected and cannot be downloaded")
            print("Try a different video.")
            return 1
        except VideoUnavailableError as e:
            print(f"\n[ERROR] {e}")
            return 1
        except NetworkError as e:
            print(f"\n[ERROR] Network issue: {e}")
            print("Please check your internet connection and try again.")
            return 1
        
        # Step 3: Display formats and select quality
        display_formats(formats, title, duration)
        format_id = select_quality(formats)
        
        # Step 4: Get download folder
        download_folder = get_download_folder()
        
        # Step 5: Download video
        print("\n" + "=" * 70)
        print("  STARTING DOWNLOAD")
        print("=" * 70)
        
        try:
            downloaded_file = download_video(url, download_folder, format_id)
            
            # Success message
            print("\n" + "=" * 70)
            print("  DOWNLOAD COMPLETE!")
            print("=" * 70)
            print(f"\n[SUCCESS] Video saved to:")
            print(f"  {downloaded_file}")
            
            # Show file size
            file_size = Path(downloaded_file).stat().st_size
            size_mb = file_size / (1024 * 1024)
            print(f"\n[FILE SIZE] {size_mb:.2f} MB")
            print("\n" + "=" * 70 + "\n")
            
            return 0
            
        except VideoUnavailableError as e:
            print(f"\n[ERROR] {e}")
            return 1
        except NetworkError as e:
            print(f"\n[ERROR] {e}")
            return 1
        except Exception as e:
            print(f"\n[ERROR] Download failed: {e}")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Download cancelled by user")
        print("Exiting...\n")
        return 1
    
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
