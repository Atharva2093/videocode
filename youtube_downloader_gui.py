import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from concurrent.futures import ThreadPoolExecutor
import os
import sys
import time
import re
import io
import urllib.request

# Try to import PIL for thumbnail display
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Try to import yt-dlp (preferred) or fallback to pytube
try:
    import yt_dlp
    DOWNLOADER = 'yt-dlp'
except ImportError:
    try:
        from pytube import YouTube
        DOWNLOADER = 'pytube'
    except ImportError:
        DOWNLOADER = None


class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")
        
        # Default download path
        self.default_path = "F:\\temp\\New folder"
        
        # Threading control
        self.download_thread = None
        self.cancel_download = False
        self.is_downloading = False
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        # Video metadata cache
        self.current_video_info = None
        self.thumbnail_image = None
        
        # Playlist data
        self.playlist_videos = []
        self.playlist_checkboxes = {}
        
        # Create GUI elements
        self.create_widgets()
        
        # Check if required libraries are installed
        self.check_dependencies()
    
    def create_widgets(self):
        # Main frame with scrollbar
        self.canvas = tk.Canvas(self.root, bg="#f0f0f0")
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, padding="20 20 20 20")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        main_frame = self.scrollable_frame
        
        # Title
        title_label = ttk.Label(main_frame, text="YouTube Video Downloader", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # URL input frame
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        url_label = ttk.Label(url_frame, text="YouTube URL:")
        url_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.url_entry.focus()
        
        # Preview Info button
        self.preview_button = ttk.Button(url_frame, text="Preview Info", command=self.preview_video_info)
        self.preview_button.pack(side=tk.LEFT)
        
        # Video Preview Frame (initially hidden)
        self.preview_frame = ttk.LabelFrame(main_frame, text="Video Preview")
        self.preview_frame.pack(fill=tk.X, pady=(0, 10))
        self.preview_frame.pack_forget()  # Hide initially
        
        # Thumbnail and info container
        self.preview_content = ttk.Frame(self.preview_frame)
        self.preview_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Thumbnail label
        self.thumbnail_label = ttk.Label(self.preview_content)
        self.thumbnail_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Video info frame
        self.video_info_frame = ttk.Frame(self.preview_content)
        self.video_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.title_label_var = tk.StringVar(value="")
        self.channel_label_var = tk.StringVar(value="")
        self.duration_label_var = tk.StringVar(value="")
        self.views_label_var = tk.StringVar(value="")
        
        ttk.Label(self.video_info_frame, textvariable=self.title_label_var, font=("Arial", 10, "bold"), wraplength=400).pack(anchor="w")
        ttk.Label(self.video_info_frame, textvariable=self.channel_label_var).pack(anchor="w")
        ttk.Label(self.video_info_frame, textvariable=self.duration_label_var).pack(anchor="w")
        ttk.Label(self.video_info_frame, textvariable=self.views_label_var).pack(anchor="w")
        
        # Available formats frame
        self.formats_frame = ttk.LabelFrame(main_frame, text="Available Formats")
        self.formats_frame.pack(fill=tk.X, pady=(0, 10))
        self.formats_frame.pack_forget()  # Hide initially
        
        self.formats_tree = ttk.Treeview(self.formats_frame, columns=("format", "resolution", "ext", "size"), show="headings", height=5)
        self.formats_tree.heading("format", text="Format ID")
        self.formats_tree.heading("resolution", text="Resolution")
        self.formats_tree.heading("ext", text="Extension")
        self.formats_tree.heading("size", text="Size")
        self.formats_tree.column("format", width=80)
        self.formats_tree.column("resolution", width=100)
        self.formats_tree.column("ext", width=60)
        self.formats_tree.column("size", width=100)
        self.formats_tree.pack(fill=tk.X, padx=5, pady=5)
        
        # Playlist Frame (initially hidden)
        self.playlist_frame = ttk.LabelFrame(main_frame, text="Playlist Videos")
        self.playlist_frame.pack(fill=tk.BOTH, pady=(0, 10))
        self.playlist_frame.pack_forget()  # Hide initially
        
        # Playlist controls
        playlist_controls = ttk.Frame(self.playlist_frame)
        playlist_controls.pack(fill=tk.X, padx=5, pady=5)
        
        self.select_all_btn = ttk.Button(playlist_controls, text="Select All", command=self.select_all_playlist)
        self.select_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.deselect_all_btn = ttk.Button(playlist_controls, text="Deselect All", command=self.deselect_all_playlist)
        self.deselect_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.playlist_count_var = tk.StringVar(value="0 videos selected")
        ttk.Label(playlist_controls, textvariable=self.playlist_count_var).pack(side=tk.RIGHT, padx=5)
        
        # Playlist listbox with checkboxes
        playlist_list_frame = ttk.Frame(self.playlist_frame)
        playlist_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.playlist_canvas = tk.Canvas(playlist_list_frame, height=150)
        self.playlist_scrollbar = ttk.Scrollbar(playlist_list_frame, orient="vertical", command=self.playlist_canvas.yview)
        self.playlist_inner_frame = ttk.Frame(self.playlist_canvas)
        
        self.playlist_inner_frame.bind(
            "<Configure>",
            lambda e: self.playlist_canvas.configure(scrollregion=self.playlist_canvas.bbox("all"))
        )
        
        self.playlist_canvas.create_window((0, 0), window=self.playlist_inner_frame, anchor="nw")
        self.playlist_canvas.configure(yscrollcommand=self.playlist_scrollbar.set)
        
        self.playlist_canvas.pack(side="left", fill="both", expand=True)
        self.playlist_scrollbar.pack(side="right", fill="y")
        
        # Download path selection
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(0, 20))
        
        path_label = ttk.Label(path_frame, text="Save to:")
        path_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.path_entry = ttk.Entry(path_frame, width=40)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.path_entry.insert(0, self.default_path)
        
        browse_button = ttk.Button(path_frame, text="Browse", command=self.browse_folder)
        browse_button.pack(side=tk.LEFT)
        
        # Format options
        format_frame = ttk.Frame(main_frame)
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        format_label = ttk.Label(format_frame, text="Format:")
        format_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.format_var = tk.StringVar(value="mp4")
        format_options = ["mp4", "webm", "audio only"]
        format_dropdown = ttk.Combobox(format_frame, textvariable=self.format_var, values=format_options, width=10)
        format_dropdown.pack(side=tk.LEFT, padx=(0, 20))
        
        quality_label = ttk.Label(format_frame, text="Quality:")
        quality_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.quality_var = tk.StringVar(value="best")
        quality_options = ["best", "medium", "worst"]
        quality_dropdown = ttk.Combobox(format_frame, textvariable=self.quality_var, values=quality_options, width=10)
        quality_dropdown.pack(side=tk.LEFT)
        
        # Button frame for Download and Cancel
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(0, 20))
        
        self.download_button = ttk.Button(button_frame, text="Download", command=self.start_download)
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_current_download, state="disabled")
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        # Progress details
        self.progress_detail_var = tk.StringVar(value="")
        progress_detail_label = ttk.Label(main_frame, textvariable=self.progress_detail_var)
        progress_detail_label.pack(pady=(0, 5))
        
        # Progress details
        self.progress_detail_var = tk.StringVar(value="")
        progress_detail_label = ttk.Label(main_frame, textvariable=self.progress_detail_var)
        progress_detail_label.pack(pady=(0, 5))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=(0, 10))
        
        # Video list (for multiple downloads)
        list_frame = ttk.LabelFrame(main_frame, text="Download Queue")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.download_list = ttk.Treeview(list_frame, columns=("url", "status"), show="headings")
        self.download_list.heading("url", text="Video")
        self.download_list.heading("status", text="Status")
        self.download_list.column("url", width=400)
        self.download_list.column("status", width=100)
        self.download_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.download_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.download_list.configure(yscrollcommand=scrollbar.set)
    
    def is_playlist_url(self, url):
        """Check if URL is a playlist"""
        return 'list=' in url or '/playlist?' in url
    
    def format_duration(self, seconds):
        """Format duration in seconds to HH:MM:SS"""
        if not seconds:
            return "Unknown"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    
    def format_views(self, views):
        """Format view count"""
        if not views:
            return "Unknown views"
        if views >= 1000000000:
            return f"{views / 1000000000:.1f}B views"
        if views >= 1000000:
            return f"{views / 1000000:.1f}M views"
        if views >= 1000:
            return f"{views / 1000:.1f}K views"
        return f"{views} views"
    
    def format_filesize(self, size):
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
    
    def preview_video_info(self):
        """Fetch and display video metadata"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a YouTube URL")
            return
        
        if DOWNLOADER != 'yt-dlp':
            messagebox.showwarning("Feature Unavailable", "Video preview requires yt-dlp")
            return
        
        self.status_var.set("Fetching video info...")
        self.preview_button.config(state="disabled")
        
        # Run in background thread
        thread = threading.Thread(target=self._fetch_video_info, args=(url,), daemon=True)
        thread.start()
    
    def _fetch_video_info(self, url):
        """Background thread to fetch video info"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist' if self.is_playlist_url(url) else False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check if it's a playlist
                if info.get('_type') == 'playlist' or 'entries' in info:
                    self.root.after(0, lambda: self._display_playlist_info(info))
                else:
                    self.root.after(0, lambda: self._display_video_info(info))
                    
        except Exception as e:
            self.root.after(0, lambda: self._handle_preview_error(str(e)))
    
    def _display_video_info(self, info):
        """Display single video info in GUI"""
        self.current_video_info = info
        
        # Update labels
        self.title_label_var.set(f"Title: {info.get('title', 'Unknown')}")
        self.channel_label_var.set(f"Channel: {info.get('uploader', 'Unknown')}")
        self.duration_label_var.set(f"Duration: {self.format_duration(info.get('duration'))}")
        self.views_label_var.set(f"Views: {self.format_views(info.get('view_count'))}")
        
        # Show preview frame
        self.preview_frame.pack(fill=tk.X, pady=(0, 10), before=self.playlist_frame if self.playlist_frame.winfo_manager() else None)
        
        # Hide playlist frame
        self.playlist_frame.pack_forget()
        
        # Load thumbnail
        thumbnail_url = info.get('thumbnail')
        if thumbnail_url and HAS_PIL:
            thread = threading.Thread(target=self._load_thumbnail, args=(thumbnail_url,), daemon=True)
            thread.start()
        
        # Display available formats
        self._display_formats(info.get('formats', []))
        
        self.status_var.set("Video info loaded")
        self.preview_button.config(state="normal")
    
    def _display_playlist_info(self, info):
        """Display playlist info in GUI"""
        self.playlist_videos = []
        entries = info.get('entries', [])
        
        # Clear previous checkboxes
        for widget in self.playlist_inner_frame.winfo_children():
            widget.destroy()
        self.playlist_checkboxes.clear()
        
        # Create checkboxes for each video
        for i, entry in enumerate(entries):
            if entry:
                video_title = entry.get('title', f'Video {i+1}')
                video_url = entry.get('url') or entry.get('webpage_url') or f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                
                self.playlist_videos.append({
                    'title': video_title,
                    'url': video_url,
                    'id': entry.get('id', '')
                })
                
                var = tk.BooleanVar(value=True)
                cb = ttk.Checkbutton(
                    self.playlist_inner_frame, 
                    text=f"{i+1}. {video_title[:60]}{'...' if len(video_title) > 60 else ''}",
                    variable=var,
                    command=self._update_playlist_count
                )
                cb.pack(anchor="w", pady=2)
                self.playlist_checkboxes[i] = var
        
        # Update count
        self._update_playlist_count()
        
        # Hide preview frame, show playlist frame
        self.preview_frame.pack_forget()
        self.formats_frame.pack_forget()
        self.playlist_frame.pack(fill=tk.BOTH, pady=(0, 10))
        
        # Update title info
        self.title_label_var.set(f"Playlist: {info.get('title', 'Unknown Playlist')}")
        self.channel_label_var.set(f"Videos: {len(entries)}")
        
        self.status_var.set(f"Playlist loaded: {len(entries)} videos")
        self.preview_button.config(state="normal")
    
    def _update_playlist_count(self):
        """Update the selected video count"""
        count = sum(1 for var in self.playlist_checkboxes.values() if var.get())
        self.playlist_count_var.set(f"{count} videos selected")
    
    def select_all_playlist(self):
        """Select all videos in playlist"""
        for var in self.playlist_checkboxes.values():
            var.set(True)
        self._update_playlist_count()
    
    def deselect_all_playlist(self):
        """Deselect all videos in playlist"""
        for var in self.playlist_checkboxes.values():
            var.set(False)
        self._update_playlist_count()
    
    def _load_thumbnail(self, url):
        """Load thumbnail in background"""
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                image_data = response.read()
            
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((160, 90), Image.Resampling.LANCZOS)
            self.thumbnail_image = ImageTk.PhotoImage(image)
            
            self.root.after(0, lambda: self.thumbnail_label.config(image=self.thumbnail_image))
        except Exception as e:
            print(f"Failed to load thumbnail: {e}")
    
    def _display_formats(self, formats):
        """Display available formats in treeview"""
        # Clear existing items
        for item in self.formats_tree.get_children():
            self.formats_tree.delete(item)
        
        if not formats:
            self.formats_frame.pack_forget()
            return
        
        # Show formats frame
        self.formats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Filter and sort formats
        video_formats = []
        for fmt in formats:
            if fmt.get('vcodec') != 'none' and fmt.get('resolution') != 'audio only':
                video_formats.append(fmt)
        
        # Sort by resolution (descending)
        video_formats.sort(key=lambda x: x.get('height') or 0, reverse=True)
        
        # Display top formats
        seen_resolutions = set()
        for fmt in video_formats[:15]:
            resolution = fmt.get('resolution', 'N/A')
            if resolution in seen_resolutions:
                continue
            seen_resolutions.add(resolution)
            
            self.formats_tree.insert("", "end", values=(
                fmt.get('format_id', 'N/A'),
                resolution,
                fmt.get('ext', 'N/A'),
                self.format_filesize(fmt.get('filesize') or fmt.get('filesize_approx'))
            ))
    
    def _handle_preview_error(self, error):
        """Handle preview error"""
        self.status_var.set("Error fetching video info")
        self.preview_button.config(state="normal")
        messagebox.showerror("Preview Error", f"Could not fetch video info:\n{error}")
    
    def check_dependencies(self):
        if DOWNLOADER is None:
            messagebox.showwarning(
                "Missing Dependencies",
                "Neither yt-dlp nor pytube is installed. Please install one of them:\n\n"
                "pip install yt-dlp\n"
                "or\n"
                "pip install pytube"
            )
            self.status_var.set("Please install required libraries")
            self.download_button.config(state="disabled")
        else:
            self.status_var.set(f"Using {DOWNLOADER} library")
            if not HAS_PIL:
                self.status_var.set(f"Using {DOWNLOADER} (Install Pillow for thumbnails)")
    
    def browse_folder(self):
        folder_path = filedialog.askdirectory(initialdir=self.path_entry.get())
        if folder_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_path)
    
    def cancel_current_download(self):
        """Cancel the current download"""
        if self.is_downloading:
            self.cancel_download = True
            self.status_var.set("Cancelling download...")
            self.cancel_button.config(state="disabled")
    
    def lock_ui(self, lock=True):
        """Lock or unlock UI during download"""
        state = "disabled" if lock else "normal"
        self.download_button.config(state=state)
        self.preview_button.config(state=state)
        self.url_entry.config(state=state)
        self.path_entry.config(state=state)
        self.cancel_button.config(state="normal" if lock else "disabled")
    
    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a YouTube URL")
            return
        
        # Check if playlist with selected videos
        if self.playlist_videos and self.playlist_checkboxes:
            selected_videos = [
                self.playlist_videos[i] 
                for i, var in self.playlist_checkboxes.items() 
                if var.get()
            ]
            if selected_videos:
                self._start_playlist_download(selected_videos)
                return
        
        # Single video download
        item_id = self.download_list.insert("", tk.END, values=(url, "Queued"))
        
        # Reset cancel flag
        self.cancel_download = False
        self.is_downloading = True
        
        # Lock UI
        self.lock_ui(True)
        
        # Start download in a separate thread
        self.download_thread = threading.Thread(
            target=self._download_worker,
            args=(url, item_id),
            daemon=True
        )
        self.download_thread.start()
        
        # Clear URL entry for next video
        self.url_entry.delete(0, tk.END)
    
    def _start_playlist_download(self, videos):
        """Start downloading selected playlist videos"""
        self.cancel_download = False
        self.is_downloading = True
        self.lock_ui(True)
        
        # Add all videos to queue
        item_ids = []
        for video in videos:
            item_id = self.download_list.insert("", tk.END, values=(video['title'], "Queued"))
            item_ids.append((video, item_id))
        
        # Start download thread
        self.download_thread = threading.Thread(
            target=self._playlist_download_worker,
            args=(item_ids,),
            daemon=True
        )
        self.download_thread.start()
    
    def _playlist_download_worker(self, video_items):
        """Worker thread for playlist downloads"""
        total = len(video_items)
        for i, (video, item_id) in enumerate(video_items):
            if self.cancel_download:
                self.root.after(0, lambda vid=video, iid=item_id: self.download_list.item(iid, values=(vid['title'], "Cancelled")))
                continue
            
            self.root.after(0, lambda idx=i, tot=total: self.progress_detail_var.set(f"Downloading {idx+1}/{tot}"))
            
            url = video['url']
            if not url.startswith('http'):
                url = f"https://www.youtube.com/watch?v={video['id']}"
            
            self._download_single_video(url, item_id)
        
        self.root.after(0, self._download_complete)
    
    def _download_worker(self, url, item_id):
        """Worker thread for single video download"""
        self._download_single_video(url, item_id)
        self.root.after(0, self._download_complete)
    
    def _download_single_video(self, url, item_id):
        """Download a single video (runs in worker thread)"""
        try:
            self.root.after(0, lambda: self.download_list.item(item_id, values=(self.download_list.item(item_id)['values'][0], "Downloading")))
            
            output_path = self.path_entry.get() or self.default_path
            os.makedirs(output_path, exist_ok=True)
            
            if DOWNLOADER == 'yt-dlp':
                self._download_with_ytdlp_threaded(url, output_path, item_id)
            else:
                self._download_with_pytube_threaded(url, output_path, item_id)
                
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._handle_download_error(item_id, error_msg))
    
    def _download_complete(self):
        """Called when download completes"""
        self.is_downloading = False
        self.cancel_download = False
        self.lock_ui(False)
        self.progress_var.set(0)
        self.progress_detail_var.set("")
        
        if self.cancel_download:
            self.status_var.set("Download cancelled")
        else:
            self.status_var.set("Download complete")
    
    def _handle_download_error(self, item_id, error):
        """Handle download error in main thread"""
        self.download_list.item(item_id, values=(self.download_list.item(item_id)['values'][0], "Failed"))
        self.status_var.set(f"Error: {error[:50]}...")
    
    def _download_with_ytdlp_threaded(self, url, output_path, item_id):
        """Download with yt-dlp (thread-safe)"""
        format_option = self.format_var.get()
        quality_option = self.quality_var.get()
        
        if format_option == "audio only":
            format_spec = "bestaudio/best"
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            format_spec = f'{quality_option}[ext={format_option}]/{quality_option}' if format_option else quality_option
            postprocessors = []
        
        def progress_hook(d):
            if self.cancel_download:
                raise Exception("Download cancelled by user")
            
            if d['status'] == 'downloading':
                try:
                    percent_str = d.get('_percent_str', '0%').replace('%', '').strip()
                    percent = float(percent_str)
                    speed = d.get('_speed_str', 'N/A')
                    eta = d.get('_eta_str', 'N/A')
                    
                    self.root.after(0, lambda p=percent: self.progress_var.set(p))
                    self.root.after(0, lambda s=speed, e=eta: self.progress_detail_var.set(f"Speed: {s} | ETA: {e}"))
                    self.root.after(0, lambda p=percent, iid=item_id: self.download_list.item(iid, values=(self.download_list.item(iid)['values'][0], f"{p:.1f}%")))
                except:
                    pass
            elif d['status'] == 'finished':
                self.root.after(0, lambda: self.progress_var.set(100))
                self.root.after(0, lambda iid=item_id: self.download_list.item(iid, values=(self.download_list.item(iid)['values'][0], "Processing")))
        
        ydl_opts = {
            'format': format_spec,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'postprocessors': postprocessors,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            self.root.after(0, lambda t=title, iid=item_id: self.download_list.item(iid, values=(t, "Downloading")))
            
            if not self.cancel_download:
                ydl.download([url])
                self.root.after(0, lambda t=title, iid=item_id: self.download_list.item(iid, values=(t, "Completed")))
                self.root.after(0, lambda t=title: self.status_var.set(f"Downloaded: {t}"))
    
    def _download_with_pytube_threaded(self, url, output_path, item_id):
        """Download with pytube (thread-safe)"""
        def progress_callback(stream, chunk, bytes_remaining):
            if self.cancel_download:
                raise Exception("Download cancelled by user")
            
            filesize = stream.filesize
            bytes_downloaded = filesize - bytes_remaining
            percent = (bytes_downloaded / filesize) * 100
            
            self.root.after(0, lambda p=percent: self.progress_var.set(p))
            self.root.after(0, lambda p=percent, iid=item_id: self.download_list.item(iid, values=(self.download_list.item(iid)['values'][0], f"{p:.1f}%")))
        
        yt = YouTube(url, on_progress_callback=progress_callback)
        title = yt.title
        self.root.after(0, lambda t=title, iid=item_id: self.download_list.item(iid, values=(t, "Downloading")))
        
        format_option = self.format_var.get()
        quality_option = self.quality_var.get()
        
        if format_option == "audio only":
            stream = yt.streams.filter(only_audio=True).first()
        else:
            streams = yt.streams.filter(progressive=True, file_extension=format_option).order_by('resolution')
            if quality_option == "best":
                stream = streams.desc().first()
            elif quality_option == "worst":
                stream = streams.asc().first()
            else:
                stream = streams.desc().first()
            
            if not stream:
                stream = yt.streams.order_by('resolution').desc().first()
        
        if not stream:
            raise Exception("No suitable stream found")
        
        if not self.cancel_download:
            stream.download(output_path)
            self.root.after(0, lambda t=title, iid=item_id: self.download_list.item(iid, values=(t, "Completed")))
            self.root.after(0, lambda t=title: self.status_var.set(f"Downloaded: {t}"))

def main():
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()