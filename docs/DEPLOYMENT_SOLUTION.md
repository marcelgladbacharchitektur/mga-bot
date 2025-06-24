# MGA Bot Deployment Solution

## Problem Analysis

The Telegram bot fails to start because:
1. Flask's development server (`app.run()`) doesn't support SSL/HTTPS
2. Telegram webhooks require HTTPS with valid SSL certificates
3. Port 8443 is expected to serve HTTPS but the Python app serves HTTP

## Solutions Overview

### 1. IMMEDIATE FIX - Nginx Reverse Proxy (Recommended)
**Time to implement: 15 minutes**

Use nginx as a reverse proxy to handle SSL termination:
- Bot runs on HTTP port 5000 (localhost only)
- Nginx handles SSL on port 8443
- Nginx proxies HTTPS requests to HTTP backend

**Pros:**
- Quick to implement
- Production-ready
- Handles SSL properly
- Can add rate limiting, caching, etc.

**Cons:**
- Requires nginx installation
- One more service to manage

### 2. Python SSL with Gunicorn
**Time to implement: 30 minutes**

Use Gunicorn with SSL certificates:
```bash
gunicorn --certfile=/path/to/cert.pem --keyfile=/path/to/key.pem \
         --bind 0.0.0.0:8443 src.telegram_agent_google:app
```

**Pros:**
- No additional services needed
- Python-native solution

**Cons:**
- Gunicorn SSL support is basic
- Not recommended for production

### 3. Use Polling Instead of Webhooks
**Time to implement: 1 hour**

Rewrite bot to use long polling:
```python
from telegram.ext import Application, CommandHandler, MessageHandler, filters

async def start(update, context):
    await update.message.reply_text('Hello!')

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
```

**Pros:**
- No SSL needed
- Works behind firewalls
- Simpler deployment

**Cons:**
- Higher latency
- More resource usage
- Not scalable

### 4. Use Cloudflare Tunnel
**Time to implement: 45 minutes**

Use Cloudflare's free tunnel service:
```bash
cloudflared tunnel --url http://localhost:5000
```

**Pros:**
- Free SSL
- No port forwarding needed
- DDoS protection

**Cons:**
- Dependency on Cloudflare
- Additional latency

## Recommended Implementation Steps

### Step 1: Deploy HTTP Version
```bash
# Copy the HTTP version to server
scp src/telegram_agent_google_http.py user@server:/var/www/mga-portal/src/

# SSH to server
ssh user@server
```

### Step 2: Setup Nginx
```bash
# Install nginx if not already installed
sudo apt-get update
sudo apt-get install nginx

# Create SSL certificate
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/telegram-bot.key \
    -out /etc/nginx/ssl/telegram-bot.crt \
    -subj "/C=AT/ST=Tirol/L=Innsbruck/O=MGA/CN=telegram-bot"

# Copy nginx config
sudo cp nginx/mga-bot.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/mga-bot.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 3: Run Bot with PM2
```bash
# Stop old process
pm2 delete telegram-google

# Start new HTTP version
pm2 start src/telegram_agent_google_http.py --name telegram-google --interpreter python3
pm2 save
```

### Step 4: Register Webhook
```bash
cd /var/www/mga-portal
python3 scripts/register_webhook.py
```

## Alternative: Systemd Service

Create `/etc/systemd/system/mga-bot.service`:
```ini
[Unit]
Description=MGA Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/mga-portal
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/var/www/mga-portal/.env
ExecStart=/usr/bin/python3 /var/www/mga-portal/src/telegram_agent_google_http.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mga-bot
sudo systemctl start mga-bot
sudo systemctl status mga-bot
```

## Monitoring

### Check Bot Status
```bash
# PM2
pm2 status
pm2 logs telegram-google

# Systemd
sudo systemctl status mga-bot
sudo journalctl -u mga-bot -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Bot health
curl http://localhost:5000/health
```

### Test Webhook
```bash
# Check webhook info
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo

# Send test message
curl -X POST https://SERVER_IP:8443/telegram-webhook \
     -H "Content-Type: application/json" \
     -d '{"message": {"chat": {"id": 123}, "text": "test"}}'
```

## Troubleshooting

### Bot not responding
1. Check PM2 logs: `pm2 logs telegram-google`
2. Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Test health endpoint: `curl http://localhost:5000/health`
4. Check webhook: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

### SSL errors
1. Check certificate: `openssl x509 -in /etc/nginx/ssl/telegram-bot.crt -text`
2. Test SSL: `openssl s_client -connect SERVER_IP:8443`
3. Check nginx config: `sudo nginx -t`

### Port conflicts
1. Check what's using port: `sudo lsof -i :8443` or `sudo lsof -i :5000`
2. Kill process: `sudo kill -9 <PID>`

## Security Considerations

1. **Firewall**: Only allow port 8443 from Telegram IPs
2. **Rate limiting**: Add to nginx config
3. **Environment variables**: Never commit .env file
4. **SSL**: Use Let's Encrypt for production
5. **Updates**: Keep dependencies updated

## Production Recommendations

1. Use Let's Encrypt for SSL:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

2. Add monitoring with Prometheus/Grafana
3. Setup log rotation
4. Use Redis for caching
5. Implement health checks
6. Setup backup strategy