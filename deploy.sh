#!/bin/bash

# MGA Bot Deployment Script
# This script deploys the bot to the production server

set -e

echo "🚀 MGA Bot Deployment Script"
echo "============================"

# Configuration
SERVER_USER="root"
SERVER_HOST="157.90.232.184"
SERVER_PATH="/var/www/mga-portal"
BOT_SERVICE_NAME="mga-bot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please create it from .env.example"
    exit 1
fi

print_info "Starting deployment to $SERVER_HOST..."

# Create deployment package
print_status "Creating deployment package..."
tar -czf deploy.tar.gz \
    src/ \
    requirements.txt \
    .env \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git'

# Upload to server
print_status "Uploading to server..."
scp -i ~/.ssh/mga-hetzner deploy.tar.gz $SERVER_USER@$SERVER_HOST:/tmp/

# Deploy on server
print_status "Deploying on server..."
ssh -i ~/.ssh/mga-hetzner $SERVER_USER@$SERVER_HOST << 'ENDSSH'
    set -e
    
    # Extract files
    cd /var/www/mga-portal
    tar -xzf /tmp/deploy.tar.gz
    rm /tmp/deploy.tar.gz
    
    # Install/update dependencies
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
    fi
    
    # Restart bot service
    # If using systemd
    if systemctl is-active --quiet mga-bot; then
        systemctl restart mga-bot
        echo "Bot service restarted"
    # If using PM2
    elif pm2 list | grep -q "mga-bot"; then
        pm2 restart mga-bot
        echo "PM2 process restarted"
    else
        echo "Warning: Bot service not found. You may need to start it manually."
    fi
    
    echo "Deployment completed!"
ENDSSH

# Clean up local files
rm deploy.tar.gz

print_status "Deployment completed successfully!"
print_info "Check the bot status with: ssh -i ~/.ssh/mga-hetzner $SERVER_USER@$SERVER_HOST 'pm2 status mga-bot'"