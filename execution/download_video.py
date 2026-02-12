"""
download_video.py — Download videos using yt-dlp with a Professional GUI v2.

Features:
- Format Selection: Video+Audio (Merged), Video Only, Audio Only
- Quality Selection: Best, 1080p, 720p, 480p, Best Audio

Usage:
    GUI mode:  python execution/download_video.py
    CLI mode:  python execution/download_video.py --url "..."

Output:
    .tmp/downloads/yt_<title>.<ext>
"""

import argparse
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

# Import shared logic
try:
    from core import download_video, OUTPUT_DIR
except ImportError:
    # Handle running directly from execution/ folder or root
    sys.path.append(str(Path(__file__).parent))
    from core import download_video, OUTPUT_DIR


# ──────────────────────────────────────────────
# Tkinter GUI
# ──────────────────────────────────────────────
class DownloadApp:
    """A modern-looking Tkinter window for downloading videos (v2)."""

    BG = "#1e1e2e"
    BG_SECONDARY = "#282840"
    FG = "#cdd6f4"
    ACCENT = "#89b4fa"
    ACCENT_HOVER = "#74c7ec"
    SUCCESS = "#a6e3a1"
    ERROR = "#f38ba8"
    BORDER = "#45475a"
    FONT = ("Segoe UI", 10)
    FONT_BOLD = ("Segoe UI", 10, "bold")
    FONT_MONO = ("Cascadia Code", 9)
    FONT_TITLE = ("Segoe UI", 16, "bold")

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("YT-DLP Downloader Pro")
        self.root.geometry("750x600")
        self.root.configure(bg=self.BG)
        
        # Configure layout weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1) # Log area expands

        self._downloading = False
        self._build_ui()
        self.root.bind("<FocusIn>", self._check_clipboard_auto)

    def _check_clipboard_auto(self, event):
        """Auto-fill URL from clipboard if valid and different."""
        # Simple check: Only on root window focus or manual paste action
        # Note: <FocusIn> triggers for all widgets, so filter by root if possible
        # or just check periodically. For UX, let's keep it simple:
        # If clipboard has YouTube link & current input is empty, fill it.
        try:
            if event and event.widget != self.root:
                return  # Avoid spamming on every widget focus
            
            text = self.root.clipboard_get()
            if "youtube.com" in text or "youtu.be" in text:
                current = self.url_var.get()
                if not current or (text != current and "youtube" not in current):
                    self.url_var.set(text)
                    self.status_var.set("URL pasted from clipboard")
                    # Visual pulse (optional/simple bg flash via after)
        except:
            pass


    # ── UI Construction ──────────────────────
    def _build_ui(self):
        # 1. Title bar
        title_frame = tk.Frame(self.root, bg=self.BG)
        title_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 15))
        
        tk.Label(
            title_frame, text="⬇  Video Downloader Pro", font=self.FONT_TITLE,
            bg=self.BG, fg=self.ACCENT,
        ).pack(anchor="w")
        tk.Label(
            title_frame,
            text="High-performance media downloader powered by yt-dlp & ffmpeg.",
            font=("Segoe UI", 9), bg=self.BG, fg="#a6adc8",
        ).pack(anchor="w", pady=(2, 0))

        # 2. Input Area
        input_frame = tk.Frame(self.root, bg=self.BG)
        input_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        
        tk.Label(input_frame, text="Video URL", font=self.FONT_BOLD, bg=self.BG, fg=self.FG).pack(anchor="w", pady=(0, 5))
        
        # Custom styled entry
        url_container = tk.Frame(input_frame, bg=self.BORDER, bd=0)
        url_container.pack(fill="x")
        inner_url = tk.Frame(url_container, bg=self.BG_SECONDARY, bd=0)
        inner_url.pack(fill="x", padx=1, pady=1)
        
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(
            inner_url, textvariable=self.url_var, font=("Segoe UI", 11),
            bg=self.BG_SECONDARY, fg=self.FG,
            insertbackground=self.ACCENT, relief="flat", bd=10
        )
        self.url_entry.pack(fill="x")
        self.url_entry.bind("<Return>", lambda e: self._on_download())

        # 3. Settings Area (Format & Quality)
        settings_frame = tk.Frame(self.root, bg=self.BG)
        settings_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(5, 15))
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)

        # Format Selector
        fmt_frame = tk.Frame(settings_frame, bg=self.BG)
        fmt_frame.grid(row=0, column=0, sticky="nesw", padx=(0, 10))
        
        tk.Label(fmt_frame, text="Format", font=self.FONT_BOLD, bg=self.BG, fg="#bac2de").pack(anchor="w", pady=(0, 5))
        
        self.format_var = tk.StringVar(value="merged")
        self.format_combo = ttk.Combobox(
            fmt_frame, textvariable=self.format_var, state="readonly", font=self.FONT,
            values=["Merged (Video+Audio)", "Video Only", "Audio Only"],
        )
        self.format_combo.pack(fill="x", ipady=4)
        self.format_combo.bind("<<ComboboxSelected>>", self._on_format_change)

        # Quality Selector
        qual_frame = tk.Frame(settings_frame, bg=self.BG)
        qual_frame.grid(row=0, column=1, sticky="nesw", padx=(10, 0))
        
        tk.Label(qual_frame, text="Quality / Max Resolution", font=self.FONT_BOLD, bg=self.BG, fg="#bac2de").pack(anchor="w", pady=(0, 5))
        
        self.quality_var = tk.StringVar(value="Best Available")
        self.quality_combo = ttk.Combobox(
            qual_frame, textvariable=self.quality_var, state="readonly", font=self.FONT,
            values=["Best Available", "1080p", "720p", "480p"],
        )
        self.quality_combo.pack(fill="x", ipady=4)

        # 4. Action Buttons & Status
        action_frame = tk.Frame(self.root, bg=self.BG)
        action_frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(5, 10))

        self.download_btn = tk.Button(
            action_frame, text="⬇  Download Media", font=("Segoe UI", 11, "bold"),
            bg=self.ACCENT, fg="#1e1e2e", activebackground=self.ACCENT_HOVER,
            activeforeground="#1e1e2e", relief="flat", cursor="hand2",
            bd=0, padx=25, pady=10, command=self._on_download,
        )
        self.download_btn.pack(side="left")

        self.clear_btn = tk.Button(
            action_frame, text="Clear Log", font=("Segoe UI", 10),
            bg=self.BG_SECONDARY, fg=self.FG, activebackground=self.BORDER,
            activeforeground=self.FG, relief="flat", cursor="hand2",
            bd=0, padx=15, pady=10, command=self._on_clear,
        )
        self.clear_btn.pack(side="left", padx=(10, 0))

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(
            action_frame, textvariable=self.status_var, font=("Segoe UI", 10),
            bg=self.BG, fg="#6c7086", anchor="w"
        )
        self.status_label.pack(side="left", padx=(20, 0))

        # 5. Log Output
        log_frame = tk.Frame(self.root, bg=self.BORDER)
        log_frame.grid(row=4, column=0, sticky="nesw", padx=24, pady=(0, 24))
        
        inner_log = tk.Frame(log_frame, bg=self.BG_SECONDARY, bd=0)
        inner_log.pack(fill="both", expand=True, padx=1, pady=1)

        self.log_text = scrolledtext.ScrolledText(
            inner_log, font=self.FONT_MONO, wrap="word",
            bg=self.BG_SECONDARY, fg=self.FG,
            insertbackground=self.FG, relief="flat",
            bd=10, state="disabled",
        )
        self.log_text.pack(fill="both", expand=True)

        self.log_text.tag_configure("error", foreground=self.ERROR)
        self.log_text.tag_configure("success", foreground=self.SUCCESS)
        self.log_text.tag_configure("info", foreground=self.ACCENT)

    # ── Logic & Event Handlers ────────────────
    def _on_format_change(self, event):
        fmt = self.format_combo.get()
        if "Audio" in fmt and "Video" not in fmt:
            self.quality_combo.set("Best Available")
            self.quality_combo.configure(state="disabled")
        else:
            self.quality_combo.configure(state="readonly")

    def _on_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please paste a video URL first.")
            return

        if self._downloading:
            return

        # Map UI selection to internal codes
        fmt_map = {
            "Merged (Video+Audio)": "merged",
            "Video Only": "video",
            "Audio Only": "audio"
        }
        qual_map = {
            "Best Available": "best",
            "1080p": "1080p",
            "720p": "720p",
            "480p": "480p"
        }

        fmt_mode = fmt_map.get(self.format_combo.get(), "merged")
        qual_mode = qual_map.get(self.quality_combo.get(), "best")

        self._downloading = True
        self.download_btn.configure(state="disabled", bg=self.BORDER, cursor="wait")
        self.status_var.set("Starting download process…")
        
        self._log_clear()
        self._log(f"--- Started Download ---\n", "info")
        self._log(f"URL: {url}\n")
        self._log(f"Format: {fmt_mode} | Quality: {qual_mode}\n")
        self._log(f"Output: {OUTPUT_DIR}\n\n")

        thread = threading.Thread(
            target=download_video,
            args=(url, fmt_mode, qual_mode, self._on_output_line, self._on_finished),
            daemon=True,
        )
        thread.start()

    def _on_clear(self):
        self._log_clear()
        self.status_var.set("Ready")

    def _on_output_line(self, line: str):
        self.root.after(0, self._log, line)

    def _on_finished(self, returncode: int):
        def _finish():
            self._downloading = False
            self.download_btn.configure(state="normal", bg=self.ACCENT, cursor="hand2")
            if returncode == 0:
                self.status_var.set("✓ Done")
                self.status_label.configure(fg=self.SUCCESS)
                self._log("\n✓ Process completed successfully.\n", "success")
            else:
                self.status_var.set("✗ Failed")
                self.status_label.configure(fg=self.ERROR)
                self._log(f"\n✗ Process failed (code {returncode}).\n", "error")
        self.root.after(0, _finish)

    def _log(self, text: str, tag: str = None):
        self.log_text.configure(state="normal")
        if tag:
            self.log_text.insert("end", text, tag)
        else:
            self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _log_clear(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.status_label.configure(fg="#6c7086")


def main():
    # Basic CLI support for testing
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Usage: python download_video.py [--url <url>]")
            return
        if sys.argv[1] == "--url" and len(sys.argv) > 2:
            url = sys.argv[2]
            print(f"CLI Download: {url}")
            download_video(url, "merged", "best", lambda x: print(x, end=""), lambda r: print(f"Done: {r}"))
            return

    root = tk.Tk()
    # Attempt to improve DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    DownloadApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
