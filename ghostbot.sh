#!/bin/bash
GHOST_DIR="/opt/ghostbot"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ ! -d "$GHOST_DIR" ]; then
    if [ -f "./docker-compose.yml" ]; then
        GHOST_DIR=$(pwd)
    else
        echo -e "${RED}Error: GhostBot directory not found at $GHOST_DIR${NC}"
        echo "Please edit this script to point to your installation folder."
        exit 1
    fi
fi

cd "$GHOST_DIR" || exit 1

case "$1" in
    up)
        echo -e "${GREEN}Starting GhostBot...${NC}"
        docker compose up -d
        ;;
    down)
        echo -e "${RED}Stopping GhostBot...${NC}"
        docker compose down
        ;;
    restart)
        echo -e "${YELLOW}Restarting GhostBot...${NC}"
        docker compose restart
        ;;
    logs)
        LINES=${2:-100}
        docker compose logs -f --tail="$LINES"
        ;;
    update)
        echo -e "${YELLOW}Pulling updates...${NC}"
        git pull
        echo -e "${YELLOW}Rebuilding image...${NC}"
        docker compose build
        echo -e "${GREEN}Restarting...${NC}"
        docker compose up -d
        ;;
    build)
        docker compose build
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
        echo -e "${YELLOW}Stopping background container...${NC}"
        docker compose down
        echo -e "${GREEN}Starting interactive session for Login...${NC}"
        echo -e "${YELLOW}NOTE: Press Ctrl+C after you successfully login and see 'GHOST BOT STARTED'${NC}"
        docker compose up
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