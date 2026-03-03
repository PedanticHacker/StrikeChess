#!/bin/bash

DESKTOP_DIRECTORY="$HOME/.local/share/applications"
INSTALLATION_DIRECTORY="$HOME/.local/share/StrikeChess"

mkdir -p "$DESKTOP_DIRECTORY"
mkdir -p "$INSTALLATION_DIRECTORY"

cp StrikeChess "$INSTALLATION_DIRECTORY/"
cp logo.svg "$INSTALLATION_DIRECTORY/"

cat > "$DESKTOP_DIRECTORY/StrikeChess.desktop" << EOF
[Desktop Entry]
Categories=BoardGame;Game;
Comment=Chess app with Stockfish 18
Exec=$INSTALLATION_DIRECTORY/StrikeChess
Icon=$INSTALLATION_DIRECTORY/logo.svg
Name=StrikeChess
Terminal=false
Type=Application
EOF

chmod +x "$INSTALLATION_DIRECTORY/StrikeChess"

echo "StrikeChess installed."
