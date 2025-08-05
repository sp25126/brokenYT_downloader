import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from yt_dlp import YoutubeDL

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader - Dark Theme")
        self.root.geometry("850x650")
        self.root.configure(bg="#1e1e1e")

        self.video_list = []
        self.checkbox_vars = []
        self.progress_bars = []
        self.selected_path = tk.StringVar(value=os.getcwd())
        self.download_type = tk.StringVar(value="both")
        self.url = tk.StringVar()

        self.create_ui()

    def create_ui(self):
        # URL input
        tk.Label(self.root, text="YouTube URL:", bg="#1e1e1e", fg="white", font=("Arial", 12)).pack(pady=(10, 2))
        tk.Entry(self.root, textvariable=self.url, width=80, font=("Arial", 11)).pack(pady=2)

        tk.Button(self.root, text="Fetch Playlist", command=self.fetch_playlist, bg="#333", fg="white").pack(pady=8)

        # Scrollable video frame
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg="#1e1e1e")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.video_frame = tk.Frame(canvas, bg="#1e1e1e")

        self.video_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.video_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Download options
        options_frame = tk.Frame(self.root, bg="#1e1e1e")
        options_frame.pack()

        tk.Label(options_frame, text="Download Type:", bg="#1e1e1e", fg="white").grid(row=0, column=0, padx=5)
        tk.Radiobutton(options_frame, text="Video + Audio", variable=self.download_type, value="both", bg="#1e1e1e", fg="white", selectcolor="#333").grid(row=0, column=1)
        tk.Radiobutton(options_frame, text="Audio Only", variable=self.download_type, value="audio", bg="#1e1e1e", fg="white", selectcolor="#333").grid(row=0, column=2)

        tk.Button(options_frame, text="Choose Path", command=self.choose_path).grid(row=1, column=0, columnspan=2, pady=10)
        tk.Label(options_frame, textvariable=self.selected_path, fg="cyan", bg="#1e1e1e").grid(row=1, column=2, sticky="w")

        # Download and Cancel buttons
        tk.Button(self.root, text="Download Selected", command=self.download_selected, bg="#4caf50", fg="white").pack(pady=10)
        tk.Button(self.root, text="Cancel", command=self.root.quit, bg="#f44336", fg="white").pack()

    def choose_path(self):
        path = filedialog.askdirectory()
        if path:
            self.selected_path.set(path)

    def fetch_playlist(self):
        url = self.url.get()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a YouTube URL.")
            return

        self.clear_video_frame()
        self.video_list.clear()
        self.checkbox_vars.clear()
        self.progress_bars.clear()

        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': True
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                if 'entries' in info_dict:
                    for entry in info_dict['entries']:
                        self.add_video_checkbox(entry.get('title', 'Untitled'), f"https://www.youtube.com/watch?v={entry['id']}")
                else:
                    self.add_video_checkbox(info_dict.get('title', 'Untitled'), info_dict.get('webpage_url'))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch videos: {str(e)}")

    def clear_video_frame(self):
        for widget in self.video_frame.winfo_children():
            widget.destroy()

    def add_video_checkbox(self, title, url):
        var = tk.BooleanVar(value=True)
        self.checkbox_vars.append((var, title, url))

        frame = tk.Frame(self.video_frame, bg="#2a2a2a", padx=5, pady=5)
        frame.pack(fill=tk.X, pady=2)

        cb = tk.Checkbutton(frame, text=title, variable=var, bg="#2a2a2a", fg="white", wraplength=600, justify="left", anchor="w")
        cb.pack(side=tk.LEFT, fill=tk.X, expand=True)

        progress = ttk.Progressbar(frame, length=200)
        progress.pack(side=tk.RIGHT, padx=5)
        self.progress_bars.append(progress)

    def download_selected(self):
        for i, (var, title, url) in enumerate(self.checkbox_vars):
            if var.get():
                Thread(target=self.download_video, args=(url, self.progress_bars[i], title)).start()

    def download_video(self, url, progress_bar, title):
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                if total:
                    percent = int((downloaded / total) * 100)
                    progress_bar["value"] = percent
            elif d['status'] == 'finished':
                progress_bar["value"] = 100

        ydl_opts = {
            'outtmpl': os.path.join(self.selected_path.get(), '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'format': 'bestaudio/best' if self.download_type.get() == 'audio' else 'bestvideo+bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if self.download_type.get() == 'audio' else []
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"Error downloading {title}: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
