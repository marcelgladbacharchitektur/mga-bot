#!/bin/bash
# Comprehensive server debugging script

echo "🔍 TELEGRAM BOT DEBUGGING"
echo "========================"
echo "Run this script on your server!"
echo ""

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Basic checks
echo "1️⃣ BASIC SYSTEM INFO:"
echo "Current directory: $(pwd)"
echo "Current user: $(whoami)"
echo "Python version: $(python3 --version)"
echo ""

# 2. Check deployment directory
echo "2️⃣ DEPLOYMENT DIRECTORY:"
if [ -z "$1" ]; then
    echo "Usage: ./server_debug.sh /path/to/deployment"
    echo "Please provide deployment path as argument"
    exit 1
fi

DEPLOY_DIR="$1"
cd "$DEPLOY_DIR" || { echo "Cannot access $DEPLOY_DIR"; exit 1; }

echo "Files in deployment directory:"
ls -la
echo ""

# 3. Check Python bot file
echo "3️⃣ BOT FILE CHECK:"
if [ -f "src/telegram_agent_google.py" ]; then
    echo "✅ Bot file exists at src/telegram_agent_google.py"
    echo "File size: $(wc -c < src/telegram_agent_google.py) bytes"
else
    echo "❌ Bot file NOT FOUND at src/telegram_agent_google.py"
    echo "Looking for Python files:"
    find . -name "*.py" -type f | head -20
fi
echo ""

# 4. Check environment file
echo "4️⃣ ENVIRONMENT VARIABLES:"
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    echo "Number of variables: $(grep -c "=" .env)"
    # Check for required vars without showing values
    for var in TELEGRAM_BOT_TOKEN GROQ_API_KEY; do
        if grep -q "^${var}=" .env; then
            echo "✅ $var is set"
        else
            echo "❌ $var is MISSING"
        fi
    done
else
    echo "❌ .env file NOT FOUND!"
fi
echo ""

# 5. PM2 Status
echo "5️⃣ PM2 STATUS:"
if command_exists pm2; then
    pm2 list
    echo ""
    echo "PM2 Logs (last 50 lines):"
    pm2 logs telegram-google --lines 50 --nostream
else
    echo "❌ PM2 is not installed!"
fi
echo ""

# 6. Test Python imports
echo "6️⃣ PYTHON IMPORT TEST:"
cd "$DEPLOY_DIR"
python3 << 'EOF'
import sys
print(f"Python path: {sys.path}")
try:
    import flask
    print("✅ Flask installed")
except ImportError:
    print("❌ Flask NOT installed")

try:
    import groq
    print("✅ Groq installed")
except ImportError:
    print("❌ Groq NOT installed")

try:
    from src.telegram_agent_google import app
    print("✅ Bot imports successfully")
except Exception as e:
    print(f"❌ Bot import failed: {e}")
EOF
echo ""

# 7. Port check
echo "7️⃣ PORT 8443 CHECK:"
if command_exists lsof; then
    sudo lsof -i:8443 || echo "Port 8443 is free"
else
    netstat -tuln | grep 8443 || echo "Port 8443 is free"
fi
echo ""

# 8. Try to run bot directly
echo "8️⃣ DIRECT BOT TEST:"
echo "Attempting to run bot directly (will timeout in 10 seconds)..."
cd "$DEPLOY_DIR"
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi
timeout 10 python3 src/telegram_agent_google.py 2>&1 | head -50
echo ""

# 9. SSL Certificate check
echo "9️⃣ SSL CERTIFICATES:"
if [ -f "certs/server.crt" ]; then
    echo "✅ SSL certificate exists"
    openssl x509 -in certs/server.crt -text -noout | grep -E "(Subject:|Not After)"
else
    echo "❌ No SSL certificate found"
fi
echo ""

# 10. Gunicorn check
echo "🔟 GUNICORN CHECK:"
if pip3 list | grep -q gunicorn; then
    echo "✅ Gunicorn installed"
    # Try gunicorn directly
    echo "Testing gunicorn startup..."
    cd "$DEPLOY_DIR"
    timeout 5 gunicorn --bind 0.0.0.0:8443 src.telegram_agent_google:app 2>&1 | head -20
else
    echo "❌ Gunicorn NOT installed"
fi
echo ""

# Summary and recommendations
echo "📋 SUMMARY & RECOMMENDATIONS:"
echo "============================="
echo "1. If PM2 shows errors, check the logs above"
echo "2. If imports fail, install missing packages: pip3 install -r requirements.txt"
echo "3. If port 8443 is in use, kill the process or use a different port"
echo "4. If SSL certs are missing, the bot can't use HTTPS"
echo "5. Check firewall: sudo ufw status (port 8443 should be open)"
echo ""
echo "To manually test the webhook:"
echo "curl -k https://localhost:8443/telegram-webhook"