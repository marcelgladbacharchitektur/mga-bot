# 🔍 TELEGRAM BOT DEPLOYMENT DEBUGGING GUIDE

## 📋 Current Situation Analysis

Based on the code review, here are the key findings:

### 1. **Bot Architecture**
- Flask webhook server on port 8443 (HTTPS)
- Self-signed SSL certificate expected
- PM2 process manager for keeping bot alive
- Environment variables loaded from .env file

### 2. **Potential Failure Points Identified**

#### 🔴 **CRITICAL ISSUE: Flask HTTPS/SSL**
The bot is configured to run on port 8443 with Flask's built-in server, but there's **NO SSL CERTIFICATE CONFIGURATION** in the code!

```python
app.run(host='0.0.0.0', port=8443, debug=False)
```

This will fail because:
- Telegram requires HTTPS for webhooks
- Flask's built-in server doesn't handle SSL by default
- No SSL context is being created

## 🛠️ IMMEDIATE DEBUGGING STEPS

### Step 1: Check PM2 Status and Logs

```bash
# SSH into your server first
ssh user@157.90.232.184

# Check PM2 process list
pm2 list

# Check PM2 logs (last 100 lines)
pm2 logs telegram-google --lines 100

# Check PM2 process details
pm2 describe telegram-google

# Monitor real-time logs
pm2 logs telegram-google
```

### Step 2: Test Bot Manually Without PM2

```bash
# Navigate to bot directory
cd /path/to/mga-bot

# Load environment variables
export $(cat .env | xargs)

# Try running the bot directly to see errors
python3 src/telegram_agent_google.py

# If it starts, you'll see startup messages
# If it fails, you'll see the exact error
```

### Step 3: Check Environment Variables

```bash
# Check if .env file exists and has content
ls -la .env
cat .env | grep -E "TELEGRAM_BOT_TOKEN|GROQ_API_KEY"

# Test if variables are loaded
source .env
echo $TELEGRAM_BOT_TOKEN
echo $GROQ_API_KEY
```

### Step 4: Test Python Dependencies

```bash
# Check if all dependencies are installed
python3 -c "import flask, requests, groq, google.oauth2, googleapiclient, supabase"

# If any import fails, reinstall dependencies
pip3 install --user -r requirements.txt

# Check specific versions
pip3 show flask groq google-api-python-client supabase
```

### Step 5: Network and Port Testing

```bash
# Check if port 8443 is open
sudo netstat -tlnp | grep 8443

# Check firewall rules
sudo ufw status
sudo iptables -L -n | grep 8443

# Test if port is accessible from outside
# From your local machine:
curl -k https://157.90.232.184:8443/health
```

### Step 6: Test Webhook Registration

```bash
# Check current webhook status
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo

# The response should show your webhook URL
# Look for errors like "ssl_error" or "wrong_response"
```

## 🔧 FIXING THE SSL/HTTPS ISSUE

### Option 1: Use Gunicorn with SSL (RECOMMENDED)

```bash
# Install gunicorn
pip3 install --user gunicorn

# Create SSL certificates if not exists
mkdir -p /path/to/mga-bot/certs
cd /path/to/mga-bot/certs

# Generate self-signed certificate
openssl req -newkey rsa:2048 -sha256 -nodes -keyout server.key -x509 -days 365 -out server.crt \
  -subj "/C=AT/ST=Tirol/L=Innsbruck/O=MGA/CN=157.90.232.184"

# Update PM2 to use gunicorn
pm2 delete telegram-google
pm2 start "gunicorn --certfile=certs/server.crt --keyfile=certs/server.key --bind 0.0.0.0:8443 src.telegram_agent_google:app" --name telegram-google
pm2 save
```

### Option 2: Modify Bot Code for SSL

Create a new file `src/telegram_agent_google_ssl.py`:

```python
#!/usr/bin/env python3
# At the end of telegram_agent_google.py, replace the last lines with:

if __name__ == '__main__':
    import ssl
    
    # Initialize all services
    init_services()
    
    logger.info("🚀 MGA Telegram Bot starting...")
    logger.info(f"📱 Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    logger.info(f"🧠 AI Provider: Groq (Llama 3.3)")
    logger.info(f"💾 Storage: Google Drive ({GOOGLE_DRIVE_ROOT_FOLDER_ID})")
    logger.info(f"🗄️ Database: Supabase {'✅ Connected' if supabase_client else '❌ Not configured'}")
    logger.info(f"⏱️ Time Tracking: ✅ Enabled")
    logger.info("✅ SSL Webhook ready on port 8443")
    
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('certs/server.crt', 'certs/server.key')
    
    app.run(host='0.0.0.0', port=8443, debug=False, ssl_context=context)
```

### Option 3: Use Reverse Proxy (nginx)

```bash
# Install nginx
sudo apt update
sudo apt install nginx

# Create nginx config
sudo nano /etc/nginx/sites-available/telegram-bot

# Add this configuration:
server {
    listen 8443 ssl;
    server_name 157.90.232.184;

    ssl_certificate /path/to/mga-bot/certs/server.crt;
    ssl_certificate_key /path/to/mga-bot/certs/server.key;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Update bot to run on localhost:5000
# Modify last line in telegram_agent_google.py:
app.run(host='127.0.0.1', port=5000, debug=False)
```

## 📝 COMPLETE DEBUGGING CHECKLIST

Run these commands in order:

```bash
# 1. Check PM2 process
pm2 list
pm2 logs telegram-google --lines 50

# 2. Check Python installation
which python3
python3 --version

# 3. Test imports
cd /path/to/mga-bot
python3 -c "import sys; print(sys.path)"
python3 -c "from src.telegram_agent_google import app; print('Import successful')"

# 4. Check environment
cat .env | wc -l  # Should show number of env vars
source .env && echo $TELEGRAM_BOT_TOKEN | wc -c  # Should be > 10

# 5. Test bot startup
python3 src/telegram_agent_google.py 2>&1 | head -20

# 6. Check network
sudo lsof -i:8443
curl -k https://localhost:8443/health

# 7. Test Telegram API
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe

# 8. Check webhook
python3 scripts/register_webhook.py
```

## 🚨 COMMON ISSUES AND SOLUTIONS

### Issue 1: ImportError
```bash
# Solution: Install missing packages
pip3 install --user flask requests groq google-api-python-client supabase
```

### Issue 2: SSL Error
```bash
# Solution: Create self-signed certificate
openssl req -newkey rsa:2048 -sha256 -nodes -keyout server.key -x509 -days 365 -out server.crt
```

### Issue 3: Port Already in Use
```bash
# Find and kill process using port
sudo lsof -t -i:8443 | xargs kill -9
```

### Issue 4: Environment Variables Not Loading
```bash
# Create proper .env file
nano .env
# Add all required variables
# Then restart PM2
pm2 restart telegram-google --update-env
```

### Issue 5: PM2 Not Finding Python
```bash
# Update PM2 with full python path
pm2 delete telegram-google
pm2 start /path/to/mga-bot/src/telegram_agent_google.py --name telegram-google --interpreter /usr/bin/python3
```

## 🎯 QUICK FIX SCRIPT

Create and run this script on your server:

```bash
#!/bin/bash
# fix_telegram_bot.sh

BOT_DIR="/path/to/mga-bot"
cd $BOT_DIR

echo "🔍 Debugging Telegram Bot..."

# 1. Check PM2
echo "📊 PM2 Status:"
pm2 list
pm2 logs telegram-google --lines 20 --nostream

# 2. Test manual start
echo -e "\n🧪 Testing manual start..."
timeout 5 python3 src/telegram_agent_google.py 2>&1 || true

# 3. Create SSL certificates
echo -e "\n🔐 Creating SSL certificates..."
mkdir -p certs
cd certs
if [ ! -f server.crt ]; then
    openssl req -newkey rsa:2048 -sha256 -nodes -keyout server.key -x509 -days 365 -out server.crt \
        -subj "/C=AT/ST=Tirol/L=Innsbruck/O=MGA/CN=157.90.232.184"
fi
cd ..

# 4. Install gunicorn
echo -e "\n📦 Installing gunicorn..."
pip3 install --user gunicorn

# 5. Restart with gunicorn
echo -e "\n🔄 Restarting with SSL support..."
pm2 delete telegram-google
pm2 start "gunicorn --certfile=certs/server.crt --keyfile=certs/server.key --bind 0.0.0.0:8443 src.telegram_agent_google:app" \
    --name telegram-google \
    --cwd $BOT_DIR
pm2 save

# 6. Register webhook
echo -e "\n🔗 Registering webhook..."
python3 scripts/register_webhook.py

# 7. Test health endpoint
echo -e "\n💓 Testing health endpoint..."
sleep 3
curl -k https://localhost:8443/health

echo -e "\n✅ Debugging complete! Check the output above for issues."
```

## 📊 MONITORING COMMANDS

Once the bot is running:

```bash
# Watch logs in real-time
pm2 logs telegram-google

# Monitor CPU/Memory usage
pm2 monit

# Check bot health
watch -n 5 'curl -k https://localhost:8443/health'

# Check Telegram webhook status
watch -n 60 'curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo | jq .'
```

## 🎯 MOST LIKELY ISSUE

Based on the code analysis, the **#1 most likely issue** is that Flask is trying to run HTTPS on port 8443 without any SSL certificate configuration. The bot will immediately crash when trying to start.

**Immediate fix:**
1. SSH into your server
2. Run: `pm2 logs telegram-google --lines 100`
3. You'll likely see an SSL-related error
4. Implement one of the SSL solutions above (preferably the Gunicorn option)

The deployment workflow looks correct, but the bot itself needs SSL support to handle Telegram's HTTPS webhook requirements.