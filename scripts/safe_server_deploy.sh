#!/bin/bash
# Safe Server Deployment Script for MGA Telegram Bot
# This script carefully integrates the bot without disrupting existing services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BOT_USER="mga-bot"
BOT_DIR="/opt/mga-bot"
VENV_DIR="$BOT_DIR/venv"
SERVICE_NAME="mga-telegram-bot"
NGINX_CONFIG="/etc/nginx/sites-available/telegram-bot.conf"
LOG_DIR="/var/log/mga-telegram-bot"

echo -e "${GREEN}🚀 MGA Telegram Bot - Safe Server Deployment${NC}"
echo "============================================="
echo "Server: 157.90.232.184"
echo "Date: $(date)"
echo ""

# Function to check if command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1 failed!${NC}"
        exit 1
    fi
}

# Function to check if port is in use
check_port() {
    local port=$1
    if sudo ss -tlnp | grep -q ":${port}\s"; then
        echo -e "${RED}❌ Port $port is already in use!${NC}"
        sudo ss -tlnp | grep ":${port}\s"
        return 1
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
        return 0
    fi
}

# Phase 1: System Analysis
echo -e "\n${YELLOW}Phase 1: System Analysis${NC}"
echo "========================"

# Check existing services
echo -e "\n📊 Checking existing services..."
for service in nginx mysql postgresql redis-server umami uptime-kuma; do
    if systemctl is-active --quiet $service 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} $service is running"
    fi
done

# Check critical ports
echo -e "\n🔌 Checking port availability..."
check_port 5000 || exit 1

# Check nginx sites
echo -e "\n🌐 Current nginx sites:"
ls -la /etc/nginx/sites-enabled/ | grep -v "total\|^d" | awk '{print "  - " $9}'

# Check disk space
echo -e "\n💾 Disk space check:"
df -h / | awk 'NR==2 {print "  Usage: " $5 " (Available: " $4 ")"}'

# Phase 2: Pre-deployment Backup
echo -e "\n${YELLOW}Phase 2: Creating Backups${NC}"
echo "========================"

# Backup nginx configuration
BACKUP_DIR="/root/deployment-backups/$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo cp -r /etc/nginx "$BACKUP_DIR/"
check_status "Nginx configuration backed up"

# Save running services state
systemctl list-units --type=service --state=running > "$BACKUP_DIR/running_services.txt"
check_status "Service states backed up"

# Phase 3: Bot Deployment
echo -e "\n${YELLOW}Phase 3: Deploying Bot Application${NC}"
echo "==================================="

# Create bot user (if doesn't exist)
if ! id "$BOT_USER" &>/dev/null; then
    sudo useradd -r -m -s /bin/bash -d "$BOT_DIR" "$BOT_USER"
    check_status "Created bot user"
else
    echo -e "${GREEN}✅ Bot user already exists${NC}"
fi

# Create necessary directories
sudo mkdir -p "$BOT_DIR" "$LOG_DIR"
sudo chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR" "$LOG_DIR"
check_status "Created bot directories"

# Clone or update repository
if [ -d "$BOT_DIR/.git" ]; then
    echo "Updating existing repository..."
    cd "$BOT_DIR"
    sudo -u "$BOT_USER" git pull origin main
else
    echo "Cloning repository..."
    cd "$BOT_DIR"
    # Note: Update with actual repository URL
    sudo -u "$BOT_USER" git clone https://github.com/yourusername/mga-bot.git .
fi
check_status "Code deployed"

# Setup Python virtual environment
sudo -u "$BOT_USER" python3 -m venv "$VENV_DIR"
sudo -u "$BOT_USER" "$VENV_DIR/bin/pip" install --upgrade pip
sudo -u "$BOT_USER" "$VENV_DIR/bin/pip" install -r requirements.txt
check_status "Python dependencies installed"

# Copy environment file (you need to create this)
if [ -f "$BOT_DIR/.env" ]; then
    echo -e "${GREEN}✅ Environment file exists${NC}"
else
    echo -e "${YELLOW}⚠️  Please create $BOT_DIR/.env with required variables${NC}"
fi

# Phase 4: Systemd Service Configuration
echo -e "\n${YELLOW}Phase 4: Configuring Systemd Service${NC}"
echo "===================================="

# Create systemd service file
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=MGA Telegram Bot
Documentation=https://github.com/yourusername/mga-bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$BOT_USER
Group=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$BOT_DIR"
EnvironmentFile=$BOT_DIR/.env

# Start command
ExecStart=$VENV_DIR/bin/python src/telegram_agent_google_http.py

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$BOT_DIR $LOG_DIR

# Logging
StandardOutput=append:$LOG_DIR/bot.log
StandardError=append:$LOG_DIR/bot_error.log

[Install]
WantedBy=multi-user.target
EOF

check_status "Systemd service created"

# Reload systemd
sudo systemctl daemon-reload
check_status "Systemd reloaded"

# Phase 5: Nginx Configuration
echo -e "\n${YELLOW}Phase 5: Configuring Nginx${NC}"
echo "=========================="

# Check for existing Let's Encrypt certificates
CERT_DOMAIN="marcelgladbach.com"
if [ -d "/etc/letsencrypt/live/$CERT_DOMAIN" ]; then
    echo -e "${GREEN}✅ SSL certificates found for $CERT_DOMAIN${NC}"
    SSL_CERT="/etc/letsencrypt/live/$CERT_DOMAIN/fullchain.pem"
    SSL_KEY="/etc/letsencrypt/live/$CERT_DOMAIN/privkey.pem"
else
    echo -e "${YELLOW}⚠️  No SSL certificates found, will create self-signed${NC}"
    SSL_CERT="/etc/ssl/certs/telegram-bot.crt"
    SSL_KEY="/etc/ssl/private/telegram-bot.key"
    
    # Create self-signed certificate
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_KEY" \
        -out "$SSL_CERT" \
        -subj "/C=AT/ST=Tirol/L=Innsbruck/O=Marcel Gladbach/CN=bot.marcelgladbach.com"
fi

# Create nginx configuration
sudo tee "$NGINX_CONFIG" > /dev/null << EOF
# MGA Telegram Bot Configuration
# Managed by: safe_server_deploy.sh
# Created: $(date)

# HTTP redirect
server {
    listen 80;
    server_name bot.marcelgladbach.com;
    
    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name bot.marcelgladbach.com;
    
    # SSL Configuration
    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/bot.mga.at.access.log;
    error_log /var/log/nginx/bot.mga.at.error.log;
    
    # Telegram webhook endpoint
    location /webhook {
        # Only allow Telegram IP ranges
        allow 149.154.160.0/20;
        allow 91.108.4.0/22;
        allow 91.108.56.0/22;
        allow 91.108.12.0/22;
        allow 149.154.164.0/22;
        deny all;
        
        proxy_pass http://127.0.0.1:5000/telegram-webhook;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts for long-polling
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
        
        # Disable buffering for real-time
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # Health check endpoint (no IP restrictions)
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        
        # Don't log health checks
        access_log off;
    }
    
    # Root location - return 404
    location / {
        return 404;
    }
}
EOF

check_status "Nginx configuration created"

# Test nginx configuration
sudo nginx -t
check_status "Nginx configuration valid"

# Enable the site
sudo ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/
check_status "Nginx site enabled"

# Phase 6: Service Startup
echo -e "\n${YELLOW}Phase 6: Starting Services${NC}"
echo "=========================="

# Start the bot service
sudo systemctl start $SERVICE_NAME
sleep 3

# Check if service is running
if systemctl is-active --quiet $SERVICE_NAME; then
    check_status "Bot service started"
else
    echo -e "${RED}❌ Bot service failed to start!${NC}"
    sudo journalctl -u $SERVICE_NAME -n 50
    exit 1
fi

# Enable service for auto-start
sudo systemctl enable $SERVICE_NAME
check_status "Bot service enabled"

# Reload nginx (safer than restart)
sudo systemctl reload nginx
check_status "Nginx reloaded"

# Phase 7: Verification
echo -e "\n${YELLOW}Phase 7: Verification${NC}"
echo "===================="

# Check if bot is responding
if curl -s http://localhost:5000/health | grep -q "ok\|healthy"; then
    check_status "Bot health check passed"
else
    echo -e "${YELLOW}⚠️  Bot health check unclear${NC}"
fi

# Check if all original services are still running
echo -e "\n🔍 Verifying existing services..."
for service in nginx mysql postgresql redis-server umami uptime-kuma; do
    if systemctl is-active --quiet $service 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} $service is still running"
    fi
done

# Display important information
echo -e "\n${GREEN}✨ Deployment Complete!${NC}"
echo "====================="
echo -e "Bot URL: ${YELLOW}https://bot.marcelgladbach.com${NC}"
echo -e "Health: ${YELLOW}https://bot.marcelgladbach.com/health${NC}"
echo -e "Webhook: ${YELLOW}https://bot.marcelgladbach.com/webhook${NC}"
echo ""
echo "📝 Next Steps:"
echo "1. Update DNS to point bot.marcelgladbach.com to 157.90.232.184"
echo "2. Register webhook with Telegram:"
echo "   curl -F \"url=https://bot.marcelgladbach.com/webhook\" https://api.telegram.org/bot\$TOKEN/setWebhook"
echo "3. Add monitoring in Uptime Kuma"
echo "4. Test the bot functionality"
echo ""
echo "🔧 Useful Commands:"
echo "  View logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "  Check status:  sudo systemctl status $SERVICE_NAME"
echo "  Restart bot:   sudo systemctl restart $SERVICE_NAME"
echo "  Nginx logs:    sudo tail -f /var/log/nginx/bot.marcelgladbach.com.*.log"
echo ""
echo "🚨 Rollback:"
echo "  Run: $BOT_DIR/scripts/rollback_deployment.sh"