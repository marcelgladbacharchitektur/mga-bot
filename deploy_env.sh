#\!/bin/bash
# Deployment script für .env auf bot.marcelgladbach.com

cat << 'ENV_FILE' | ssh root@164.92.224.249 "cat > /var/www/mga-portal/.env"
# MGA Bot Production Environment Variables

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# AI/LLM Configuration  
GROQ_API_KEY=your_groq_api_key_here

# Google Drive Configuration
# WICHTIG: Das JSON muss in EINER ZEILE sein\!
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id","private_key_id":"your-key-id","private_key":"-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n","client_email":"your-service-account@your-project.iam.gserviceaccount.com","client_id":"your-client-id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"your-cert-url"}
GOOGLE_DRIVE_ROOT_FOLDER_ID=your_shared_drive_id_here

# Supabase Database Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Application Configuration
PROJECT_COUNTER_FILE=/var/www/mga-portal/project_counter.json

# Server Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=8443
FLASK_ENV=production
ENV_FILE
