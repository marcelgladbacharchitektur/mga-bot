#!/bin/bash
# Systematic fix following the architect's plan
# Execute each step carefully

echo "🔧 SYSTEMATIC REPAIR PROCEDURE"
echo "=============================="
echo "Following WP-17: Repair environment configuration"
echo ""

# Step 1: Stop conflicting services
echo "Step 1: Stopping conflicting services..."
echo "----------------------------------------"
sudo systemctl stop nginx 2>/dev/null && echo "✅ nginx stopped" || echo "⚠️  nginx was not running"
sudo systemctl disable nginx 2>/dev/null && echo "✅ nginx disabled" || echo "⚠️  nginx already disabled"
pm2 stop telegram-google && echo "✅ Bot stopped" || echo "⚠️  Bot was not running"
echo ""

# Step 2: Backup old .env
echo "Step 2: Backing up current .env..."
echo "-----------------------------------"
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup created"
else
    echo "⚠️  No .env file found"
fi
echo ""

# Step 3: Create template for new .env
echo "Step 3: Creating new .env template..."
echo "-------------------------------------"
cat > .env.template << 'EOF'
# Telegram
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Groq AI
GROQ_API_KEY=YOUR_GROQ_KEY_HERE

# Google (as Base64 - IMPORTANT!)
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=YOUR_BASE64_ENCODED_JSON_HERE

# Google Drive
GOOGLE_DRIVE_ROOT_FOLDER_ID=YOUR_FOLDER_ID_HERE

# Supabase
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_ANON_KEY_HERE
EOF

echo "✅ Template created at .env.template"
echo ""
echo "📝 INSTRUCTIONS:"
echo "1. Get your Google service account JSON file"
echo "2. Encode it to Base64:"
echo "   cat service-account.json | base64 | tr -d '\n' > google_base64.txt"
echo "3. Copy the content of google_base64.txt"
echo "4. Edit .env.template and add all values"
echo "5. Move to production: mv .env.template .env"
echo ""

# Step 4: Check if bot code needs updating
echo "Step 4: Checking bot code..."
echo "-----------------------------"
if grep -q "GOOGLE_SERVICE_ACCOUNT_JSON_BASE64" src/telegram_agent_google.py; then
    echo "✅ Bot already supports Base64 JSON"
else
    echo "⚠️  Bot needs update to support Base64 JSON"
    echo "   See systematic_fix_code.py for the required changes"
fi
echo ""

echo "📋 NEXT STEPS:"
echo "=============="
echo "1. Update .env file with correct values"
echo "2. Test manually: python3 src/telegram_agent_google.py"
echo "3. If successful: pm2 start telegram-google"
echo "4. Check logs: pm2 logs telegram-google"