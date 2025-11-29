#!/bin/bash
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

INSTALL_DIR="/opt/ghostbot"
REPO_URL="https://github.com/furik30/ghostbot"

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Run as root: sudo bash install_fixed.sh${NC}"
    exit 1
fi

echo -e "${GREEN}=== GhostBot Auto-Installer (Fixed) ===${NC}"

if ! command -v git &> /dev/null; then
    apt-get update && apt-get install -y git
fi

if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
fi

# Clone Repo (Ветка DEV)
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Directory $INSTALL_DIR exists. Updating...${NC}"
    cd "$INSTALL_DIR" && git pull
else
    echo "Cloning repository (DEV branch)..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: Failed to clone files. Repository might be empty or branch 'dev' does not exist.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}=== Configuration ===${NC}"
if [ ! -f .env ]; then
    read -p "Enter Telegram API_ID: " API_ID
    read -p "Enter Telegram API_HASH: " API_HASH
    read -p "Enter Gemini API Key: " GEMINI_API_KEY
    
    cat > .env <<EOL
API_ID=$API_ID
API_HASH=$API_HASH
GEMINI_API_KEY=$GEMINI_API_KEY
MODEL_NAME=gemini-2.5-flash
SESSION_NAME=ghost_session
EOL
    echo -e "${GREEN}.env created.${NC}"
else
    echo -e "${YELLOW}.env already exists. Skipping configuration.${NC}"
fi

echo -e "\n${YELLOW}=== Building Container ===${NC}"
docker compose build

if [ ! -f "sessions/ghost_session.session" ]; then
    echo -e "\n${GREEN}=== Telegram Authentication ===${NC}"
    echo "Please login now. Press Ctrl+C only after 'GHOST BOT STARTED' appears."
    docker compose run --rm -it ghost_bot
fi

if [ -f "ghostbot.sh" ]; then
    cp ghostbot.sh /usr/bin/ghostbot
    chmod +x /usr/bin/ghostbot
    sed -i "s|GHOST_DIR=.*|GHOST_DIR=\"$INSTALL_DIR\"|" /usr/bin/ghostbot
else
    echo -e "${RED}Error: ghostbot.sh not found!${NC}"
fi

echo -e "\n${GREEN}=== Starting Daemon ===${NC}"
docker compose up -d

echo -e "\n${GREEN}Success! Type 'ghostbot help' to manage.${NC}"
