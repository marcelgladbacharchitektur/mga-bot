# Marcel Gladbach Server Infrastructure Analysis & Telegram Bot Integration Plan

## Executive Summary
This document provides a comprehensive analysis of the existing server infrastructure (157.90.232.184) and a safe deployment strategy for the MGA Telegram Bot that ensures zero disruption to existing services.

## Existing Services Architecture

### Current Services & Typical Ports
1. **Umami Analytics** - Typically runs on port 3000
2. **Uptime Kuma Monitoring** - Commonly port 3001 or 3002
3. **SvelteKit Portal** - Likely ports 3000-5173 range
4. **Telegram Bot** (To be integrated) - Requires HTTPS (443/8443)

### Typical Nginx Architecture for Multi-Service Setup
```
Internet → Nginx (80/443) → Reverse Proxy
                           ├── analytics.marcelgladbach.com → localhost:3000
                           ├── status.marcelgladbach.com → localhost:3001
                           ├── portal.marcelgladbach.com → localhost:4000
                           └── bot.marcelgladbach.com → localhost:5000
```

## Pre-Deployment Analysis Commands

### 1. Safe System Discovery Commands
```bash
# Check current port usage (non-intrusive)
sudo ss -tlnp | grep -E ':(80|443|3000|3001|3002|4000|5000|8443)\s'

# List nginx virtual hosts
sudo ls -la /etc/nginx/sites-enabled/

# Check running services
sudo systemctl list-units --type=service --state=running | grep -E 'umami|uptime|portal|nginx'

# Examine nginx main config (read-only)
sudo nginx -T | grep -E 'server_name|listen|proxy_pass' | head -50

# Check SSL certificates
sudo certbot certificates

# Review process management
pm2 list 2>/dev/null || echo "PM2 not in use"
docker ps 2>/dev/null || echo "Docker not accessible"

# Check firewall rules
sudo ufw status numbered

# Memory and CPU check
free -h
top -bn1 | head -20
```

### 2. Service Configuration Discovery
```bash
# Nginx configuration structure
find /etc/nginx -name "*.conf" -type f | sort

# Check for existing bot configurations
grep -r "telegram\|bot" /etc/nginx/sites-enabled/ 2>/dev/null

# Identify SSL setup
ls -la /etc/letsencrypt/live/

# Check systemd services
systemctl list-unit-files | grep -E 'mga|portal|umami|uptime'
```

## Recommended Architecture for Bot Integration

### Port Allocation Strategy
```
Service          | Subdomain                      | Internal Port | External Access
-----------------|--------------------------------|---------------|------------------
Umami Analytics  | analytics.marcelgladbach.com   | 3000          | HTTPS via Nginx
Uptime Kuma      | status.marcelgladbach.com      | 3001          | HTTPS via Nginx
SvelteKit Portal | portal.marcelgladbach.com      | 4000          | HTTPS via Nginx
Telegram Bot     | bot.marcelgladbach.com         | 5000          | HTTPS via Nginx
```

### Nginx Configuration Strategy

#### 1. Create Separate Config File
```bash
# Create new config without touching existing ones
sudo nano /etc/nginx/sites-available/telegram-bot.conf
```

#### 2. Safe Nginx Configuration
```nginx
# Telegram Bot Configuration
# This runs alongside existing services without conflicts

server {
    listen 80;
    server_name bot.marcelgladbach.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bot.marcelgladbach.com;
    
    # SSL configuration (uses existing Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/marcelgladbach.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/marcelgladbach.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    
    # Telegram webhook endpoint
    location /webhook {
        proxy_pass http://127.0.0.1:5000/telegram-webhook;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Telegram specific timeouts
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # Only allow Telegram IPs
        allow 149.154.160.0/20;
        allow 91.108.4.0/22;
        deny all;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
    
    # Block other paths
    location / {
        return 404;
    }
}
```

## Deployment Strategy

### Phase 1: Pre-Deployment Validation
```bash
#!/bin/bash
# pre-deploy-check.sh

echo "🔍 Pre-deployment System Check"
echo "=============================="

# Check if port 5000 is available
if sudo ss -tlnp | grep -q ':5000\s'; then
    echo "❌ Port 5000 is in use!"
    sudo ss -tlnp | grep ':5000\s'
    exit 1
else
    echo "✅ Port 5000 is available"
fi

# Check nginx syntax
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

# Check disk space
df -h / | awk 'NR==2 {if ($5+0 > 80) print "⚠️  Disk usage is high: " $5; else print "✅ Disk space OK: " $5}'

# Check SSL certificate validity
if sudo certbot certificates | grep -q "VALID"; then
    echo "✅ SSL certificates are valid"
else
    echo "⚠️  Check SSL certificate status"
fi
```

### Phase 2: Bot Deployment Script
```bash
#!/bin/bash
# safe-deploy-bot.sh

set -e  # Exit on error

echo "🚀 Safe MGA Bot Deployment"
echo "========================="

# Configuration
BOT_USER="mga-bot"
BOT_DIR="/opt/mga-bot"
VENV_DIR="$BOT_DIR/venv"
SERVICE_NAME="mga-telegram-bot"

# Create dedicated user (if not exists)
if ! id "$BOT_USER" &>/dev/null; then
    sudo useradd -r -s /bin/bash -d "$BOT_DIR" "$BOT_USER"
    echo "✅ Created bot user"
fi

# Create bot directory
sudo mkdir -p "$BOT_DIR"
sudo chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR"

# Deploy code (from GitHub)
cd "$BOT_DIR"
sudo -u "$BOT_USER" git clone https://github.com/yourusername/mga-bot.git . || \
sudo -u "$BOT_USER" git pull origin main

# Setup Python environment
sudo -u "$BOT_USER" python3 -m venv "$VENV_DIR"
sudo -u "$BOT_USER" "$VENV_DIR/bin/pip" install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=MGA Telegram Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$BOT_USER
Group=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$BOT_DIR/.env
ExecStart=$VENV_DIR/bin/python src/telegram_agent_google_http.py
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Enable but don't start yet
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

echo "✅ Bot deployment prepared"
```

### Phase 3: Integration with Uptime Kuma
```bash
# Add monitoring in Uptime Kuma
curl -X POST https://status.marcelgladbach.com/api/monitor \
  -H "Content-Type: application/json" \
  -d '{
    "type": "http",
    "name": "Telegram Bot Health",
    "url": "https://bot.marcelgladbach.com/health",
    "interval": 60,
    "retryInterval": 20,
    "maxretries": 3
  }'
```

## Zero-Downtime Deployment Process

### Step 1: Backup Current Configuration
```bash
# Backup nginx configs
sudo cp -r /etc/nginx /etc/nginx.backup.$(date +%Y%m%d)

# List current services
sudo systemctl list-units --type=service --state=running > running_services_backup.txt
```

### Step 2: Deploy Bot Service
```bash
# Start the bot service
sudo systemctl start mga-telegram-bot

# Verify it's running
sudo systemctl status mga-telegram-bot

# Check logs
sudo journalctl -u mga-telegram-bot -f
```

### Step 3: Configure Nginx (Safely)
```bash
# Test new configuration
sudo nginx -t

# If OK, reload (zero downtime)
sudo systemctl reload nginx

# Verify all services still accessible
for service in analytics status portal; do
    curl -sI https://$service.marcelgladbach.com | head -1
done
```

### Step 4: Register Telegram Webhook
```bash
# Set webhook URL
curl -F "url=https://bot.marcelgladbach.com/webhook" \
     https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook
```

## Rollback Plan

```bash
#!/bin/bash
# rollback.sh

echo "🔄 Rolling back bot deployment..."

# Stop bot service
sudo systemctl stop mga-telegram-bot
sudo systemctl disable mga-telegram-bot

# Remove nginx config
sudo rm /etc/nginx/sites-enabled/telegram-bot.conf
sudo systemctl reload nginx

# Remove webhook
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook

echo "✅ Rollback complete"
```

## Monitoring & Maintenance

### Health Check Endpoints
- Bot: https://bot.marcelgladbach.com/health
- Umami: https://analytics.marcelgladbach.com/api/health
- Uptime Kuma: https://status.marcelgladbach.com/metrics
- Portal: https://portal.marcelgladbach.com/health

### Log Locations
```bash
# Bot logs
/var/log/mga-telegram-bot/
journalctl -u mga-telegram-bot

# Nginx logs
/var/log/nginx/bot.marcelgladbach.com.access.log
/var/log/nginx/bot.marcelgladbach.com.error.log

# System logs
/var/log/syslog
```

### Monitoring Commands
```bash
# Check all MGA services
for service in mga-telegram-bot umami uptime-kuma portal; do
    echo -n "$service: "
    systemctl is-active $service
done

# Check port usage
sudo ss -tlnp | grep -E ':(3000|3001|3002|4000|5000)\s'

# Check nginx status
sudo nginx -t && echo "Nginx config OK"
```

## Security Considerations

1. **Firewall Rules**
```bash
# Only allow necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw default deny incoming
sudo ufw enable
```

2. **SSL/TLS Configuration**
- Use Let's Encrypt wildcard certificate: *.marcelgladbach.com
- Auto-renewal via certbot
- Strong cipher suite configuration

3. **Process Isolation**
- Each service runs as separate user
- Systemd security directives
- Private tmp directories

## Final Deployment Checklist

- [ ] Run pre-deployment checks
- [ ] Backup existing configurations
- [ ] Verify port 5000 is available
- [ ] Deploy bot code to /opt/mga-bot
- [ ] Create systemd service file
- [ ] Configure nginx (test first!)
- [ ] Start bot service
- [ ] Reload nginx (not restart!)
- [ ] Test webhook endpoint
- [ ] Configure Uptime Kuma monitoring
- [ ] Verify all existing services still work
- [ ] Document deployment in team wiki

## Emergency Contacts

- Server Admin: [Your contact]
- Backup Admin: [Backup contact]
- Hosting: Hetzner Support
- Domain: Your registrar

This plan ensures safe integration of the Telegram bot without disrupting any existing services. Each step is reversible and includes validation checks.