#!/bin/bash
# Debug script to check bot status on server

echo "🔍 Debugging Telegram Bot Deployment"
echo "===================================="

# Check if bot files exist
echo -e "\n📁 Checking deployment directory:"
ls -la $1 | grep -E "(telegram_agent_google.py|requirements.txt|.env)"

# Check if .env file exists and has content
echo -e "\n🔐 Checking environment file:"
if [ -f "$1/.env" ]; then
    echo "✅ .env file exists"
    echo "Size: $(wc -c < $1/.env) bytes"
    # Check if required vars are set (without showing values)
    for var in TELEGRAM_BOT_TOKEN GROQ_API_KEY GOOGLE_SERVICE_ACCOUNT_JSON; do
        if grep -q "^$var=" "$1/.env"; then
            echo "✅ $var is set"
        else
            echo "❌ $var is missing"
        fi
    done
else
    echo "❌ .env file not found"
fi

# Check PM2 status
echo -e "\n🔄 PM2 Status:"
pm2 list

# Check if process is running
echo -e "\n📊 Process Details:"
pm2 describe telegram-google || echo "Process not found"

# Check recent logs
echo -e "\n📝 Recent Logs:"
pm2 logs telegram-google --lines 20 --nostream || echo "No logs available"

# Check Python and dependencies
echo -e "\n🐍 Python Environment:"
which python3
python3 --version

# Test if bot script has syntax errors
echo -e "\n✅ Syntax Check:"
cd $1 && python3 -m py_compile telegram_agent_google.py && echo "✅ No syntax errors" || echo "❌ Syntax errors found"

# Check if required Python packages are installed
echo -e "\n📦 Required Packages:"
cd $1
for package in telethon groq google-api-python-client; do
    if python3 -c "import $package" 2>/dev/null; then
        echo "✅ $package is installed"
    else
        echo "❌ $package is missing"
    fi
done