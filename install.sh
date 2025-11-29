#!/bin/bash
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

INSTALL_DIR="/opt/ghostbot"
REPO_URL="https://github.com/furik30/ghostbot.git"
BRANCH=${1:-main}

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Run as root: sudo bash install.sh${NC}"
    exit 1
fi

echo -e "${GREEN}=== GhostBot Auto-Installer (Branch: $BRANCH) ===${NC}"

# 1. Проверка зависимостей
if ! command -v git &> /dev/null; then
    apt-get update && apt-get install -y git
fi

if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
fi

# 2. Клонирование или обновление кода
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Directory $INSTALL_DIR exists. Updating...${NC}"
    cd "$INSTALL_DIR"
    git fetch origin
    # Переключаемся на выбранную ветку
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    echo "Cloning repository ($BRANCH)..."
    git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 3. Настройка .env
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
    echo -e "${GREEN}Config created.${NC}"
else
    echo -e "${YELLOW}.env exists. Skipping setup.${NC}"
fi

# 4. Сборка и Авторизация
echo -e "\n${YELLOW}=== Building Container ===${NC}"
docker compose build

if [ ! -f "sessions/ghost_session.session" ]; then
    echo -e "\n${GREEN}=== Telegram Login ===${NC}"
    echo "Please login now. Press Ctrl+C when you see 'GHOST BOT STARTED'."
    docker compose run --rm -it ghost_bot
fi

# 5. Установка системной команды
cp ghostbot.sh /usr/bin/ghostbot
chmod +x /usr/bin/ghostbot
sed -i "s|GHOST_DIR=.*|GHOST_DIR=\"$INSTALL_DIR\"|" /usr/bin/ghostbot

# 6. Запуск
echo -e "\n${GREEN}=== Starting Daemon ===${NC}"
docker compose up -d

echo -e "\n${GREEN}Done! Use 'ghostbot' command to manage.${NC}"