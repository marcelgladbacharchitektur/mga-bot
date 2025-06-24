#!/usr/bin/env python3
"""
Simple bot runner that uses ngrok for HTTPS tunneling
This avoids SSL certificate complexity
"""
import os
import sys
import threading
import time
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def setup_webhook_with_ngrok():
    """Setup webhook using ngrok for HTTPS"""
    try:
        # Start ngrok on port 8080 (HTTP)
        import subprocess
        ngrok_process = subprocess.Popen(['ngrok', 'http', '8080'], 
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
        
        # Wait for ngrok to start
        time.sleep(3)
        
        # Get ngrok public URL
        response = requests.get('http://localhost:4040/api/tunnels')
        tunnels = response.json()['tunnels']
        public_url = None
        
        for tunnel in tunnels:
            if tunnel['proto'] == 'https':
                public_url = tunnel['public_url']
                break
        
        if public_url:
            print(f"✅ Ngrok tunnel created: {public_url}")
            
            # Register webhook with Telegram
            token = os.getenv('TELEGRAM_BOT_TOKEN')
            webhook_url = f"{public_url}/telegram-webhook"
            
            result = requests.post(
                f"https://api.telegram.org/bot{token}/setWebhook",
                data={'url': webhook_url}
            ).json()
            
            print(f"📱 Webhook registration: {result}")
            return True
            
    except Exception as e:
        print(f"❌ Ngrok setup failed: {e}")
        return False

def run_bot_http():
    """Run bot on HTTP (port 8080) with ngrok handling HTTPS"""
    from src.telegram_agent_google import app
    
    # Modify the run configuration
    print("🚀 Starting bot on HTTP port 8080...")
    print("🔧 Ngrok will handle HTTPS tunneling")
    
    # Run on HTTP instead of HTTPS
    app.run(host='0.0.0.0', port=8080, debug=False)

if __name__ == '__main__':
    print("🤖 Simple Bot Runner")
    print("===================")
    
    # Check if ngrok is installed
    try:
        import subprocess
        subprocess.run(['ngrok', 'version'], capture_output=True, check=True)
        print("✅ Ngrok is installed")
    except:
        print("❌ Ngrok not found. Installing...")
        os.system('wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz')
        os.system('tar -xzf ngrok-v3-stable-linux-amd64.tgz')
        os.system('sudo mv ngrok /usr/local/bin/')
        os.system('rm ngrok-v3-stable-linux-amd64.tgz')
    
    # Setup webhook in a separate thread
    webhook_thread = threading.Thread(target=setup_webhook_with_ngrok)
    webhook_thread.start()
    
    # Give ngrok time to start
    time.sleep(5)
    
    # Run the bot
    run_bot_http()