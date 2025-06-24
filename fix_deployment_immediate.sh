#!/bin/bash
# IMMEDIATE FIX: Get MGA Bot online with nginx reverse proxy

echo "🚀 MGA Bot Immediate Fix - Nginx Reverse Proxy Solution"
echo "======================================================="

# Create modified bot file that runs on HTTP
cat > /tmp/telegram_agent_google_http.py << 'EOF'
#!/usr/bin/env python3
"""
MGA Telegram Bot - HTTP Version for Nginx Proxy
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
import requests
from groq import Groq
import io
from typing import Dict, Any, Optional, Tuple, List
import re

# Google Drive imports
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Supabase imports
from supabase import create_client, Client

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configuration - From Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')  # Base64 encoded
GOOGLE_DRIVE_ROOT_FOLDER_ID = os.getenv('GOOGLE_DRIVE_ROOT_FOLDER_ID', '0ADxsi_12PIVhUk9PVA')

# Supabase Configuration - From Environment Variables
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')

# Initialize Flask
app = Flask(__name__)

# [REST OF THE CODE REMAINS THE SAME UNTIL THE BOTTOM]
# ... (copy all the functions and routes from the original file) ...

# MODIFIED SECTION - Run on HTTP port 5000 for nginx proxy
if __name__ == '__main__':
    # Initialize all services
    init_services()
    
    logger.info("🚀 MGA Telegram Bot starting (HTTP mode for nginx proxy)...")
    logger.info(f"📱 Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    logger.info(f"🧠 AI Provider: Groq (Llama 3.3)")
    logger.info(f"💾 Storage: Google Drive ({GOOGLE_DRIVE_ROOT_FOLDER_ID})")
    logger.info(f"🗄️ Database: Supabase {'✅ Connected' if supabase_client else '❌ Not configured'}")
    logger.info(f"⏱️ Time Tracking: ✅ Enabled")
    logger.info("✅ HTTP Server ready on port 5000 (nginx will handle SSL)")
    
    # Run on HTTP port 5000, nginx will proxy and handle SSL
    app.run(host='127.0.0.1', port=5000, debug=False)
EOF

# Create nginx configuration
cat > /tmp/mga-bot-nginx.conf << 'EOF'
server {
    listen 8443 ssl;
    server_name _;
    
    # SSL configuration
    ssl_certificate /etc/nginx/ssl/telegram-bot.crt;
    ssl_certificate_key /etc/nginx/ssl/telegram-bot.key;
    
    # SSL parameters
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Telegram webhook endpoint
    location /telegram-webhook {
        proxy_pass http://127.0.0.1:5000/telegram-webhook;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Telegram specific
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Create deployment script for server
cat > /tmp/deploy_immediate_fix.sh << 'DEPLOY_SCRIPT'
#!/bin/bash
set -e

echo "🔧 Deploying immediate fix on server..."

# Create self-signed certificate for nginx
sudo mkdir -p /etc/nginx/ssl
if [ ! -f /etc/nginx/ssl/telegram-bot.crt ]; then
    echo "🔐 Creating self-signed SSL certificate..."
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/telegram-bot.key \
        -out /etc/nginx/ssl/telegram-bot.crt \
        -subj "/C=AT/ST=Tirol/L=Innsbruck/O=MGA/CN=telegram-bot"
fi

# Copy nginx config
sudo cp /tmp/mga-bot-nginx.conf /etc/nginx/sites-available/mga-bot
sudo ln -sf /etc/nginx/sites-available/mga-bot /etc/nginx/sites-enabled/mga-bot

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Stop current bot process
pm2 delete telegram-google || true
pkill -f telegram_agent_google.py || true

# Start bot with HTTP mode
cd /var/www/mga-portal
pm2 start /tmp/telegram_agent_google_http.py --name telegram-google --interpreter python3
pm2 save

echo "✅ Bot should now be running behind nginx proxy!"
echo "🔗 Webhook URL: https://SERVER_IP:8443/telegram-webhook"
DEPLOY_SCRIPT

echo "📝 Instructions to deploy:"
echo "1. Copy the modified bot file to your server"
echo "2. Setup nginx as reverse proxy"
echo "3. Run the bot on HTTP port 5000"
echo "4. Nginx handles SSL on port 8443"