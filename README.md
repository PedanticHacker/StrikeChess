# ⚡ StrikeChess

![License](https://img.shields.io/badge/License-MIT-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/Python-3.14+-blue)
![Stockfish](https://img.shields.io/badge/Stockfish-19-blue)

A chess app with Stockfish 19, 4 languages, 8 themes, 32 time controls, and 3500 openings.

![Preview](https://github.com/user-attachments/assets/0b737e7b-f014-4f5d-8f7b-6fc80f74ac3d)

## Features

- **Play against or analyze with Stockfish 19** → bundled engine with automatic CPU optimization
- **Real-time analysis** → evaluation bar, best move arrows, and principal variation
- **PGN support** → load and save games
- **FEN editor** → type a FEN or double-click to paste one, then press `Enter`
- **Move history** → navigate with arrow keys, mouse wheel, or click
- **Drag-and-drop** → smooth piece movement with slide-back animation
- **Sound effects** → distinct sounds for moves, captures, checks, castling, promotion, and game over
- **4 languages** → German, English, Spanish, and Italian
- **8 themes** → 4 dark and 4 light
- **32 time controls** → 8 time settings × 4 increment options
- **3500 openings** → opening name shown as you play

## Installation

Download the latest stable release for your platform from the [Releases](https://github.com/PedanticHacker/StrikeChess/releases) page.

### Windows users

Requirements: Windows 10+

Extract the downloaded ZIP file and launch `StrikeChess.exe` from the extracted `StrikeChess-Windows` folder. If you see "Windows protected your PC", select **More info**, then **Run anyway**.

### Linux users

Requirements: Arch Linux, CachyOS, Debian 13+, Fedora 39+, Linux Mint 22+, Ubuntu 24.04+, or another distribution with glibc 2.38+, on an Intel or AMD processor

Extract the downloaded ZIP file, navigate to the extracted folder in your terminal, and run the `install.sh` script:
```bash
cd ~/Downloads/StrikeChess-Linux  # Adjust path if needed
bash install.sh
```

Then launch StrikeChess from your app menu, and keep the extracted folder for uninstallation.

### macOS users

Requirements: macOS 14.4+

StrikeChess isn't signed with an Apple Developer certificate, so macOS blocks it when downloaded through a browser. Download it in your terminal instead, which avoids the quarantine attribute:
```bash
cd ~/Downloads
curl -LO https://github.com/PedanticHacker/StrikeChess/releases/latest/download/StrikeChess-macOS.zip
unzip StrikeChess-macOS.zip
open StrikeChess.app
```

If you've already downloaded the ZIP file through a browser, extract it and delete the quarantine attribute that macOS applied to the app:
```bash
cd ~/Downloads  # Adjust path if needed
unzip -o StrikeChess-macOS.zip
xattr -dr com.apple.quarantine StrikeChess.app
open StrikeChess.app
```

## Uninstallation

- **Windows:** Delete the extracted `StrikeChess-Windows` folder. To also delete personal settings, delete the `.StrikeChess` folder from your home folder.
- **Linux:** Run the `uninstall.sh` script from the extracted `StrikeChess-Linux` folder.
- **macOS:** Delete `StrikeChess.app`. To also delete personal settings, run `rm -r ~/.StrikeChess` in your terminal.

## Development

> **Linux/macOS:** Use `python3` and `pip3` instead of `python` and `pip`.

Requirements: Python 3.14+, 2+ GB RAM, 2+ GB storage, and macOS 14.4+ on a Mac
```bash
git clone https://github.com/PedanticHacker/StrikeChess.git
cd StrikeChess
pip install -r requirements.txt
python main.py
```

> **macOS:** The standalone build supports both CPU architectures, Apple Silicon and Intel, so it needs Python from [python.org](https://www.python.org/downloads/macos/), which is built for both. Python from Homebrew or pyenv is built only for your Mac's own CPU architecture.

Standalone build:
```bash
pip install pyinstaller
pyinstaller --clean bundle.spec
```

## Keyboard shortcuts

> **macOS:** `Ctrl` → `Command ⌘`, `Alt` → `Option ⌥`

**General**

| Action | Shortcut |
|--------|----------|
| About StrikeChess | `F1` |
| Settings | `F2` |
| Flip | `Ctrl+F` |
| Load from PGN | `Ctrl+O` |
| Save as PGN | `Ctrl+S` |
| New game | `Ctrl+N` |
| Quit | `Ctrl+Q` |

**Analysis**

| Action | Shortcut |
|--------|----------|
| Start analysis | `F3` |
| Stop analysis | `F4` |

**Engine**

| Action | Shortcut |
|--------|----------|
| Load engine | `Ctrl+L` |
| Unload engine | `Ctrl+U` |
| Play move now | `Ctrl+P` |

**Themes**

| Theme | Shortcut |
|-------|----------|
| Dark Forest | `Alt+1` |
| Dark Mint | `Alt+2` |
| Dark Nebula | `Alt+3` |
| Dark Ocean | `Alt+4` |
| Light Forest | `Alt+5` |
| Light Mint | `Alt+6` |
| Light Nebula | `Alt+7` |
| Light Ocean | `Alt+8` |

## Licenses

- **StrikeChess:** MIT License Copyright (C) 2026 Boštjan Mejak → See [LICENSE](LICENSE.txt) file
- **Stockfish:** GPLv3 Copyright (C) 2004-2026 The Stockfish developers → See [NOTICE](NOTICE.txt) file
- **Python dependencies:** chess, PySide6 → See [NOTICE](NOTICE.txt) file
