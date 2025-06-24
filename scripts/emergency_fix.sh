#!/bin/bash
# Emergency fix script for the server

echo "🚨 EMERGENCY FIX FOR MGA SERVER"
echo "=============================="

# 1. Stop conflicting nginx
echo "1️⃣ Stopping nginx (we use Caddy)..."
sudo systemctl stop nginx
sudo systemctl disable nginx

# 2. Fix PM2
echo "2️⃣ Updating PM2..."
pm2 update

# 3. Stop bot temporarily
echo "3️⃣ Stopping broken bot..."
pm2 stop telegram-google

# 4. Check Caddy config
echo "4️⃣ Current Caddy status:"
sudo systemctl status caddy --no-pager | head -10

# 5. Fix .env file
echo "5️⃣ Creating proper .env template..."
cat > /tmp/env.template << 'EOF'
# IMPORTANT: Each value must be on ONE LINE!
TELEGRAM_BOT_TOKEN=your_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your_project","private_key_id":"your_id","private_key":"-----BEGIN PRIVATE KEY-----\nyour_key_here\n-----END PRIVATE KEY-----\n","client_email":"your_email@project.iam.gserviceaccount.com","client_id":"your_client_id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"your_cert_url"}
GOOGLE_DRIVE_ROOT_FOLDER_ID=your_folder_id_here
SUPABASE_URL=https://your_project.supabase.co
SUPABASE_ANON_KEY=your_supabase_key_here
EOF

echo ""
echo "📋 NEXT STEPS:"
echo "============="
echo "1. Get NEW bot token from @BotFather (old one is invalid)"
echo "2. Edit /tmp/env.template with your actual values"
echo "3. IMPORTANT: Keep Google JSON on ONE LINE!"
echo "4. Copy to production: cp /tmp/env.template /var/www/mga-portal/.env"
echo "5. Restart bot: pm2 restart telegram-google"
echo ""
echo "🔧 For Caddy (not nginx!):"
echo "- Config is usually at: /etc/caddy/Caddyfile"
echo "- Reload: sudo systemctl reload caddy"
echo "- Logs: sudo journalctl -u caddy -f"