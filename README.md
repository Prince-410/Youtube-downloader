# 🎬 YouTube Downloader

A modern, feature-rich desktop application for downloading YouTube videos and playlists with an intuitive graphical user interface. Built with Python and powered by `yt-dlp`, this tool provides seamless video downloading with customizable quality settings, playlist management, and real-time progress tracking.

## ✨ Features

- **Single Video & Playlist Downloads** - Download individual videos or entire playlists with ease
- **Quality Selection** - Choose from multiple video quality presets and audio bitrates
- **Smart Playlist Management** - Selective downloading with per-video checkboxes
- **Real-time Progress Tracking** - Live progress bars and download speed indicators
- **Pause & Resume** - Pause downloads and resume them later without losing progress
- **Download History** - Track all your past downloads with detailed metadata
- **Customizable Settings** - Configure download location, filename format, video/audio quality, and theme
- **Theme Support** - Switch between Light, Dark, and System-default themes
- **Metadata Preview** - View video thumbnails, duration, uploader info before downloading
- **Duplicate Detection** - Prevents re-downloading the same content
- **Format Support** - Automatic format handling for videos and audio extraction

## 🖼️ Interface Preview

The application features a modern, responsive GUI with:

- **Download Page** - Main interface for URL input, metadata preview, and quality settings
- **History Page** - View all downloaded videos with search and filter capabilities
- **Settings Page** - Configure preferences, theme, and download options
- **Sidebar Navigation** - Easy switching between different sections

## 📋 Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux

## 🚀 Installation

### Option 1: Quick Start with pip

1. Clone or download the project:

```bash
git clone https://github.com/Prince-410/Youtube-downloader.git
cd "Youtube downloader"
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python app.py
```

### Option 2: Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## 📦 Dependencies

| Package         | Version   | Purpose                         |
| --------------- | --------- | ------------------------------- |
| `yt-dlp`        | ≥2026.7.4 | Core YouTube downloading engine |
| `customtkinter` | ≥6.0.0    | Modern GUI framework            |
| `Pillow`        | ≥11.1.0   | Image processing for thumbnails |
| `requests`      | ≥2.32.3   | HTTP requests for metadata      |

## 💡 Usage Guide

### Downloading a Single Video

1. Launch the application: `python app.py`
2. Go to the **Download** tab
3. Paste a YouTube video URL in the input field
4. Click **Fetch Video Info** to preview metadata
5. Select your preferred video and audio quality
6. Choose the download location (if needed)
7. Click **Download** to start

### Downloading a Playlist

1. Paste a YouTube playlist URL in the input field
2. Click **Fetch Video Info**
3. Browse the playlist and select which videos to download (toggle checkboxes)
4. Choose quality settings
5. Click **Download** to begin batch downloading
6. Monitor progress in real-time

### Viewing Download History

1. Click the **History** tab
2. Browse all previously downloaded videos
3. View detailed information about each download

### Configuring Settings

1. Click the **Settings** tab
2. Adjust the following options:
   - **Download Location** - Where files are saved
   - **Video Quality** - Select from available quality presets
   - **Audio Quality** - Choose audio bitrate (320kbps, 256kbps, etc.)
   - **Filename Format** - Customize the output filename pattern
   - **Theme Mode** - Light, Dark, or System default
3. Changes are saved automatically

## 📂 Project Structure

```
YouTube downloader/
├── app.py                    # Application entry point
├── config.json               # Default configuration settings
├── requirements.txt          # Python package dependencies
├── README.md                 # This file
│
├── downloader/               # Core downloading module
│   ├── __init__.py
│   ├── downloader.py         # Main YoutubeDownloader class
│   ├── playlist.py           # Playlist extraction & management
│   └── progress.py           # Download progress tracking
│
├── gui/                      # User interface module
│   ├── __init__.py
│   ├── main_window.py        # Main application window
│   ├── download_page.py      # Download interface
│   ├── history_page.py       # Download history viewer
│   └── settings_page.py      # Configuration page
│
├── utils/                    # Utility functions
│   ├── __init__.py
│   ├── config.py             # Configuration management
│   ├── helpers.py            # Helper functions (formatting, thumbnails)
│   └── validators.py         # Input validation
│
├── assets/                   # Icons and media files
├── downloads/                # Default download directory
```

## ⚙️ Configuration

The application uses `config.json` for persistent settings:

```json
{
  "download_location": "D:\\Youtube downloader\\downloads",
  "preferred_video_quality": "Highest Available",
  "preferred_audio_quality": "320kbps",
  "filename_format": "%(title)s.%(ext)s",
  "theme_mode": "System"
}
```

### Configuration Options

- **download_location** - Directory where videos are saved
- **preferred_video_quality** - Default video quality (affects bandwidth and file size)
- **preferred_audio_quality** - Audio bitrate for extracted audio
- **filename_format** - Output filename template using yt-dlp variables:
  - `%(title)s` - Video title
  - `%(ext)s` - File extension
  - `%(uploader)s` - Channel name
  - `%(upload_date)s` - Upload date
- **theme_mode** - Application appearance (System, Light, Dark)

## 🎮 Keyboard Shortcuts

| Action          | Shortcut |
| --------------- | -------- |
| Toggle Download | Space    |
| Clear URL       | Ctrl+L   |
| Open Settings   | Ctrl+,   |
| Exit            | Ctrl+Q   |

## 🔧 Advanced Features

### Pause and Resume

- Click **Pause** during download to temporarily stop
- Click **Resume** to continue from where you left off
- Progress is preserved (files are not re-downloaded)

### Duplicate Detection

The application automatically detects if a video is already in your download history and prevents redundant downloads.

### Metadata Fetching

Before downloading, the app fetches:

- Video title and duration
- Uploader/channel name
- Thumbnail image
- Available quality options
- File size estimate

## 🐛 Troubleshooting

### "Invalid URL" Error

- Ensure the URL is a complete YouTube link (e.g., `https://www.youtube.com/watch?v=...`)
- Check for typos in the URL

### Downloads Keep Failing

- Verify your internet connection
- Check if the download location has write permissions
- Ensure the disk has sufficient free space
- Try updating yt-dlp: `pip install --upgrade yt-dlp`

### GUI Not Launching

- Verify Python version (3.8+): `python --version`
- Reinstall customtkinter: `pip install --force-reinstall customtkinter`
- On Linux, ensure tkinter is installed: `sudo apt-get install python3-tk`

### Slow Downloads

- Check your internet speed
- Lower the video quality setting
- Ensure no other applications are consuming bandwidth

### Theme Not Applying

- Restart the application after changing theme settings
- Check that your system supports the selected theme mode

## 📝 File Format Variables

When configuring the `filename_format`, you can use these yt-dlp variables:

| Variable          | Example        | Description            |
| ----------------- | -------------- | ---------------------- |
| `%(title)s`       | "How to Code"  | Video title            |
| `%(uploader)s`    | "Tech Channel" | Creator's channel name |
| `%(upload_date)s` | "20250723"     | Upload date (YYYYMMDD) |
| `%(duration)s`    | "450"          | Duration in seconds    |
| `%(ext)s`         | "mp4"          | File extension         |
| `%(id)s`          | "dQw4w9WgXcQ"  | YouTube video ID       |

Example custom format: `%(upload_date)s - %(title)s [%(uploader)s]`

## 🌐 System Requirements

### Minimum

- CPU: Dual-core processor
- RAM: 512 MB
- Storage: 100 MB for application + space for downloads
- Network: Stable internet connection

### Recommended

- CPU: Quad-core processor or better
- RAM: 2 GB or more
- Storage: SSD with at least 1 GB free space
- Network: High-speed internet (for faster downloads)

## 📜 License

This project is provided as-is for personal and educational use. Please respect YouTube's Terms of Service and copyright laws when downloading content.

## ⚠️ Legal Notice

- **Respect Copyright** - Only download content you have permission to download
- **Terms of Service** - Usage complies with YouTube's Terms of Service
- **Liability** - The creator is not responsible for misuse of this tool
- **Video Rights** - You are responsible for ensuring downloaded content respects copyright laws

## 🤝 Contributing

To contribute improvements:

1. Test your changes thoroughly
2. Ensure code follows the existing style
3. Add comments for complex logic
4. Submit with clear descriptions

## 🎯 Future Enhancements

Planned features for future releases:

- [ ] Batch URL importing from text file
- [ ] Subtitle downloading support
- [ ] Conversion to alternative formats (MP3, WebM, etc.)
- [ ] Download queue management
- [ ] Channel subscription tracking
- [ ] Statistics dashboard
- [ ] Video filtering and sorting in history
- [ ] Export history to CSV/JSON
- [ ] Multi-language support

## 📞 Support

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Verify all dependencies are installed: `pip list`
3. Update yt-dlp: `pip install --upgrade yt-dlp`
4. Check internet connectivity
5. Review application logs in the console output

## 🙏 Acknowledgments

- **yt-dlp** - Powerful video downloader
- **customtkinter** - Modern Python GUI framework
- **Pillow** - Image processing
- **requests** - HTTP library

---

**Version**: 1.0.0  
**Last Updated**: July 2026  
**Status**: Active Development

Enjoy downloading! 🎉
