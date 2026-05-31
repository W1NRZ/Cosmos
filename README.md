# Cosmos

A premium macOS desktop background manager built with **PyQt6** and **PyQtWebEngine**. Cosmos lets you import images, GIFs, and videos into a personal library and apply them as wallpapers with a single click.

![Cosmos](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)

## Features

- **Import backgrounds** — Add images (JPG, PNG, WebP, HEIC), animated GIFs, and videos (MP4, MOV, WebM, etc.)
- **Library grid** — Browse your collection with auto-generated thumbnails
- **One-click apply** — Switch wallpapers instantly from the grid
- **Native image wallpapers** — Static images are set via AppleScript on all displays
- **Animated media** — GIFs and videos play in desktop-level windows behind your icons
- **Customizable UI** — Tune accent colors, spacing, corner radius, glass blur, button opacity, and animation speed with live CSS variable updates

## Requirements

- macOS 11+
- Python 3.10–3.13 (PyQt6 wheels; 3.14 may not be supported yet)
- Optional: `ffmpeg` for higher-quality video thumbnails
- Optional: `pyobjc-framework-Cocoa` for precise desktop-level media windows

## Installation

```bash
cd Cosmos
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional (improves desktop-level wallpaper placement on macOS):

```bash
pip install pyobjc-framework-Cocoa
```

## Usage

```bash
python main.py
```

1. Click **Import** to add background files
2. Click any card in the library to apply it
3. Open **Customize** to adjust the interface styling

## How wallpapers are applied

| Type   | Method                                              |
|--------|-----------------------------------------------------|
| Image  | `osascript` AppleScript — sets picture on all desktops |
| GIF    | Desktop-level WebEngine window with looping `<img>` |
| Video  | Desktop-level WebEngine window with looping `<video>` |

Static images use the same mechanism as System Settings. GIF and video wallpapers render behind desktop icons using a frameless Qt window at the macOS desktop window level.

## Project structure

```
Cosmos/
├── main.py                 # Entry point
├── cosmos/
│   ├── app.py              # PyQt6 main window
│   ├── bridge.py           # QWebChannel Python ↔ JS bridge
│   ├── config.py           # Paths and constants
│   ├── settings.py         # UI preference persistence
│   ├── library/            # Import, storage, thumbnails
│   └── wallpaper/          # AppleScript + media engine
└── web/
    ├── index.html
    ├── css/styles.css
    └── js/app.js
```

## Data storage

Library files and settings are stored in:

```
~/Library/Application Support/Cosmos/
├── library/       # Imported media files
├── thumbnails/    # Generated preview JPEGs
├── library.json   # Library metadata
└── settings.json  # UI customization
```

## License

MIT
