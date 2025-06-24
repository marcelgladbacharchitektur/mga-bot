#!/usr/bin/env python3
"""Test Telegram bot connection and credentials"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_telegram_connection():
    """Test if Telegram credentials are valid and bot is accessible"""
    
    print("🔍 Testing Telegram Bot Connection")
    print("==================================")
    
    # Get bot token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment!")
        print("   Please check your .env file")
        return False
    
    print(f"✅ Token found: {token[:10]}...{token[-5:]}")
    
    # Test 1: Get bot info
    print("\n📱 Testing Bot Info (getMe):")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            print(f"✅ Bot Name: {bot_info.get('first_name')}")
            print(f"✅ Bot Username: @{bot_info.get('username')}")
            print(f"✅ Bot ID: {bot_info.get('id')}")
            print(f"✅ Can join groups: {bot_info.get('can_join_groups', False)}")
            print(f"✅ Can read messages: {bot_info.get('can_read_all_group_messages', False)}")
        else:
            print(f"❌ Bot API Error: {data}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False
    
    # Test 2: Check webhook
    print("\n🔗 Checking Webhook Status:")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
        data = response.json()
        
        if data.get('ok'):
            webhook = data['result']
            url = webhook.get('url', 'Not set')
            pending = webhook.get('pending_update_count', 0)
            last_error = webhook.get('last_error_message', 'None')
            last_error_date = webhook.get('last_error_date', 0)
            
            print(f"📍 Webhook URL: {url}")
            print(f"📊 Pending updates: {pending}")
            print(f"⚠️  Last error: {last_error}")
            if last_error_date:
                from datetime import datetime
                error_time = datetime.fromtimestamp(last_error_date)
                print(f"🕒 Error time: {error_time}")
                
            if url and url != 'Not set':
                print("✅ Webhook is configured")
                
                # Test webhook endpoint
                if 'bot.marcelgladbach.com' in url:
                    print("\n🌐 Testing webhook endpoint:")
                    try:
                        test_response = requests.get(url.replace('/telegram-webhook', '/health'), timeout=5)
                        if test_response.status_code == 200:
                            print("✅ Webhook endpoint is reachable")
                        else:
                            print(f"⚠️  Webhook returned status: {test_response.status_code}")
                    except:
                        print("❌ Cannot reach webhook endpoint")
            else:
                print("❌ No webhook configured!")
                print("\n🔧 To set webhook, run:")
                print(f"   curl -X POST https://api.telegram.org/bot{token}/setWebhook \\")
                print("        -d 'url=https://bot.marcelgladbach.com/telegram-webhook'")
                
        else:
            print(f"❌ Webhook API Error: {data}")
            
    except Exception as e:
        print(f"❌ Webhook Check Error: {e}")
    
    # Test 3: Get recent updates
    print("\n📨 Checking Recent Updates:")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates?limit=5")
        data = response.json()
        
        if data.get('ok'):
            updates = data['result']
            if updates:
                print(f"✅ Found {len(updates)} recent updates")
                for update in updates[-3:]:  # Show last 3
                    if 'message' in update:
                        msg = update['message']
                        print(f"   - From: {msg.get('from', {}).get('username', 'Unknown')}")
                        print(f"     Text: {msg.get('text', 'No text')[:50]}")
            else:
                print("ℹ️  No recent updates (this is normal if webhook is active)")
        else:
            print(f"❌ Updates API Error: {data}")
            
    except Exception as e:
        print(f"❌ Updates Check Error: {e}")
    
    return True

if __name__ == "__main__":
    print("Current directory:", os.getcwd())
    print("Looking for .env file...")
    
    if not os.path.exists('.env'):
        print("❌ No .env file found in current directory!")
        print("   Make sure to run this from the project directory")
        sys.exit(1)
    
    success = test_telegram_connection()
    
    print("\n" + "="*40)
    if success:
        print("✅ Telegram connection is working!")
    else:
        print("❌ Telegram connection has issues!")
        print("\nPossible solutions:")
        print("1. Check if bot token is correct")
        print("2. Make sure bot wasn't deleted in @BotFather")
        print("3. Verify webhook URL is accessible")
        print("4. Check server firewall for port 443/8443")
    
    sys.exit(0 if success else 1)