# MGA Bot - Quick Fix Steps

## IMMEDIATE SOLUTION - Get Bot Online in 15 Minutes

### Prerequisites
- SSH access to server (157.90.232.184)
- Nginx installed on server
- PM2 installed on server

### Step 1: Upload Fixed Files (On Local Machine)

```bash
# From your local mga-bot directory
cd /path/to/mga-bot

# Upload the HTTP version of the bot
scp src/telegram_agent_google_http.py root@157.90.232.184:/var/www/mga-portal/src/

# Upload nginx config
scp nginx/mga-bot.conf root@157.90.232.184:/tmp/

# Upload deployment script
scp scripts/deploy_nginx_fix.sh root@157.90.232.184:/tmp/
```

### Step 2: Connect to Server

```bash
ssh root@157.90.232.184
```

### Step 3: Run Quick Fix (On Server)

```bash
# Make script executable
chmod +x /tmp/deploy_nginx_fix.sh

# Run the deployment
cd /tmp
./deploy_nginx_fix.sh
```

### Alternative Manual Steps (If Script Fails)

#### 1. Create SSL Certificate
```bash
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/telegram-bot.key \
    -out /etc/nginx/ssl/telegram-bot.crt \
    -subj "/C=AT/ST=Tirol/L=Innsbruck/O=MGA/CN=telegram-bot"
```

#### 2. Setup Nginx
```bash
# Copy nginx config
sudo cp /tmp/mga-bot.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/mga-bot.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. Install Dependencies
```bash
cd /var/www/mga-portal
pip3 install python-dotenv
```

#### 4. Stop Old Bot
```bash
pm2 delete telegram-google || true
pkill -f telegram_agent_google.py || true
```

#### 5. Start New Bot
```bash
cd /var/www/mga-portal
pm2 start src/telegram_agent_google_http.py --name telegram-google --interpreter python3
pm2 save
```

#### 6. Register Webhook
```bash
cd /var/www/mga-portal
export SERVER_HOST="157.90.232.184"
python3 scripts/register_webhook.py
```

### Step 4: Verify Bot is Working

1. Check PM2 status:
```bash
pm2 status
pm2 logs telegram-google --lines 50
```

2. Check health endpoint:
```bash
curl http://localhost:5000/health
```

3. Check webhook:
```bash
curl https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo
```

4. Test in Telegram:
- Open Telegram
- Send message to bot
- Should get immediate response

### Troubleshooting

If bot doesn't respond:

1. Check PM2 logs:
```bash
pm2 logs telegram-google
```

2. Check nginx error log:
```bash
sudo tail -f /var/log/nginx/error.log
```

3. Check if services are running:
```bash
# Check nginx
sudo systemctl status nginx

# Check if bot is listening
netstat -tlnp | grep 5000

# Check if nginx is listening
netstat -tlnp | grep 8443
```

4. Test webhook manually:
```bash
# Get webhook info
curl https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo

# If webhook not set, set it manually:
curl -F "url=https://157.90.232.184:8443/telegram-webhook" \
     https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook
```

### Success Indicators

✅ PM2 shows bot as "online"
✅ Health endpoint returns JSON with "status": "healthy"
✅ Webhook info shows correct URL
✅ Bot responds to messages in Telegram

### Next Steps (After Bot is Online)

1. Monitor for 24 hours
2. Setup proper SSL with Let's Encrypt
3. Add monitoring and alerts
4. Configure log rotation
5. Setup automated backups

## Emergency Rollback

If something goes wrong:

```bash
# Stop new version
pm2 delete telegram-google

# Restore original
cp /var/www/mga-portal/src/telegram_agent_google.py.bak /var/www/mga-portal/src/telegram_agent_google.py

# Try original with workaround
cd /var/www/mga-portal
python3 src/telegram_agent_google.py
```