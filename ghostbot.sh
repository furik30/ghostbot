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

case "$1" in
    up)
        docker compose up -d
        ;;
    down)
        docker compose down
        ;;
    restart)
        docker compose restart
        ;;
    logs)
        LINES=${2:-100}
        docker compose logs -f --tail="$LINES"
        ;;
    update)
        git pull
        docker compose build
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
        docker compose down
        docker compose run --rm -it ghost_bot
        ;;
    help|*)
        echo -e "${GREEN}GhostBot Manager${NC}"
        echo "Usage: ghostbot [command]"
        echo ""
        echo "Commands:"
        echo "  up           Start the bot (background)"
        echo "  down         Stop the bot"
        echo "  restart      Restart the bot"
        echo "  logs [n]     Show logs (tail n lines)"
        echo "  status       Check container status"
        echo "  update       Git pull + Rebuild + Restart"
        echo "  login        Interactive mode for Telegram Auth"
        echo "  edit-env     Edit .env file"
        echo "  edit-prompts Edit prompts.yaml"
        ;;
esac