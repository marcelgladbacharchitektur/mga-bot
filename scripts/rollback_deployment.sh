#!/bin/bash
# Rollback Script for MGA Telegram Bot Deployment
# This safely removes the bot without affecting other services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SERVICE_NAME="mga-telegram-bot"
NGINX_CONFIG="/etc/nginx/sites-available/telegram-bot.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/telegram-bot.conf"
BOT_DIR="/opt/mga-bot"
LOG_DIR="/var/log/mga-telegram-bot"

echo -e "${YELLOW}🔄 MGA Telegram Bot - Rollback Procedure${NC}"
echo "========================================"
echo "This will safely remove the bot deployment"
echo ""

# Confirmation
read -p "Are you sure you want to rollback? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled."
    exit 0
fi

echo -e "\n${YELLOW}Step 1: Stopping Bot Service${NC}"
echo "============================"

# Stop the service if running
if systemctl is-active --quiet $SERVICE_NAME; then
    sudo systemctl stop $SERVICE_NAME
    echo -e "${GREEN}✅ Bot service stopped${NC}"
else
    echo -e "${GREEN}✅ Bot service already stopped${NC}"
fi

# Disable the service
if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
    sudo systemctl disable $SERVICE_NAME
    echo -e "${GREEN}✅ Bot service disabled${NC}"
fi

echo -e "\n${YELLOW}Step 2: Removing Nginx Configuration${NC}"
echo "==================================="

# Remove nginx site link
if [ -L "$NGINX_ENABLED" ]; then
    sudo rm "$NGINX_ENABLED"
    echo -e "${GREEN}✅ Nginx site disabled${NC}"
fi

# Test nginx before reload
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo -e "${GREEN}✅ Nginx reloaded${NC}"
else
    echo -e "${RED}❌ Nginx config error - please check manually${NC}"
fi

echo -e "\n${YELLOW}Step 3: Removing Systemd Service${NC}"
echo "=============================="

# Remove systemd service file
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    sudo rm "/etc/systemd/system/$SERVICE_NAME.service"
    sudo systemctl daemon-reload
    echo -e "${GREEN}✅ Systemd service removed${NC}"
fi

echo -e "\n${YELLOW}Step 4: Cleaning Up Files${NC}"
echo "======================="

# Archive logs instead of deleting
if [ -d "$LOG_DIR" ]; then
    ARCHIVE_NAME="mga-bot-logs-$(date +%Y%m%d-%H%M%S).tar.gz"
    sudo tar -czf "/root/$ARCHIVE_NAME" -C "$LOG_DIR" .
    echo -e "${GREEN}✅ Logs archived to /root/$ARCHIVE_NAME${NC}"
fi

# Optional: Remove bot directory
echo -e "\n${YELLOW}Optional: Remove bot directory?${NC}"
echo "The bot directory contains code and configuration."
read -p "Remove $BOT_DIR? (yes/no): " remove_dir
if [ "$remove_dir" = "yes" ]; then
    sudo rm -rf "$BOT_DIR"
    echo -e "${GREEN}✅ Bot directory removed${NC}"
else
    echo -e "${YELLOW}ℹ️  Bot directory preserved at $BOT_DIR${NC}"
fi

# Remove nginx config file
if [ -f "$NGINX_CONFIG" ]; then
    sudo rm "$NGINX_CONFIG"
    echo -e "${GREEN}✅ Nginx config file removed${NC}"
fi

echo -e "\n${YELLOW}Step 5: Removing Telegram Webhook${NC}"
echo "==============================="

# Check if .env file exists to get token
if [ -f "$BOT_DIR/.env" ] && [ "$remove_dir" != "yes" ]; then
    source "$BOT_DIR/.env"
    if [ ! -z "$TELEGRAM_BOT_TOKEN" ]; then
        curl -s https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook > /dev/null
        echo -e "${GREEN}✅ Telegram webhook removed${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not find bot token to remove webhook${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Remember to manually delete the Telegram webhook${NC}"
fi

echo -e "\n${YELLOW}Step 6: Verification${NC}"
echo "=================="

# Check all services are still running
echo -e "\n🔍 Checking existing services..."
for service in nginx mysql postgresql redis-server umami uptime-kuma; do
    if systemctl is-active --quiet $service 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} $service is running normally"
    fi
done

# Check nginx is serving other sites
echo -e "\n🌐 Active nginx sites:"
ls -la /etc/nginx/sites-enabled/ | grep -v "total\|^d" | awk '{print "  - " $9}'

echo -e "\n${GREEN}✅ Rollback Complete!${NC}"
echo "==================="
echo ""
echo "The bot has been removed without affecting other services."
echo "Log archive saved to: /root/$ARCHIVE_NAME"
echo ""
echo "To redeploy, run: ./scripts/safe_server_deploy.sh"