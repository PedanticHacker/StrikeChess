# ⚡ StrikeChess

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/Python-3.14+-blue)
![Stockfish](https://img.shields.io/badge/Stockfish-18-blue)

A chess app with Stockfish 18, 8 themes, 32 time controls, and 3500 openings.

![Preview](https://github.com/user-attachments/assets/0c7fa27c-2638-4634-81d7-0531d4d9064b)

## Features

- **Play against or analyze with Stockfish 18** → bundled engine with automatic CPU optimization
- **Real-time analysis** → evaluation bar visualization, best move arrows, and live principal variation updates
- **PGN support** → import and export games in standard notation
- **FEN editor** → paste or type positions directly, with validation in place
- **Move history** → navigate with arrow keys, mouse wheel, or click
- **Drag-and-drop** → smooth piece movement with slide-back animation
- **Sound effects** → distinct audio output for moves, captures, checks, castling, promotion, and game over
- **8 themes** → 4 dark and 4 light theme variants
- **32 time controls** → 8 time settings × 4 increment options

## Installation

Download the latest stable release for your platform from the [Releases](https://github.com/PedanticHacker/StrikeChess/releases) page.

### Linux users

Extract the downloaded ZIP file, navigate to the extracted directory in your terminal, and run the `install.sh` script:
```bash
cd ~/Downloads/StrikeChess-Linux  # Adjust path if needed
./install.sh
```

## Uninstallation

- **Linux:** Run the `uninstall.sh` script from the extracted `StrikeChess-Linux` directory.
- **Windows/macOS:** Delete the extracted `StrikeChess-Windows` or `StrikeChess-macOS` directory. To also delete personal settings of StrikeChess, delete the `.StrikeChess` directory from your home directory.

## Development

Requirements: Python 3.14+, 2+ GB RAM, 1.5+ GB storage
```bash
git clone https://github.com/PedanticHacker/StrikeChess.git
cd StrikeChess
pip install -r requirements.txt
python main.py
```

Standalone build:
```bash
pip install pyinstaller
pyinstaller --clean bundle.spec
```

## Keyboard Shortcuts

> **macOS:** `Ctrl` → `Command ⌘`, `Alt` → `Option ⌥`

**General**

| Action | Shortcut |
|--------|----------|
| Start new game | `Ctrl+N` |
| Open settings | `F2` |
| Flip board | `Ctrl+F` |
| Navigate moves | `←`/`→` or scroll up/down |
| Load PGN | `Ctrl+O` |
| Save PGN | `Ctrl+S` |
| Set custom position | Double-click FEN editor to paste from clipboard |

**Analysis**

| Action | Shortcut |
|--------|----------|
| Start analysis | `F3` |
| Stop analysis | `F4` |

**Engine**

| Action | Shortcut |
|--------|----------|
| Force engine move | `Ctrl+P` |
| Load custom engine | `Ctrl+L` |
| Unload engine | `Ctrl+U` |

**Themes**

| Shortcut | Theme |
|----------|-------|
| `Alt+1` | Dark Forest |
| `Alt+2` | Dark Mint |
| `Alt+3` | Dark Nebula |
| `Alt+4` | Dark Ocean |
| `Alt+5` | Light Forest |
| `Alt+6` | Light Mint |
| `Alt+7` | Light Nebula |
| `Alt+8` | Light Ocean |

## Licenses

- **StrikeChess:** MIT License © 2026 Boštjan Mejak → See [LICENSE](LICENSE.txt) file
- **Stockfish:** GPLv3 © 2004-2026 The Stockfish developers → See [NOTICE](NOTICE.txt) file
- **Python dependencies:** chess, psutil, py-cpuinfo, PySide6 → See [NOTICE](NOTICE.txt) file
