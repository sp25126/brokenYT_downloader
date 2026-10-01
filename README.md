# Whop Course Downloader

A 100% local, high-speed automated tool to bulk download any course you have access to on Whop in full 1080p HD, with exact titles and folder structure.

---

## Features
- **1-Click Bulk Downloading**: Downloads all courses and lessons in your account with a single command.
- **Full HD (1080p)**: Automatically merges the highest-quality video stream and audio tracks using `yt-dlp`.
- **Parallel Chunk Acceleration**: Downloads video fragments concurrently for fast downloads even on unstable connections.
- **Smart Resuming**: Automatically skips already downloaded files—safely interrupt and resume anytime.
- **Zero Browser Automation**: Direct internal API integration—no headless browsers, no Cloudflare blocks, and no Chrome Web Store fees.

---

## Prerequisites
1. **Python 3.8+**
2. **ffmpeg** installed and available in your system `PATH`
3. **yt-dlp**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Quick Start

### 1. Run the Downloader
```bash
python whop_course_downloader.py
```

### 2. Enter Session Cookie (First Time Only)
On the first run, the script prompts for your Whop session cookie:
1. Open [whop.com](https://whop.com) in your browser and log in.
2. Press `F12` to open Developer Tools, go to the **Network** tab, and refresh or click any course.
3. Select any request to `whop.com`, look under **Request Headers**, and copy the value of `cookie:`.
4. Paste it into the script prompt.

The cookie is stored locally in `cookies.txt` (which is excluded by `.gitignore`) and remembered automatically for future runs. Alternatively, set the environment variable:
```bash
export WHOP_COOKIE="your_cookie_here"   # Linux/macOS
$env:WHOP_COOKIE="your_cookie_here"     # Windows PowerShell
```

---

## Usage Modes

### Interactive Mode
```bash
python whop_course_downloader.py
```
Displays your complete course library and prompts you to select a course or download all.

### Download All Courses Automatically
```bash
python whop_course_downloader.py --all
```

### Download a Specific Course
```bash
python whop_course_downloader.py --course 1
```

### Custom Course Exclusion
Skip courses by title keywords (e.g. skip "yapping" or specific test courses):
```bash
python whop_course_downloader.py --all --skip yapping bonus
```

---

## Output Structure
Videos are organized into `downloads/` with sequential numbering and exact lesson titles:

```
downloads/
├── Creatives Mastery behind 100M$ Brand/
│   ├── 01_The First Shift Rewiring How You See Ads.mp4
│   └── 02_Visual Psychology of High-Converting Hooks.mp4
├── ELITE COPYWRITING Masterclass/
│   ├── 01_The Foundation Brand-Safe Direct Response.mp4
│   └── ...
└── ...
```

---

## Optional: Chrome Extension
If you prefer exporting manifests directly from your browser, a standalone unpacked Manifest V3 extension is also provided inside the `extension/` directory.

To use it:
1. Navigate to `chrome://extensions/`
2. Enable **Developer mode** (top-right).
3. Click **Load unpacked** and select the `extension/` folder.
