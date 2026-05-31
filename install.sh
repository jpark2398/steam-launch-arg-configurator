#!/bin/bash
# install.sh - User-friendly automated installer
set -e

# ANSI Color codes for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==> Steam Launch Arg Configurator Installer${NC}"

# Define URLs
BASE_URL="https://raw.githubusercontent.com/jpark2398/steam-launch-arg-configurator/main"
BINARY_URL="https://github.com/jpark2398/steam-launch-arg-configurator/releases/latest/download/steam-launch-arg-configurator"

echo -e "${GREEN}[1/3]${NC} Downloading latest binary..."
mkdir -p ~/.local/bin
curl -s -S -L -o ~/.local/bin/steam-launch-arg-configurator $BINARY_URL
chmod +x ~/.local/bin/steam-launch-arg-configurator

echo -e "${GREEN}[2/3]${NC} Setting up application icon..."
mkdir -p ~/.local/share/icons
curl -s -S -L -o ~/.local/share/icons/steam-launch-arg-configurator.png $BASE_URL/icon.png

echo -e "${GREEN}[3/3]${NC} Creating desktop entry..."
cat <<EOF > ~/.local/share/applications/steam-launch-arg-configurator.desktop
[Desktop Entry]
Name=Steam Launch Arg Configurator
Exec=$HOME/.local/bin/steam-launch-arg-configurator
Icon=$HOME/.local/share/icons/steam-launch-arg-configurator.png
Type=Application
Categories=Utility;
EOF

# Refresh the desktop database
update-desktop-database ~/.local/share/applications/ > /dev/null 2>&1

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}Success!${NC} Steam Launch Arg Configurator is installed."
echo -e "You can now launch it from your application menu."
echo -e "${BLUE}======================================================${NC}"