#!/bin/bash

SETTINGS_DIRECTORY="$HOME/.StrikeChess"
INSTALLATION_DIRECTORY="$HOME/.local/share/StrikeChess"
DESKTOP_FILE="$HOME/.local/share/applications/StrikeChess.desktop"

rm -f "$DESKTOP_FILE"
rm -rf "$INSTALLATION_DIRECTORY"

read -p "Remove personal settings? [y/N] " response

if [[ "$response" =~ ^[Yy]$ ]]; then
    rm -rf "$SETTINGS_DIRECTORY"
    echo "StrikeChess uninstalled with personal settings removed."
else
    echo "StrikeChess uninstalled. Personal settings preserved in $SETTINGS_DIRECTORY."
fi
