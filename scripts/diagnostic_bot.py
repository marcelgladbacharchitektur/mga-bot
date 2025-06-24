#!/usr/bin/env python3
"""
Diagnostic version of the bot with extensive logging
This will help us understand exactly what's failing
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_diagnostic.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('DIAGNOSTIC')

def diagnose_environment():
    """Step 1: Check all environment variables"""
    logger.info("="*60)
    logger.info("STARTING DIAGNOSTIC MODE")
    logger.info("="*60)
    
    logger.info("\n1. ENVIRONMENT VARIABLES CHECK:")
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GROQ_API_KEY',
        'GOOGLE_SERVICE_ACCOUNT_JSON',
        'GOOGLE_DRIVE_ROOT_FOLDER_ID',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY'
    ]
    
    env_status = {}
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'TELEGRAM_BOT_TOKEN':
                masked = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "TOO_SHORT"
            elif var == 'GOOGLE_SERVICE_ACCOUNT_JSON':
                try:
                    # Try to parse as JSON
                    parsed = json.loads(value)
                    masked = f"Valid JSON with {len(parsed)} keys"
                except:
                    masked = f"INVALID JSON! Length: {len(value)}"
            else:
                masked = f"SET (length: {len(value)})"
            env_status[var] = masked
            logger.info(f"✅ {var}: {masked}")
        else:
            env_status[var] = "NOT SET"
            logger.error(f"❌ {var}: NOT SET")
    
    return env_status

def test_telegram_connection(token):
    """Step 2: Test Telegram API connection"""
    logger.info("\n2. TELEGRAM API TEST:")
    
    try:
        import requests
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            logger.info(f"✅ Bot connected: @{bot_info.get('username')} ({bot_info.get('first_name')})")
            return True
        else:
            logger.error(f"❌ Telegram API error: {data}")
            return False
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False

def test_groq_connection(api_key):
    """Step 3: Test Groq API connection"""
    logger.info("\n3. GROQ API TEST:")
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        # Simple test
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=10
        )
        
        if response.choices[0].message.content:
            logger.info(f"✅ Groq API working: {response.choices[0].message.content}")
            return True
    except Exception as e:
        logger.error(f"❌ Groq API failed: {e}")
        return False

def test_google_services(json_str):
    """Step 4: Test Google API connection"""
    logger.info("\n4. GOOGLE SERVICES TEST:")
    
    try:
        # First, validate JSON
        service_account = json.loads(json_str)
        logger.info(f"✅ Service account JSON valid: {service_account.get('client_email')}")
        
        # Try to initialize services
        from google.oauth2 import service_account as sa
        from googleapiclient.discovery import build
        
        credentials = sa.Credentials.from_service_account_info(
            service_account,
            scopes=[
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/calendar'
            ]
        )
        
        drive_service = build('drive', 'v3', credentials=credentials)
        calendar_service = build('calendar', 'v3', credentials=credentials)
        
        logger.info("✅ Google services initialized")
        
        # Test Drive access
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.folder'",
            pageSize=1
        ).execute()
        logger.info(f"✅ Drive API working: Can see {len(results.get('files', []))} folders")
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Google services failed: {e}")
        return False

def test_supabase_connection(url, key):
    """Step 5: Test Supabase connection"""
    logger.info("\n5. SUPABASE TEST:")
    
    try:
        from supabase import create_client
        
        supabase = create_client(url, key)
        
        # Test with a simple query
        result = supabase.table('projects').select('id').limit(1).execute()
        logger.info(f"✅ Supabase connected: Found {len(result.data)} projects")
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase failed: {e}")
        return False

def run_full_diagnostic():
    """Run complete diagnostic"""
    
    # Load .env if exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✅ Loaded .env file")
    except Exception as e:
        logger.error(f"❌ Failed to load .env: {e}")
    
    # Step 1: Environment
    env_status = diagnose_environment()
    
    # Step 2: Telegram
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_ok = test_telegram_connection(token) if token else False
    
    # Step 3: Groq
    groq_key = os.getenv('GROQ_API_KEY')
    groq_ok = test_groq_connection(groq_key) if groq_key else False
    
    # Step 4: Google
    google_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    google_ok = test_google_services(google_json) if google_json else False
    
    # Step 5: Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    supabase_ok = test_supabase_connection(supabase_url, supabase_key) if (supabase_url and supabase_key) else False
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("DIAGNOSTIC SUMMARY:")
    logger.info("="*60)
    
    all_ok = all([telegram_ok, groq_ok, google_ok, supabase_ok])
    
    logger.info(f"Telegram API: {'✅ OK' if telegram_ok else '❌ FAILED'}")
    logger.info(f"Groq API: {'✅ OK' if groq_ok else '❌ FAILED'}")
    logger.info(f"Google APIs: {'✅ OK' if google_ok else '❌ FAILED'}")
    logger.info(f"Supabase: {'✅ OK' if supabase_ok else '❌ FAILED'}")
    
    if all_ok:
        logger.info("\n✅ ALL SYSTEMS OPERATIONAL!")
        logger.info("The bot should be able to start successfully.")
    else:
        logger.error("\n❌ SYSTEM FAILURES DETECTED!")
        logger.error("Fix the issues above before starting the bot.")
    
    return all_ok

if __name__ == "__main__":
    success = run_full_diagnostic()
    sys.exit(0 if success else 1)