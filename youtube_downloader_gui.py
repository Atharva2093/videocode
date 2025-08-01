import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import time

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
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")
        
        # Default download path
        self.default_path = "F:\\temp\\New folder"
        
        # Create GUI elements
        self.create_widgets()
        
        # Check if required libraries are installed
        self.check_dependencies()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="YouTube Video Downloader", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # URL input
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        url_label = ttk.Label(url_frame, text="YouTube URL:")
        url_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.url_entry.focus()
        
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
        
        # Download button
        self.download_button = ttk.Button(main_frame, text="Download", command=self.start_download)
        self.download_button.pack(pady=(0, 20))
        
        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
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
    
    def browse_folder(self):
        folder_path = filedialog.askdirectory(initialdir=self.path_entry.get())
        if folder_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_path)
    
    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a YouTube URL")
            return
        
        # Add to download list
        item_id = self.download_list.insert("", tk.END, values=(url, "Queued"))
        
        # Start download in a separate thread
        download_thread = threading.Thread(
            target=self.download_video,
            args=(url, item_id),
            daemon=True
        )
        download_thread.start()
        
        # Clear URL entry for next video
        self.url_entry.delete(0, tk.END)
        self.url_entry.focus()
    
    def download_video(self, url, item_id):
        self.download_button.config(state="disabled")
        self.status_var.set("Downloading...")
        self.download_list.item(item_id, values=(url, "Downloading"))
        
        output_path = self.path_entry.get()
        if not output_path:
            output_path = self.default_path
        
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        try:
            if DOWNLOADER == 'yt-dlp':
                self.download_with_ytdlp(url, output_path, item_id)
            else:  # pytube
                self.download_with_pytube(url, output_path, item_id)
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            self.download_list.item(item_id, values=(url, "Failed"))
            messagebox.showerror("Download Error", str(e))
        finally:
            self.download_button.config(state="normal")
            self.progress_var.set(0)
    
    def download_with_ytdlp(self, url, output_path, item_id):
        format_option = self.format_var.get()
        quality_option = self.quality_var.get()
        
        # Configure format based on selection
        if format_option == "audio only":
            format_spec = "bestaudio/best"
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            format_spec = f'{quality_option}[ext={format_option}]' if format_option else quality_option
            postprocessors = []
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': format_spec,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: self.ytdlp_progress_hook(d, item_id)],
            'quiet': True,
            'no_warnings': False,
            'postprocessors': postprocessors,
        }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            self.download_list.item(item_id, values=(title, "Downloading"))
            ydl.download([url])
            self.download_list.item(item_id, values=(title, "Completed"))
            self.status_var.set(f"Downloaded: {title}")
    
    def ytdlp_progress_hook(self, d, item_id):
        if d['status'] == 'downloading':
            try:
                percent = float(d.get('_percent_str', '0%').replace('%', ''))
                self.progress_var.set(percent)
                self.download_list.item(item_id, values=(self.download_list.item(item_id)['values'][0], f"{percent:.1f}%"))
                self.root.update_idletasks()
            except:
                pass
        elif d['status'] == 'finished':
            self.progress_var.set(100)
            self.download_list.item(item_id, values=(self.download_list.item(item_id)['values'][0], "Processing"))
    
    def download_with_pytube(self, url, output_path, item_id):
        # Create YouTube object
        yt = YouTube(
            url,
            on_progress_callback=lambda stream, chunk, bytes_remaining: self.pytube_progress_callback(
                stream, chunk, bytes_remaining, item_id
            )
        )
        
        # Get video title
        title = yt.title
        self.download_list.item(item_id, values=(title, "Downloading"))
        
        # Select stream based on format and quality
        format_option = self.format_var.get()
        quality_option = self.quality_var.get()
        
        if format_option == "audio only":
            stream = yt.streams.filter(only_audio=True).first()
        else:
            # Try to get progressive stream first
            streams = yt.streams.filter(progressive=True, file_extension=format_option).order_by('resolution')
            
            if quality_option == "best":
                stream = streams.desc().first()
            elif quality_option == "worst":
                stream = streams.asc().first()
            else:  # medium
                stream = streams.desc().first()  # Default to best if medium not available
            
            # If no suitable stream found, try any available
            if not stream:
                stream = yt.streams.order_by('resolution').desc().first()
        
        if not stream:
            raise Exception("No suitable stream found for this video")
        
        # Download the video
        stream.download(output_path)
        self.download_list.item(item_id, values=(title, "Completed"))
        self.status_var.set(f"Downloaded: {title}")
        self.progress_var.set(100)
    
    def pytube_progress_callback(self, stream, chunk, bytes_remaining, item_id):
        filesize = stream.filesize
        bytes_downloaded = filesize - bytes_remaining
        percent = (bytes_downloaded / filesize) * 100
        self.progress_var.set(percent)
        self.download_list.item(item_id, values=(self.download_list.item(item_id)['values'][0], f"{percent:.1f}%"))
        self.root.update_idletasks()

def main():
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()