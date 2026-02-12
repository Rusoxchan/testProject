# 🎥 Professional Video Downloader

A robust, 3-layer architecture application for downloading videos using `yt-dlp`. Features a modern Tkinter GUI, a FastAPI backend for remote management, and a CLI for automation.

## ✨ Features
- **Format Selection**: Video+Audio (Merged), Video Only, Audio Only.
- **Quality Control**: Select from Best to 480p.
- **Dual Interface**:
  - Desktop GUI (Tkinter)
  - Web Dashboard (FastAPI + WebSockets)
- **Architecture**: Separates Directives (SOPs), Orchestration, and Execution for reliability.

## 🚀 Getting Started

### Prerequisites
1.  **Python 3.8+**
2.  **FFmpeg**: Required for merging video and audio.
    - *Windows*: `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
    - *Linux*: `sudo apt install ffmpeg`
    - *Mac*: `brew install ffmpeg`

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/Rusoxchan/testProject.git
    cd testProject
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 📖 Usage

### 1. Desktop GUI (Recommended)
Launch the modern desktop application:
```bash
python execution/download_video.py
```
*Note: It auto-detects URLs from your clipboard!*

### 2. Command Line Interface (CLI)
Download directly from your terminal:
```bash
python execution/download_video.py --url "https://youtu.be/EXAMPLE"
```

### 3. Web Server (Background Queue)
Start the backend server to manage a download queue:
```bash
uvicorn execution.server:app --reload
```
Open **http://127.0.0.1:8000** in your browser to view the dashboard.

## 📂 Project Structure
- `directives/`: Markdown SOPs defining *what* to do.
- `execution/`: Python scripts performing the *actual work*.
- `.tmp/downloads/`: Default output directory for downloaded media.

## 🛠️ Built With
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html)
