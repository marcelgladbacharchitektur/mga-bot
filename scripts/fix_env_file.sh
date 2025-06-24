#!/bin/bash
# Fix the broken .env file

echo "🔧 FIXING .ENV FILE"
echo "=================="

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Create new .env file
cat > .env.fixed << 'EOF'
# Telegram Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Groq API
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE

# Google Service Account - MUST BE BASE64 ENCODED!
GOOGLE_SERVICE_ACCOUNT_JSON=BASE64_ENCODED_JSON_HERE

# Google Drive
GOOGLE_DRIVE_ROOT_FOLDER_ID=YOUR_FOLDER_ID_HERE

# Supabase
SUPABASE_URL=YOUR_SUPABASE_URL_HERE
SUPABASE_ANON_KEY=YOUR_SUPABASE_KEY_HERE
EOF

echo "✅ Template created at .env.fixed"
echo ""
echo "📝 Now you need to:"
echo "1. Get new bot token from @BotFather"
echo "2. Add your GROQ API key"
echo "3. Base64 encode your Google service account JSON:"
echo "   cat service-account.json | base64 -w 0"
echo "4. Update all values in .env.fixed"
echo "5. Replace old .env: mv .env.fixed .env"