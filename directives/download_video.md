# Download Video via yt-dlp

## Goal
Download a video from a given URL using `yt-dlp` with advanced options for format and quality selection.

## Inputs
- **URL**: A valid video URL (YouTube, etc.)
- **Format** (GUI only): `Merged` (default), `Video Only`, `Audio Only`
- **Quality** (GUI only): `Best` (default), `1080p`, `720p`, `480p`

## Tools
- `execution/download_video.py` — Python script with Tkinter GUI

## Usage

### GUI Mode (default)
```bash
python execution/download_video.py
```
- Select Format (e.g. "Audio Only" for music)
- Select Quality (e.g. "720p" to save space)
- Paste URL -> Download

### CLI Mode (Compatibility)
```bash
python execution/download_video.py --url "<URL>"
```
*Note: CLI currently defaults to Best Quality + Merged Format.*

## yt-dlp Logic
- **Merged**: `bv*[vcodec^=avc1]+ba[ext=m4a]/b[ext=mp4]/b` (with height filters if quality selected) -> merged to mp4
- **Audio Only**: `ba[ext=m4a]/ba` -> m4a
- **Video Only**: `bv*[ext=mp4]/bv` -> mp4 (no sound)

## Output
- Files saved to `.tmp/downloads/`
- Pattern: `yt_<title>.<ext>`

## Dependencies
- `yt-dlp`
- `ffmpeg` (Required for Merged format)

## Edge Cases
- **Quality unavailable**: If requested 1080p but max is 720p, yt-dlp falls back to best available below limit.
- **Audio Only**: Quality selector is disabled.
