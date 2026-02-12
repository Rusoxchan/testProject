"""
core.py — Core download logic for yt-dlp.

Shared by:
- download_video.py (Tkinter GUI)
- server.py (FastAPI Backend)
"""

import sys
import subprocess
from pathlib import Path

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / ".tmp" / "downloads"

# ──────────────────────────────────────────────
# Logic
# ──────────────────────────────────────────────
def build_yt_dlp_args(url, format_mode, quality_mode, output_dir):
    """
    Constructs the yt-dlp command arguments based on user selection.
    
    format_mode: "merged", "video", "audio"
    quality_mode: "best", "1080p", "720p", "480p", "audio_best"
    """
    cmd = ["yt-dlp", "--newline", "--no-mtime"]
    
    # Base Output Template
    cmd += ["-o", str(output_dir / "yt_%(title).80B.%(ext)s")]

    if format_mode == "audio":
        # Audio Only
        cmd += ["-f", "ba[ext=m4a]/ba", "--extract-audio"]
    
    elif format_mode == "video":
        # Video Only (no audio)
        if quality_mode == "best":
            cmd += ["-f", "bv*[ext=mp4]/bv"]
        else:
            height = quality_mode.replace("p", "")
            cmd += ["-f", f"bv*[height<={height}][ext=mp4]/bv*[height<={height}]"]
    
    else:
        # Merged (Video + Audio) - Default
        # prioritizing avc1/mp4 for compatibility
        if quality_mode == "best":
            cmd += ["-f", "bv*[vcodec^=avc1]+ba[ext=m4a]/b[ext=mp4]/b"]
        else:
            height = quality_mode.replace("p", "")
            # Try to find video <= height
            cmd += ["-f", f"bv*[height<={height}][vcodec^=avc1]+ba[ext=m4a]/b[height<={height}][ext=mp4]/b[height<={height}]"]
        
        cmd += ["--merge-output-format", "mp4"]

    cmd.append(url)
    return cmd


def download_video(url, format_mode, quality_mode, on_output=None, on_done=None):
    """
    Run yt-dlp in a subprocess.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = build_yt_dlp_args(url, format_mode, quality_mode, OUTPUT_DIR)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        for line in proc.stdout:
            if on_output:
                on_output(line)
        proc.wait()
        if on_done:
            on_done(proc.returncode)
    except FileNotFoundError:
        msg = "ERROR: yt-dlp not found. Install it with: pip install yt-dlp"
        if on_output:
            on_output(msg + "\n")
        if on_done:
            on_done(-1)
    except Exception as exc:
        if on_output:
            on_output(f"ERROR: {exc}\n")
        if on_done:
            on_done(-1)
