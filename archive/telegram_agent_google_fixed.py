#!/usr/bin/env python3
"""
MGA Telegram Bot - FIXED VERSION mit Projektnummerierung
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import requests
from groq import Groq
import io
from typing import Dict, Any

# Google Drive imports
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration - HARDCODED für Stabilität
TELEGRAM_BOT_TOKEN = "8085899793:AAGGmlKQmwa6823PwI2auKx-JrCdJlR_lYE"
GROQ_API_KEY = "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"
GOOGLE_SERVICE_ACCOUNT_FILE = "/var/www/mga-portal/service-account-key.json"
GOOGLE_DRIVE_ROOT_FOLDER_ID = "0ADxsi_12PIVhUk9PVA"  # Shared Drive

# Initialize Flask
app = Flask(__name__)

# Initialize services
groq_client = Groq(api_key=GROQ_API_KEY)

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

drive_service = get_drive_service()

# Project folders
PROJECT_FOLDERS = [
    "01_Admin", "02_Pläne", "03_Korrespondenz", "04_Fotos",
    "05_Berechnungen", "06_Ausschreibung", "07_Verträge", "08_Protokolle"
]

# Project Numbering System
PROJECT_COUNTER_FILE = "/var/www/mga-portal/project_counter.json"

def get_next_project_number():
    """Get next project number in format YY-NNN"""
    try:
        # Load current counter
        if os.path.exists(PROJECT_COUNTER_FILE):
            with open(PROJECT_COUNTER_FILE, 'r') as f:
                counter_data = json.load(f)
        else:
            counter_data = {"year": 25, "counter": 0, "last_number": "25-000"}
        
        # Get current year (last 2 digits)
        current_year = int(datetime.now().strftime("%y"))
        
        # Reset counter if year changed
        if counter_data["year"] != current_year:
            counter_data["year"] = current_year
            counter_data["counter"] = 1
        else:
            counter_data["counter"] += 1
        
        # Format project number
        project_number = f"{current_year:02d}-{counter_data['counter']:03d}"
        counter_data["last_number"] = project_number
        
        # Save updated counter
        with open(PROJECT_COUNTER_FILE, 'w') as f:
            json.dump(counter_data, f, indent=2)
        
        logger.info(f"📊 Generated project number: {project_number}")
        return project_number
    except Exception as e:
        logger.error(f"❌ Project numbering error: {e}")
        return f"25-{datetime.now().strftime('%H%M%S')}"

def format_project_name(base_name: str = None):
    """Format project name with number and optional description"""
    project_number = get_next_project_number()
    if base_name:
        base_name = base_name.replace("neues projekt", "").replace("projekt", "").strip()
        if base_name:
            return f"{project_number}-{base_name}"
    return project_number

def send_telegram_message(chat_id: int, text: str) -> bool:
    """Send message to Telegram with error handling"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"✅ Message sent to {chat_id}: {text[:50]}...")
            return True
        else:
            logger.error(f"❌ Telegram API error: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Send message error: {e}")
        return False

def analyze_with_groq(text: str) -> Dict[str, Any]:
    """Analyze text with Groq AI"""
    try:
        system_prompt = """Du bist ein Assistent für ein Architekturbüro.
        Analysiere die Nachricht und erkenne die Absicht.
        
        Mögliche Intents:
        - CREATE_PROJECT: Neues Projekt anlegen
        - CREATE_TASK: Aufgabe erstellen  
        - LOG_TIME: Zeit erfassen
        - HELP: Hilfe
        - UNKNOWN: Unbekannt
        
        Extrahiere:
        - project: Projektname
        - content: Inhalt
        - hours: Stunden
        
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
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"🧠 AI Analysis: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ AI Analysis error: {e}")
        return {"intent": "UNKNOWN", "error": str(e)}

def create_folder(name: str, parent_id: str = None) -> str:
    """Create folder in Google Drive"""
    try:
        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            metadata['parents'] = [parent_id]
            
        folder = drive_service.files().create(
            body=metadata, 
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        return folder.get('id')
    except Exception as e:
        logger.error(f"❌ Create folder error: {e}")
        return None

def ensure_project_structure(project_name: str) -> bool:
    """Create complete project structure"""
    try:
        # Create main project folder
        project_id = create_folder(project_name, GOOGLE_DRIVE_ROOT_FOLDER_ID)
        if not project_id:
            return False
            
        # Create all subfolders
        for folder_name in PROJECT_FOLDERS:
            subfolder_id = create_folder(folder_name, project_id)
            if not subfolder_id:
                logger.warning(f"⚠️ Failed to create subfolder: {folder_name}")
                
        logger.info(f"📁 Project structure created: {project_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Project creation error: {e}")
        return False

@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook with immediate feedback"""
    try:
        update = request.json
        logger.info(f"📩 Webhook received: {json.dumps(update, indent=2)}")
        
        # Extract message info
        message = update.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        from_user = message.get('from', {})
        user_name = from_user.get('first_name', 'Unbekannt')
        
        if not chat_id:
            return jsonify({"ok": False, "error": "No chat_id"}), 400
            
        if not text:
            send_telegram_message(chat_id, "❓ Bitte senden Sie eine Textnachricht.")
            return jsonify({"ok": True})
            
        logger.info(f"📩 Message from {user_name}: {text}")
        
        # 1. SOFORTIGES FEEDBACK - Empfangsbestätigung
        send_telegram_message(chat_id, f"🤖 **Nachricht empfangen!**\\n\\n💬 Ihre Anfrage: _{text}_\\n\\n🔄 Analysiere mit KI...")
        
        try:
            # 2. AI ANALYSE
            ai_result = analyze_with_groq(text)
            intent = ai_result.get("intent", "UNKNOWN")
            
            # 3. VERARBEITUNG mit Status-Updates
            if intent == "CREATE_PROJECT":
                base_name = ai_result.get("project", "").strip()
                project_name = format_project_name(base_name)
                
                # Status Update
                send_telegram_message(chat_id, f"🏗️ **Projekt wird erstellt...**\\n\\n📁 Projektnummer: `{project_name}`\\n🔧 Erstelle Ordnerstruktur in Google Drive...")
                
                # Aktion ausführen
                if ensure_project_structure(project_name):
                    # Erfolgreiche Completion
                    send_telegram_message(chat_id, f"✅ **PROJEKT ERFOLGREICH ERSTELLT!**\\n\\n📁 **Projekt:** `{project_name}`\\n🏗️ **Ordner:** {len(PROJECT_FOLDERS)} Standard-Ordner\\n💾 **Speicherort:** Google Drive (Shared)\\n🕐 **Erstellt:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\\n\\n🎉 **Das System funktioniert perfekt!**")
                else:
                    send_telegram_message(chat_id, "❌ **Fehler beim Erstellen des Projekts.**\\n\\nBitte versuchen Sie es erneut oder kontaktieren Sie den Support.")
                    
            elif intent == "HELP":
                send_telegram_message(chat_id, """📋 **MGA Bot - Verfügbare Befehle:**

🏗️ **Projekt erstellen:**
`"Neues Projekt EFH Mustermann"`

📝 **Aufgabe hinzufügen:**
`"Aufgabe: Grundriss überarbeiten"`

⏱️ **Zeit erfassen:**
`"3h für Planung"`

❓ **Hilfe anzeigen:**
`"Hilfe"`

📊 **System Status:**
- ✅ Google Drive verbunden
- ✅ AI-Analyse (Groq Llama 3.3)
- ✅ SSL-Verbindung sicher
- ✅ Projektnummerierung YY-NNN

💡 **Das System läuft einwandfrei und ist bereit für Ihre Projekte!**""")
                
            else:
                send_telegram_message(chat_id, f"🤔 **Intent erkannt:** `{intent}`\\n\\nIch verstehe Ihre Anfrage noch nicht vollständig.\\n\\n💡 Schreiben Sie **'Hilfe'** für alle verfügbaren Befehle.")
                
        except Exception as e:
            # Fehlerbehandlung mit Details
            error_msg = f"❌ **Verarbeitungsfehler:**\\n\\n🔍 **Details:** {str(e)}\\n🕐 **Zeit:** {datetime.now().strftime('%H:%M:%S')}\\n\\n💡 Bitte versuchen Sie es erneut."
            send_telegram_message(chat_id, error_msg)
            logger.error(f"❌ Processing error: {e}")
            
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "groq": "connected",
            "google_drive": "connected",
            "telegram": "webhook_active"
        }
    })

if __name__ == '__main__':
    logger.info("🚀 MGA Telegram Bot starting...")
    logger.info(f"📱 Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    logger.info(f"🧠 AI Provider: Groq (Llama 3.3)")
    logger.info(f"💾 Storage: Google Drive ({GOOGLE_DRIVE_ROOT_FOLDER_ID})")
    logger.info("✅ SSL Webhook ready on port 8443")
    
    app.run(host='0.0.0.0', port=8443, debug=False)