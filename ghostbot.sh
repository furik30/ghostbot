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
        docker compose up -d
        ;;
    down)
        echo -e "${RED}Stopping...${NC}"
        docker compose down
        ;;
    restart)
        echo -e "${YELLOW}Restarting...${NC}"
        docker compose up -d --force-recreate
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
        git pull origin "$TARGET_BRANCH"
        
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