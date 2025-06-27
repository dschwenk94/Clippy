# 🎯 Clippy - AI-Powered YouTube Shorts Generator

Transform long-form YouTube videos into viral shorts with AI-powered speaker detection, dynamic captions, and seamless YouTube upload integration.

## ✨ Features

- **🎤 Auto-Peak Detection**: AI identifies the most engaging moments in videos
- **👥 Speaker Detection & Switching**: Dynamically crops video to focus on current speaker
- **📝 Smart Captions**: Phrase-by-phrase captions with speaker-specific colors using ASS Caption System V6 (Speech Sync)
- **✏️ Real-time Caption Editing**: Edit captions with instant preview
- **📤 YouTube Integration**: One-click upload to YouTube Shorts with OAuth
- **🚀 Multi-User Support**: Multiple users with individual Google accounts

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- FFmpeg installed and in PATH
- PostgreSQL (for multi-user support)
- Google Cloud Project with YouTube Data API v3 enabled

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dschwenk94/Clippy.git
   cd Clippy
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements_webapp.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

Access the web interface at: `http://localhost:5000`

## 📂 Project Structure

```
Clippy/
├── app.py                      # Main Flask application
├── requirements_webapp.txt     # Python dependencies
├── .env.example               # Environment variables template
├── src/                       # Source code (organized modules)
│   ├── core/                  # Core processing modules
│   │   ├── auto_peak_viral_clipper.py      # Auto-peak detection & clip generation
│   │   ├── viral_clipper_complete.py       # Complete viral clip system
│   │   ├── enhanced_heuristic_peak_detector.py  # Peak detection algorithms
│   │   └── storage_optimizer.py            # Storage management utilities
│   ├── captions/              # Caption processing modules
│   │   ├── ass_caption_update_system_v6.py # Speech-synced caption system
│   │   ├── ass_subtitle_generation.py      # ASS subtitle generation
│   │   ├── srt_viral_caption_system.py     # SRT caption system
│   │   └── caption_fragment_fix.py         # Caption fixing utilities
│   ├── routes/                # Flask route handlers
│   │   └── tiktok_routes.py   # TikTok integration endpoints
│   └── utils/                 # Utility functions
│       └── install_deps.py    # Dependency installation helper
├── templates/                 # HTML templates
├── static/                    # CSS, JavaScript, assets
├── configs/                   # Configuration files
├── database/                  # Database migrations & models
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
└── tests/                     # Test suite
```

## 🎥 Caption System

Clippy uses the **ASS Caption Update System V6** which features:
- **Speech Synchronization**: Captions perfectly sync with original speech timing
- **Speaker Colors**: Automatic color coding for different speakers
- **Viral Word Highlighting**: Emphasizes engaging words
- **Pop-out Effects**: Dynamic caption animations

## 📖 Documentation

- [Setup Guide](docs/SETUP.md)
- [Multi-User Configuration](docs/MULTIUSER.md)
- [API Reference](docs/API.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Repository Reorganization](docs/REPOSITORY_REORGANIZATION.md)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
