#!/bin/bash
# install.sh
set -e

echo "Downloading latest version..."
curl -L -o ~/.local/bin/steam-launch-arg-configurator https://github.com/jpark2398/steam-launch-arg-configurator/releases/latest/download/steam-launch-arg-configurator
chmod +x ~/.local/bin/steam-launch-arg-configurator

# Create .desktop file
cat <<EOF > ~/.local/share/applications/steam-launch-arg-configurator.desktop
[Desktop Entry]
Name=Steam Launch Arg Configurator
Exec=$HOME/.local/bin/steam-launch-arg-configurator
Icon=$HOME/.local/share/icons/steam-launch-arg-configurator.png
Type=Application
Categories=Utility;
EOF