#!/usr/bin/env python3
"""
Code changes needed to support Base64-encoded Google credentials
Add this to telegram_agent_google.py
"""

# Replace the old get_google_services function with this:
def get_google_services():
    """Initialize and return Google Drive and Calendar service objects"""
    import base64
    import json
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    
    logger.info("Initializing Google services...")
    
    # NEW: Support Base64-encoded credentials
    creds_base64 = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON_BASE64')
    creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if creds_base64:
        # Decode Base64 to JSON
        logger.info("Using Base64-encoded credentials")
        try:
            creds_json_str = base64.b64decode(creds_base64).decode('utf-8')
            creds_info = json.loads(creds_json_str)
            logger.info(f"✅ Decoded credentials for: {creds_info.get('client_email')}")
        except Exception as e:
            logger.error(f"Failed to decode Base64 credentials: {e}")
            raise
    elif creds_json:
        # OLD: Direct JSON string (for backward compatibility)
        logger.warning("Using direct JSON credentials (deprecated)")
        try:
            creds_info = json.loads(creds_json)
        except Exception as e:
            logger.error(f"Failed to parse JSON credentials: {e}")
            raise
    else:
        raise ValueError("Neither GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 nor GOOGLE_SERVICE_ACCOUNT_JSON found")
    
    # Create credentials from the info
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/calendar'
    ]
    
    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=SCOPES
    )
    
    # Build services
    drive_service = build('drive', 'v3', credentials=creds)
    calendar_service = build('calendar', 'v3', credentials=creds)
    
    logger.info("✅ Google services initialized successfully")
    return drive_service, calendar_service

# Also update the init_services function to handle missing GROQ_API_KEY better:
def init_services():
    """Initialize all external services"""
    global groq_client, drive_service, calendar_service, supabase_client
    
    logger.info("Initializing services...")
    
    # Initialize Groq with better error handling
    groq_api_key = os.getenv('GROQ_API_KEY')
    if groq_api_key:
        try:
            groq_client = Groq(api_key=groq_api_key)
            logger.info("✅ Groq client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Groq: {e}")
            groq_client = None
    else:
        logger.error("GROQ_API_KEY not found - AI features will be disabled")
        groq_client = None
    
    # Initialize Google services
    try:
        drive_service, calendar_service = get_google_services()
        logger.info("✅ Google services initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Google services: {e}")
        drive_service = None
        calendar_service = None
    
    # Initialize Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if supabase_url and supabase_key:
        try:
            supabase_client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            supabase_client = None
    else:
        logger.error("Supabase credentials missing")
        supabase_client = None
    
    # Summary
    services_ok = all([
        groq_client is not None,
        drive_service is not None,
        calendar_service is not None,
        supabase_client is not None
    ])
    
    if services_ok:
        logger.info("✅ All services initialized successfully!")
    else:
        logger.warning("⚠️  Some services failed to initialize - bot will run with limited functionality")