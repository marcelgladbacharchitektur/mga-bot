#!/bin/bash
# Deployment Script für Shared Drive Update

echo "🚀 MGA Bot Shared Drive Deployment"
echo "=================================="

# Server Details
SERVER="157.90.232.184"
BOT_DIR="/var/www/mga-portal"

echo "📡 Verbinde mit Server $SERVER..."

# SSH Befehle
ssh root@$SERVER << 'ENDSSH'
echo "✅ Verbunden mit Server"
cd /var/www/mga-portal

echo "📝 Erstelle Backup der aktuellen Konfiguration..."
cp telegram_agent_google.py telegram_agent_google.py.backup
cp permanent_config.json permanent_config.json.backup

echo "🔧 Aktualisiere Bot-Code für Shared Drive..."

# Update the bot file with Shared Drive support
cat > shared_drive_update.py << 'EOF'
#!/usr/bin/env python3
import json

# Load current config
with open('permanent_config.json', 'r') as f:
    config = json.load(f)

# Update with Shared Drive ID
config['shared_drive_id'] = '0ACJnhb0V10tKUk9PVA'
config['root_folder_id'] = '0ACJnhb0V10tKUk9PVA'  # Use Shared Drive as root

# Save updated config
with open('permanent_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Config updated with Shared Drive ID")

# Update bot code to add supportsAllDrives parameter
bot_code = open('telegram_agent_google.py', 'r').read()

# Add Shared Drive ID constant after imports
if 'SHARED_DRIVE_ID' not in bot_code:
    bot_code = bot_code.replace(
        'GOOGLE_DRIVE_ROOT_FOLDER_ID = "1T-qVSXOmisTmzVsoR-htTsAzoMHkZ5wR"',
        'GOOGLE_DRIVE_ROOT_FOLDER_ID = "0ACJnhb0V10tKUk9PVA"  # Shared Drive'
    )

# Update create_folder to support Shared Drives
if 'supportsAllDrives' not in bot_code:
    bot_code = bot_code.replace(
        "folder = drive_service.files().create(body=metadata, fields='id').execute()",
        "folder = drive_service.files().create(body=metadata, fields='id', supportsAllDrives=True).execute()"
    )

# Save updated bot
with open('telegram_agent_google.py', 'w') as f:
    f.write(bot_code)

print("✅ Bot code updated with supportsAllDrives parameter")
EOF

python3 shared_drive_update.py

echo "🔄 Neustart des Telegram Bots..."
pm2 restart telegram_agent_google

echo "📊 Bot Status:"
pm2 status telegram_agent_google

echo "📜 Letzte Log-Einträge:"
pm2 logs telegram_agent_google --lines 10 --nostream

echo "✅ Deployment abgeschlossen!"
echo ""
echo "🧪 Testen Sie jetzt mit: 'Neues Projekt WP01-Test'"
echo "📁 Prüfen Sie: https://drive.google.com/drive/u/2/folders/0ACJnhb0V10tKUk9PVA"
ENDSSH