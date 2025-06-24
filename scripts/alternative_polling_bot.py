#!/usr/bin/env python3
"""
Alternative MGA Bot using Long Polling (No SSL Required)
This version doesn't need webhooks or HTTPS
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
from google.oauth2 import service_account
from googleapiclient.discovery import build
from supabase import create_client, Client
from dotenv import load_dotenv
import re
from typing import Dict, Any, Optional, List

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
GOOGLE_DRIVE_ROOT_FOLDER_ID = os.getenv('GOOGLE_DRIVE_ROOT_FOLDER_ID', '0ADxsi_12PIVhUk9PVA')
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global services
groq_client = None
supabase_client = None
drive_service = None
calendar_service = None

# Project folders
PROJECT_FOLDERS = [
    "01_Admin", "02_Pläne", "03_Korrespondenz", "04_Fotos",
    "05_Berechnungen", "06_Ausschreibung", "07_Verträge", "08_Protokolle"
]

def init_services():
    """Initialize all external services"""
    global groq_client, supabase_client, drive_service, calendar_service
    
    # Initialize Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
    
    # Initialize Supabase
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        try:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            logger.info("✅ Supabase initialized")
        except Exception as e:
            logger.error(f"❌ Supabase init failed: {e}")
    
    # Initialize Google services
    import base64
    import tempfile
    
    try:
        service_account_json = base64.b64decode(GOOGLE_SERVICE_ACCOUNT_JSON).decode('utf-8')
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(service_account_json)
            temp_path = f.name
        
        creds = service_account.Credentials.from_service_account_file(
            temp_path,
            scopes=[
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/calendar'
            ]
        )
        
        os.unlink(temp_path)
        
        drive_service = build('drive', 'v3', credentials=creds)
        calendar_service = build('calendar', 'v3', credentials=creds)
        logger.info("✅ Google services initialized")
    except Exception as e:
        logger.error(f"❌ Google services init failed: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 **MGA Bot aktiv!**\n\n"
        "Ich bin Ihr persönlicher Assistent für:\n"
        "• 🏗️ Projektverwaltung\n"
        "• ⏱️ Zeiterfassung\n"
        "• 📝 Aufgabenverwaltung\n"
        "• 📅 Terminplanung\n\n"
        "Senden Sie 'Hilfe' für alle Befehle."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    db_status = "✅ Verbunden" if supabase_client else "❌ Nicht konfiguriert"
    help_text = f"""📋 **MGA Bot - Verfügbare Befehle:**

🏗️ **Projekt erstellen:**
`Neues Projekt EFH Mustermann`

⏱️ **Zeit erfassen:**
`3h auf Projekt 25-003 für Entwurf`
`gestern 4h an Fassade gearbeitet`

📝 **Aufgabe hinzufügen:**
`Aufgabe: Grundriss überarbeiten`

📅 **Termine:**
`Zeige meine Termine`
`Termin: Bauverhandlung morgen 14 Uhr`

🌐 **Web-Portal:**
[portal.marcelgladbach.com](https://portal.marcelgladbach.com)

📊 **System Status:**
- ✅ Polling Mode (Kein SSL erforderlich)
- 🗄️ Datenbank: {db_status}
- ⏱️ Zeiterfassung: ✅ Aktiv"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    text = update.message.text
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "Unbekannt"
    user_id = str(update.effective_user.id)
    
    logger.info(f"Message from {user_name}: {text}")
    
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    # Quick feedback
    await update.message.reply_text(
        f"🤖 **Nachricht empfangen!**\n\n"
        f"💬 _Analysiere: {text}_",
        parse_mode='Markdown'
    )
    
    try:
        # Analyze with AI
        ai_result = analyze_with_groq(text)
        intent = ai_result.get("intent", "UNKNOWN")
        
        if intent == "HELP":
            await help_command(update, context)
            
        elif intent == "CREATE_PROJECT":
            await handle_create_project(update, context, ai_result)
            
        elif intent == "RECORD_TIME":
            await handle_record_time(update, context, ai_result, user_name, user_id)
            
        else:
            await update.message.reply_text(
                f"🤔 Ich habe Ihre Anfrage noch nicht verstanden.\n\n"
                f"Senden Sie 'Hilfe' für verfügbare Befehle.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(
            f"❌ **Fehler bei der Verarbeitung**\n\n"
            f"Bitte versuchen Sie es erneut.",
            parse_mode='Markdown'
        )

def analyze_with_groq(text: str) -> Dict[str, Any]:
    """Analyze text with Groq AI"""
    try:
        system_prompt = """Du bist ein KI-Assistent für das Architekturbüro Marcel Gladbach.
        Analysiere die Nachricht und erkenne die Absicht.
        
        Mögliche Intents:
        - CREATE_PROJECT: Neues Projekt anlegen
        - RECORD_TIME: Zeit erfassen
        - CREATE_TASK: Aufgabe erstellen
        - HELP: Hilfe
        - UNKNOWN: Unbekannt
        
        Extrahiere relevante Informationen.
        Antworte im JSON-Format.
        """
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logger.error(f"AI Analysis error: {e}")
        return {"intent": "UNKNOWN", "error": str(e)}

async def handle_create_project(update: Update, context: ContextTypes.DEFAULT_TYPE, ai_result: dict):
    """Handle project creation"""
    # Implementation similar to webhook version
    await update.message.reply_text("🏗️ Projekt wird erstellt...")
    # ... rest of implementation

async def handle_record_time(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           ai_result: dict, user_name: str, user_id: str):
    """Handle time recording"""
    # Implementation similar to webhook version
    await update.message.reply_text("⏱️ Zeit wird erfasst...")
    # ... rest of implementation

def main():
    """Start the bot using polling"""
    # Initialize services
    init_services()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start polling
    logger.info("🚀 Starting MGA Bot in polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()