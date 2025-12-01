#!/usr/bin/env python3
"""
Cookie Export Utility for YouTube Downloader

This script exports YouTube cookies from your browser to a cookies.txt file
that yt-dlp can use to bypass "Sign in to confirm you're not a bot" errors.

Usage:
    python export_cookies.py [browser]

Supported browsers:
    chrome (default), edge, firefox, brave, opera, vivaldi, chromium

Prerequisites:
    1. Be logged into YouTube in your browser
    2. Close the browser (or use --no-check)
    3. Run this script
    
Alternative (if DPAPI fails on Windows):
    1. Install browser extension: "Get cookies.txt LOCALLY"
    2. Go to youtube.com while logged in
    3. Click extension → Export → Save as cookies.txt
    4. Move cookies.txt to backend/cookies.txt
"""

import subprocess
import sys
import os
import shutil

# Output path for cookies
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
COOKIES_FILE = os.path.join(BACKEND_DIR, "cookies.txt")

# Supported browsers
BROWSERS = ["chrome", "edge", "firefox", "brave", "opera", "vivaldi", "chromium", "safari"]


def detect_browser():
    """Try to detect which browser is installed"""
    # Check common browser paths on Windows
    browser_paths = {
        "chrome": [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        ],
        "edge": [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
        ],
        "firefox": [
            os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles"),
        ],
        "brave": [
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"),
        ],
    }
    
    for browser, paths in browser_paths.items():
        for path in paths:
            if os.path.exists(path):
                return browser
    
    return "chrome"  # Default fallback


def export_cookies(browser: str) -> bool:
    """Export cookies from the specified browser"""
    print(f"\n🔄 Exporting cookies from {browser}...")
    print(f"   Output: {COOKIES_FILE}\n")
    
    try:
        # Use yt-dlp to export cookies
        cmd = [
            "yt-dlp",
            "--cookies-from-browser", browser,
            "--cookies", COOKIES_FILE,
            "--skip-download",
            "--quiet",
            "https://www.youtube.com"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            error_msg = result.stderr
            if "DPAPI" in error_msg:
                print("❌ DPAPI decryption failed (Windows issue)")
                print("\n📋 ALTERNATIVE METHOD:")
                print("   1. Install browser extension: 'Get cookies.txt LOCALLY'")
                print("      Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc")
                print("   2. Go to youtube.com (make sure you're logged in)")
                print("   3. Click extension icon → Export → Netscape format")
                print(f"   4. Save file as: {COOKIES_FILE}")
                return False
            print(f"❌ Error: {error_msg}")
            return False
        
        if os.path.exists(COOKIES_FILE):
            size = os.path.getsize(COOKIES_FILE)
            print(f"✅ Cookies exported successfully!")
            print(f"   File size: {size} bytes")
            print(f"   Location: {COOKIES_FILE}")
            return True
        else:
            print("❌ Cookie file was not created")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout: Cookie export took too long")
        return False
    except FileNotFoundError:
        print("❌ yt-dlp not found. Install it with: pip install yt-dlp")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def verify_cookies():
    """Verify cookies work by testing a video"""
    print("\n🔍 Verifying cookies...")
    
    try:
        cmd = [
            "yt-dlp",
            "--cookies", COOKIES_FILE,
            "--skip-download",
            "--print", "title",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ Cookies verified! Test video: {result.stdout.strip()}")
            return True
        else:
            print(f"⚠️ Verification failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"⚠️ Verification error: {e}")
        return False


def show_manual_instructions():
    """Show instructions for manual cookie export"""
    print("\n" + "=" * 60)
    print("📋 MANUAL COOKIE EXPORT INSTRUCTIONS")
    print("=" * 60)
    print("""
If automatic export fails, use a browser extension:

1. Install "Get cookies.txt LOCALLY" extension:
   Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   Edge:   https://microsoftedge.microsoft.com/addons/detail/get-cookiestxt-locally/helcbpdpikgjadonpkckajgpoigpllnj
   Firefox: https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/

2. Go to https://www.youtube.com and LOG IN

3. Click the extension icon → "Export" or "Get cookies.txt"

4. Save the file as:
   """)
    print(f"   {COOKIES_FILE}")
    print("""
5. Restart the backend server

6. Test with:
   curl "http://127.0.0.1:8000/api/health"
   # Should show: "cookies_loaded": true
""")
    print("=" * 60)


def main():
    print("=" * 50)
    print("🍪 YouTube Cookie Export Utility")
    print("=" * 50)
    
    # Get browser from command line or auto-detect
    if len(sys.argv) > 1:
        browser = sys.argv[1].lower()
        if browser == "--manual" or browser == "-m":
            show_manual_instructions()
            return
        if browser not in BROWSERS:
            print(f"❌ Unknown browser: {browser}")
            print(f"   Supported: {', '.join(BROWSERS)}")
            print(f"   Or use: python export_cookies.py --manual")
            sys.exit(1)
    else:
        browser = detect_browser()
        print(f"🔍 Auto-detected browser: {browser}")
    
    # Check if yt-dlp is installed
    if not shutil.which("yt-dlp"):
        print("❌ yt-dlp is not installed!")
        print("   Install with: pip install yt-dlp")
        sys.exit(1)
    
    print(f"\n⚠️  Make sure you are LOGGED INTO YouTube in {browser}!")
    print("   (Close the browser if you get permission errors)\n")
    
    # Export cookies
    if export_cookies(browser):
        verify_cookies()
        print("\n" + "=" * 50)
        print("✅ Done! Restart the backend to use the new cookies.")
        print("=" * 50)
    else:
        show_manual_instructions()
        sys.exit(1)


if __name__ == "__main__":
    main()
