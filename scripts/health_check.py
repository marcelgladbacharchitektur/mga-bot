#!/usr/bin/env python3
"""Health check script for the Telegram bot"""
import os
import sys
import requests
import subprocess
from dotenv import load_dotenv

load_dotenv()

def check_bot_health():
    """Comprehensive health check for the bot"""
    all_good = True
    
    print("🔍 MGA Bot Health Check")
    print("=" * 40)
    
    # 1. Check environment variables
    print("\n📋 Environment Variables:")
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GROQ_API_KEY', 
        'GOOGLE_SERVICE_ACCOUNT_JSON',
        'GOOGLE_DRIVE_ROOT_FOLDER_ID',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY'
    ]
    
    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ❌ {var}: Missing")
            all_good = False
    
    # 2. Check PM2 process
    print("\n🔄 PM2 Process Status:")
    try:
        result = subprocess.run(['pm2', 'list'], capture_output=True, text=True)
        if 'telegram-google' in result.stdout and 'online' in result.stdout:
            print("  ✅ Bot process is running")
        else:
            print("  ❌ Bot process is not running or errored")
            all_good = False
            # Show PM2 status
            print(result.stdout)
    except Exception as e:
        print(f"  ❌ PM2 check failed: {e}")
        all_good = False
    
    # 3. Check local endpoint
    print("\n🌐 Local Endpoint Check:")
    try:
        response = requests.get('http://localhost:8443/health', timeout=5)
        if response.status_code == 200:
            print("  ✅ Health endpoint responding")
        else:
            print(f"  ❌ Health endpoint returned: {response.status_code}")
            all_good = False
    except Exception as e:
        print(f"  ❌ Cannot reach local endpoint: {e}")
        all_good = False
    
    # 4. Check Telegram webhook
    print("\n📱 Telegram Webhook Status:")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        try:
            response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
            webhook_info = response.json()
            
            if webhook_info.get('ok'):
                result = webhook_info.get('result', {})
                url = result.get('url', 'Not set')
                pending = result.get('pending_update_count', 0)
                last_error = result.get('last_error_message', 'None')
                
                print(f"  📍 URL: {url}")
                print(f"  📊 Pending updates: {pending}")
                print(f"  ⚠️  Last error: {last_error}")
                
                if url and url != 'Not set':
                    print("  ✅ Webhook is configured")
                else:
                    print("  ❌ Webhook not configured")
                    all_good = False
            else:
                print(f"  ❌ Telegram API error: {webhook_info}")
                all_good = False
        except Exception as e:
            print(f"  ❌ Failed to check webhook: {e}")
            all_good = False
    
    # 5. Check bot info
    print("\n🤖 Bot Information:")
    if token:
        try:
            response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
            bot_info = response.json()
            if bot_info.get('ok'):
                bot = bot_info.get('result', {})
                print(f"  📛 Name: {bot.get('first_name')}")
                print(f"  🆔 Username: @{bot.get('username')}")
                print(f"  ✅ Bot token is valid")
            else:
                print(f"  ❌ Invalid bot token")
                all_good = False
        except Exception as e:
            print(f"  ❌ Failed to get bot info: {e}")
            all_good = False
    
    # Summary
    print("\n" + "=" * 40)
    if all_good:
        print("✅ All systems operational!")
        return 0
    else:
        print("❌ Some issues detected. Please check above.")
        return 1

if __name__ == "__main__":
    sys.exit(check_bot_health())