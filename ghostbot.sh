#!/bin/bash
GHOST_DIR="/opt/ghostbot"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ ! -d "$GHOST_DIR" ]; then
    GHOST_DIR=$(pwd)
fi

cd "$GHOST_DIR" || exit 1

# Функция для получения текущей ветки
get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

case "$1" in
    up)
        echo -e "${GREEN}Starting...${NC}"
        docker compose up -d --build
        ;;
    down)
        echo -e "${RED}Stopping...${NC}"
        docker compose down
        ;;
    restart)
        echo -e "${YELLOW}Restarting...${NC}"
        docker compose up -d --build --force-recreate
        ;;
    logs)
        LINES=${2:-100}
        docker compose logs -f --tail="$LINES"
        ;;
    update)
        # Можно указать ветку: ghostbot update dev
        TARGET_BRANCH=${2:-$(get_current_branch)}
        
        echo -e "${YELLOW}Updating from branch: ${TARGET_BRANCH}...${NC}"
        
        git fetch origin
        git checkout "$TARGET_BRANCH"
        git reset --hard origin/"$TARGET_BRANCH"
        
        echo -e "${YELLOW}Rebuilding image...${NC}"
        docker compose build
        
        echo -e "${GREEN}Restarting...${NC}"
        docker compose up -d
        ;;
    status)
        docker compose ps
        ;;
    edit-env)
        nano .env
        ;;
    edit-prompts)
        nano prompts.yaml
        ;;
    login)
        echo -e "${YELLOW}Interactive Login Mode${NC}"
        docker compose down
        docker compose run --rm -it ghost_bot
        ;;
    switch-api)
        KEY_NUM=$2

        if [ -z "$KEY_NUM" ]; then
            echo -e "${RED}Ошибка: Укажите номер ключа (например: ghostbot switch-api 2)${NC}"
            exit 1
        fi

        if [ ! -f .env ]; then
             echo -e "${RED}Ошибка: Файл .env не найден!${NC}"
             exit 1
        fi

        NEW_KEY_VAL=$(grep "^GEMINI_API_KEY${KEY_NUM}=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")

        if [ -z "$NEW_KEY_VAL" ]; then
            echo -e "${RED}Ошибка: Ключ GEMINI_API_KEY${KEY_NUM} не найден в .env${NC}"
            exit 1
        fi

        echo -e "${YELLOW}Переключаюсь на GEMINI_API_KEY${KEY_NUM}...${NC}"

        sed -i "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=${NEW_KEY_VAL}|" .env

        echo -e "${GREEN}Ключ успешно обновлен в .env!${NC}"

        $0 restart
        ;;
    help|*)
        echo -e "${GREEN}GhostBot Manager${NC}"
        echo "Usage: ghostbot [command]"
        echo ""
        echo "Commands:"
        echo "  up              Start background daemon"
        echo "  down            Stop bot"
        echo "  restart         Restart bot"
        echo "  logs [n]        Show logs (default 100 lines)"
        echo "  update [branch] Update code (default: current branch)"
        echo "  status          Container status"
        echo "  login           Re-login to Telegram"
        echo "  edit-env        Edit config"
        echo "  edit-prompts    Edit prompts"
        ;;
esac