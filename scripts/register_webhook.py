#!/usr/bin/env python3
"""Register Telegram webhook for the bot"""
import os
import requests
import sys
from dotenv import load_dotenv

load_dotenv()

def register_webhook():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in environment")
        sys.exit(1)
    
    # Use server IP directly since we're using self-signed cert
    server_host = os.getenv('SERVER_HOST', '157.90.232.184')
    webhook_url = f"https://{server_host}:8443/telegram-webhook"
    
    # Get current webhook info
    info_response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
    info = info_response.json()
    print(f"Current webhook info: {info.get('result', {})}")
    
    # Delete existing webhook
    delete_response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
    print(f"Delete webhook: {delete_response.json()}")
    
    # Set new webhook (allow self-signed certificates)
    response = requests.post(
        f"https://api.telegram.org/bot{token}/setWebhook",
        data={
            'url': webhook_url,
            'allowed_updates': ['message', 'callback_query'],
            'drop_pending_updates': True
        }
    )
    
    result = response.json()
    if result.get('ok'):
        print(f"✅ Webhook registered successfully: {webhook_url}")
    else:
        print(f"❌ Failed to register webhook: {result}")
        sys.exit(1)

if __name__ == "__main__":
    register_webhook()