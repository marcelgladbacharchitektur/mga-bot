#!/bin/bash
# Direct deployment script - runs bot without PM2 complications

echo "🚀 Direct Bot Deployment"
echo "======================="

# SSH into server and run commands
ssh $1@$2 << 'DEPLOY'
set -e

# Navigate to deployment directory
cd $3 || { echo "Cannot find deployment directory $3"; exit 1; }

echo "📁 Current directory: $(pwd)"
echo "📄 Python files found:"
find . -name "*.py" -type f | grep -E "(telegram|bot)" | head -10

# Kill any existing bot process
echo "🔄 Stopping existing bot processes..."
pkill -f "telegram_agent_google.py" || true
pm2 delete telegram-google || true

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Check if bot file exists
if [ -f "src/telegram_agent_google.py" ]; then
    echo "✅ Bot file found at src/telegram_agent_google.py"
elif [ -f "telegram_agent_google.py" ]; then
    echo "✅ Bot file found at telegram_agent_google.py"
    BOT_PATH="telegram_agent_google.py"
else
    echo "❌ Cannot find bot file!"
    exit 1
fi

# Start bot in background with nohup
echo "🤖 Starting bot with nohup..."
nohup python3 ${BOT_PATH:-src/telegram_agent_google.py} > bot.log 2>&1 &

# Wait and check if process started
sleep 5
if pgrep -f "telegram_agent_google.py" > /dev/null; then
    echo "✅ Bot is running!"
    echo "Process ID: $(pgrep -f telegram_agent_google.py)"
else
    echo "❌ Bot failed to start. Checking logs:"
    tail -50 bot.log
fi

# Show webhook info
echo ""
echo "📱 Checking Telegram webhook status..."
if [ -f .env ]; then
    source .env
    curl -s https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo | python3 -m json.tool || echo "Failed to get webhook info"
fi

DEPLOY