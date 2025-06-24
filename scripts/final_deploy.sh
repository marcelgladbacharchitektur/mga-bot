#!/bin/bash
# Final deployment script for bot.marcelgladbach.com

set -e

echo "🚀 MGA Bot Deployment to bot.marcelgladbach.com"
echo "=============================================="

# Configuration
DOMAIN="bot.marcelgladbach.com"
BOT_PORT="5000"
NGINX_CONFIG="/etc/nginx/sites-available/bot.marcelgladbach.com"
TARGET_DIR="${TARGET_DIR:-/var/www/mga-portal}"

# Pre-flight checks
echo "✔️ Pre-flight checks..."

# 1. Check if port 5000 is free
if lsof -i:$BOT_PORT > /dev/null 2>&1; then
    echo "❌ Port $BOT_PORT is already in use!"
    lsof -i:$BOT_PORT
    exit 1
fi

# 2. Check nginx
if ! nginx -t > /dev/null 2>&1; then
    echo "❌ Nginx configuration has errors!"
    nginx -t
    exit 1
fi

# 3. Check Python and dependencies
cd "$TARGET_DIR"
if [ ! -f "src/telegram_agent_google.py" ]; then
    echo "❌ Bot file not found at src/telegram_agent_google.py"
    exit 1
fi

echo "✅ All pre-flight checks passed!"

# Modify bot to run on port 5000 (HTTP)
echo "📝 Creating HTTP version of bot..."
cp src/telegram_agent_google.py src/telegram_agent_google_http.py

# Modify the port in the new file
sed -i 's/port=8443/port=5000/g' src/telegram_agent_google_http.py
sed -i 's/SSL Webhook ready on port 8443/HTTP Webhook ready on port 5000/g' src/telegram_agent_google_http.py

# Setup nginx
echo "🔧 Setting up nginx..."
cat > /tmp/bot.marcelgladbach.com.conf << 'EOF'
# Nginx configuration for Telegram Bot
server {
    listen 80;
    server_name bot.marcelgladbach.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bot.marcelgladbach.com;
    
    ssl_certificate /etc/letsencrypt/live/marcelgladbach.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/marcelgladbach.com/privkey.pem;
    
    location /telegram-webhook {
        proxy_pass http://localhost:5000/telegram-webhook;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        proxy_pass http://localhost:5000/health;
    }
    
    location / {
        return 200 'MGA Telegram Bot Service\n';
        add_header Content-Type text/plain;
    }
}
EOF

# Copy nginx config
sudo cp /tmp/bot.marcelgladbach.com.conf $NGINX_CONFIG
sudo ln -sf $NGINX_CONFIG /etc/nginx/sites-enabled/

# Test nginx config
if sudo nginx -t; then
    echo "✅ Nginx configuration valid"
    sudo systemctl reload nginx
else
    echo "❌ Nginx configuration error!"
    exit 1
fi

# SSL Certificate
echo "🔐 Checking SSL certificate..."
if [ ! -f "/etc/letsencrypt/live/marcelgladbach.com/fullchain.pem" ]; then
    echo "📋 Creating SSL certificate for $DOMAIN..."
    sudo certbot certonly --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@marcelgladbach.com
fi

# Start the bot with PM2
echo "🤖 Starting bot with PM2..."
cd "$TARGET_DIR"

# Stop any existing instance
pm2 delete telegram-google || true

# Start new instance
pm2 start src/telegram_agent_google_http.py \
    --name telegram-google \
    --interpreter python3 \
    --log-date-format "YYYY-MM-DD HH:mm:ss"

pm2 save

# Register webhook
echo "🔗 Registering Telegram webhook..."
sleep 5  # Give bot time to start

python3 << EOF
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')
webhook_url = f"https://$DOMAIN/telegram-webhook"

# Delete old webhook
requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")

# Set new webhook
response = requests.post(
    f"https://api.telegram.org/bot{token}/setWebhook",
    data={'url': webhook_url}
)
print(f"Webhook registration: {response.json()}")
EOF

# Final status
echo ""
echo "✅ Deployment complete!"
echo "========================"
echo "🌐 Bot URL: https://$DOMAIN"
echo "🔗 Webhook: https://$DOMAIN/telegram-webhook"
echo "📊 Status: https://$DOMAIN/health"
echo ""
echo "📝 Check logs with: pm2 logs telegram-google"
echo "🔄 Restart with: pm2 restart telegram-google"
echo ""

# Show current status
pm2 list
echo ""
echo "Recent logs:"
pm2 logs telegram-google --lines 20 --nostream