#!/bin/bash
# Deploy script to fix MGA Bot with nginx reverse proxy

set -e

echo "🚀 Deploying MGA Bot fix with nginx reverse proxy"
echo "================================================"

# Check if we're on the server
if [ ! -f "/var/www/mga-portal/src/telegram_agent_google.py" ]; then
    echo "❌ Error: This script must be run on the production server"
    echo "   Expected path: /var/www/mga-portal/src/telegram_agent_google.py"
    exit 1
fi

# Create SSL certificate if it doesn't exist
echo "🔐 Setting up SSL certificate..."
sudo mkdir -p /etc/nginx/ssl
if [ ! -f /etc/nginx/ssl/telegram-bot.crt ]; then
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/telegram-bot.key \
        -out /etc/nginx/ssl/telegram-bot.crt \
        -subj "/C=AT/ST=Tirol/L=Innsbruck/O=Marcel Gladbach/CN=telegram-bot"
    echo "✅ SSL certificate created"
else
    echo "✅ SSL certificate already exists"
fi

# Backup original bot file
echo "📦 Backing up original bot file..."
cp /var/www/mga-portal/src/telegram_agent_google.py /var/www/mga-portal/src/telegram_agent_google.py.bak

# Copy the HTTP version
echo "📝 Deploying HTTP version of bot..."
cp telegram_agent_google_http.py /var/www/mga-portal/src/telegram_agent_google_http.py

# Install python-dotenv if not already installed
echo "📦 Ensuring python-dotenv is installed..."
pip3 install python-dotenv

# Setup nginx configuration
echo "🔧 Configuring nginx..."
sudo cp mga-bot.conf /etc/nginx/sites-available/mga-bot
sudo ln -sf /etc/nginx/sites-available/mga-bot /etc/nginx/sites-enabled/mga-bot

# Remove any conflicting configurations
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
sudo nginx -t

# Reload nginx
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

# Stop any existing bot processes
echo "🛑 Stopping existing bot processes..."
pm2 delete telegram-google || true
pkill -f telegram_agent_google.py || true

# Start the HTTP version with PM2
echo "🚀 Starting bot with PM2..."
cd /var/www/mga-portal
pm2 start src/telegram_agent_google_http.py --name telegram-google --interpreter python3

# Save PM2 configuration
pm2 save
pm2 startup || true

# Wait a moment for the bot to start
sleep 3

# Check bot status
echo ""
echo "📊 Bot status:"
pm2 list
echo ""
pm2 logs telegram-google --lines 20 --nostream

# Register webhook
echo ""
echo "🔗 Registering Telegram webhook..."
cd /var/www/mga-portal
export SERVER_HOST="157.90.232.184"
python3 scripts/register_webhook.py

# Final health check
echo ""
echo "🏥 Checking bot health..."
curl -s http://127.0.0.1:5000/health | python3 -m json.tool

echo ""
echo "✅ Deployment complete!"
echo "🔗 Webhook URL: https://157.90.232.184:8443/telegram-webhook"
echo "📱 Test your bot in Telegram!"