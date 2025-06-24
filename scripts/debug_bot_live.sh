#!/bin/bash
# Live debugging script for Telegram bot

echo "🔍 LIVE BOT DEBUGGING"
echo "===================="
echo "Run this on the server: ssh root@157.90.232.184"
echo ""

# 1. Check PM2 status
echo "1️⃣ PM2 STATUS:"
pm2 list
echo ""

# 2. Show PM2 logs
echo "2️⃣ PM2 LOGS (last 50 lines):"
pm2 logs telegram-google --lines 50 --nostream
echo ""

# 3. Check if process is running
echo "3️⃣ PROCESS CHECK:"
ps aux | grep -E "telegram_agent_google|python3" | grep -v grep
echo ""

# 4. Check port 5000
echo "4️⃣ PORT 5000 STATUS:"
sudo lsof -i:5000 || echo "Port 5000 is not in use"
echo ""

# 5. Check nginx status
echo "5️⃣ NGINX STATUS:"
sudo nginx -t
ls -la /etc/nginx/sites-enabled/ | grep bot
echo ""

# 6. Test webhook endpoint
echo "6️⃣ WEBHOOK TEST:"
curl -v http://localhost:5000/health 2>&1 | grep -E "HTTP|Connected"
echo ""

# 7. Check .env file
echo "7️⃣ ENVIRONMENT CHECK:"
cd /var/www/mga-portal
if [ -f .env ]; then
    echo "✅ .env exists with $(wc -l < .env) lines"
    grep -E "TELEGRAM_BOT_TOKEN|GROQ_API_KEY" .env | sed 's/=.*/=***/'
else
    echo "❌ .env file missing!"
fi
echo ""

# 8. Check Telegram webhook status
echo "8️⃣ TELEGRAM WEBHOOK STATUS:"
if [ -f .env ]; then
    source .env
    curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool | grep -E "url|pending_update_count|last_error"
fi
echo ""

# 9. Try to run bot manually
echo "9️⃣ MANUAL BOT TEST (10 second timeout):"
cd /var/www/mga-portal
timeout 10 python3 src/telegram_agent_google_http.py 2>&1 | head -30
echo ""

# 10. Check nginx logs
echo "🔟 NGINX LOGS:"
sudo tail -20 /var/log/nginx/error.log | grep -E "bot|5000"
sudo tail -20 /var/log/nginx/access.log | grep telegram-webhook
echo ""

echo "📋 COMMON ISSUES:"
echo "- If port 5000 shows nothing, bot isn't running"
echo "- If .env is missing, credentials aren't loaded"
echo "- If webhook URL is wrong, bot won't receive messages"
echo "- If PM2 shows 'errored', check the logs above"