#!/bin/bash
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

INSTALL_DIR="/opt/ghostbot"
BIN_PATH="/usr/bin/ghostbot"

echo -e "${GREEN}=== GhostBot Installer ===${NC}"

if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}Please run as root (sudo ./install.sh)${NC}"
  exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

CURRENT_DIR=$(pwd)
if [ "$CURRENT_DIR" != "$INSTALL_DIR" ]; then
    echo "Creating install directory at $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
    cp -r . "$INSTALL_DIR/"
    cd "$INSTALL_DIR"
fi

echo "Installing 'ghostbot' command..."
cp ghostbot.sh "$BIN_PATH"
chmod +x "$BIN_PATH"

sed -i "s|GHOST_DIR=.*|GHOST_DIR=\"$INSTALL_DIR\"|" "$BIN_PATH"

echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Now you can use the 'ghostbot' command from anywhere."
echo "1. Edit config:   ghostbot edit-env"
echo "2. First login:   ghostbot login"
echo "3. Start bot:     ghostbot up"