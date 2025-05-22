# StrikeChess 1.0

## What's this?

This is StrikeChess, an app for playing chess against an engine.

## How can I get started quickly?

Here's what you need to do:

1. Make sure you have Python 3.13 installed. If not, read below:

    - For Windows, :point_right: [click here to download Python 3.13 installer](https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe) :point_left:
    - For Linux, execute `sudo apt-get install python3.13` in the
      terminal or execute a command applicable for the package manager
      of your Linux distribution
    - For macOS, :point_right: [click here to download Python 3.13 installer](https://www.python.org/ftp/python/3.13.3/python-3.13.3-macos11.pkg) :point_left:

2. Install required packages by executing this command in the terminal
   from within StrikeChess's top-level directory:

```bash
pip install -r requirements.txt
```

:point_right: On macOS, the `pip` command is written as `pip3`.

3. Launch StrikeChess by executing this command in the terminal from
   within StrikeChess's top-level directory:

```bash
python main.py
```

:point_right: On macOS, the `python` command is written as `python3`.

4. Start playing by doing this:

    - Start dragging a piece to see its legal target squares.
    - Drag the piece to a legal target square and drop it there to make
      your move.
    - Use the Settings button to customize your experience.

## In what programming language is StrikeChess written?

That would be **Python**.

### What version of Python are we talking about here?

It would be best if you launch StrikeChess using Python **3.13**.

### Why 3.13 specifically?

As tested, StrikeChess works on all major platforms using Python 3.13,
so on Windows, Linux, and macOS.

### What about other Python versions?

StrikeChess should work using a Python version older than 3.13, but it
surely won't work using a 2.x version. If needed, modify the source code
to adapt it to your specific Python version.

## Are there any dependencies?

Yes. StrikeChess depends upon:

- **python-chess**: A library for developing chess apps
- **psutil**: A library for getting operating system metrics
- **PySide6**: A framework for developing cross-platform GUI apps

### Is there any 3rd-party software integrated?

Yes. StrikeChess integrates **Stockfish**, a powerful engine for playing
and analyzing a game.

## What features does StrikeChess provide?

You get all the basic building blocks for playing chess:

- board
- clocks
- FEN editor
- table view for showing Standard Algebraic Notation (SAN)

### Is that it?

There are also many features you can use:

- flip the board
- analyze a position
- load an engine of your choice
- force the engine to make a move
- navigate through moves of the game
- select from one of the dark or light styles
- play against the latest version of the Stockfish engine
- paste a FEN from the clipboard by double-clicking the FEN editor

## Which chess variants are supported?

Chess variants are not supported.

## How do I move a piece on the board?

Making a move in StrikeChess is as simple as a drag. Just drag a piece
to one of its legal squares and then drop it there to make your move.

### How do I know which legal squares are available for a piece?

After you start dragging a piece, all of its legal squares get marked
with a dot. That's how you know.

## How does StrikeChess look?

The following screenshots show how StrikeChess looks in **Dark mint**
style.

![Settings dialog](https://github.com/user-attachments/assets/10b397b0-d855-47c7-b148-5a900c4feb29 "Settings dialog")
*Changing the settings.*

![Move history](https://github.com/user-attachments/assets/3226951e-ce18-4638-9e9d-070833ab8454 "Move history")
*Selecting a move from the table view.*

![Position analysis](https://github.com/user-attachments/assets/a7d3137a-fe5c-404a-bc3d-f0dbe76259be "Position analysis")
*Analyzing a chessboard position for the best move.*

![Pawn promotion](https://github.com/user-attachments/assets/9c922ee8-2633-49ca-9f04-7ec2c1ebcb14 "Pawn promotion")
*Promoting a white pawn to a queen, a rook, a bishop, or a knight.*

## What's the default engine in StrikeChess?

The latest version of **Stockfish** is the default engine. It works on
Windows, Linux, and macOS platforms.

### What if I want to play against some other engine?

You can load and then play against or analyze with any engine, but it
has to be a UCI-compliant one.

### Why does it have to be a UCI-compliant engine?

An engine compliant only with Chess Engine Communication Protocol (CECP)
and designed for either the WinBoard GUI (on Windows platform) or the
XBoard GUI (on a Linux-based platform) can't be loaded in StrikeChess,
because it doesn't support this type of protocol. If your engine is also
compliant with Universal Chess Interface (UCI), then you're in luck.

### Can I analyze a position?

Yes. You can analyze a position with the default Stockfish engine or a
UCI-compliant engine you load yourself.

## Who should get thanks for StrikeChess?

1. Thanks to all developers for their dedicated work on the Python
   programming language!

    - [Source](https://github.com/python/cpython)
    - [Downloads](https://www.python.org/downloads)

2. Thanks to developer Giampaolo Rodola for his dedicated work on the
   psutil library!

    - [Source](https://github.com/giampaolo/psutil)
    - [PyPI](https://pypi.org/project/psutil)

3. Thanks to all developers for their dedicated work on the PySide6 GUI
   framework!

    - [PyPI](https://pypi.org/project/PySide6)

4. Thanks to developer Niklas Fiekas for his dedicated work on the
   python-chess library!

    - [Source](https://github.com/niklasf/python-chess)
    - [PyPI](https://pypi.org/project/chess)

5. Last but not least, thanks to all developers for their dedicated work
   on the Stockfish engine!

    - [Source](https://github.com/official-stockfish/Stockfish)
    - [Downloads](https://stockfishchess.org/download)

## What license does StrikeChess use?

StrikeChess uses the **MIT License**.

### Where can I see the license?

See the `LICENSE.txt` file in the top-level directory of StrikeChess
about the permissions, limitations, and conditions of the license.

### Can I develop an app based on StrikeChess?

Absolutely! For your app, you can use any license, but make sure to
include my copyright notice above yours.

Your copyright notice should look like this:

```
Copyright (C) 2025 Boštjan Mejak
Copyright (C) 2025 John Doe
```

On the second line, provide the year in which you are releasing your app
and provide your legal first and last name.

#### What if I also want to integrate Stockfish?

If you intend to integrate Stockfish in your app:

1. Include Stockfish's copyright notice
2. Include the GPLv3 License to comply with Stockfish's license

See the `NOTICE.txt` file to get an idea how to do this.
