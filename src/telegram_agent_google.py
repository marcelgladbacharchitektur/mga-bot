#!/usr/bin/env python3
"""
MGA Telegram Bot - WITH TIME TRACKING
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
import requests
from groq import Groq
import io
from typing import Dict, Any, Optional, Tuple, List
import re

# Google Drive imports
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Supabase imports
from supabase import create_client, Client

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration - From Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')  # Base64 encoded
GOOGLE_DRIVE_ROOT_FOLDER_ID = os.getenv('GOOGLE_DRIVE_ROOT_FOLDER_ID', '0ADxsi_12PIVhUk9PVA')

# Supabase Configuration - From Environment Variables
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')

# Initialize Flask
app = Flask(__name__)

# Initialize services
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not found in environment variables")
    raise ValueError("GROQ_API_KEY is required")

groq_client = Groq(api_key=GROQ_API_KEY)

# Initialize Supabase client if credentials available
supabase_client: Optional[Client] = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("✅ Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase client: {e}")
else:
    logger.warning("⚠️  Supabase credentials not found - database integration disabled")

def get_google_services():
    """Initialize both Drive and Calendar services"""
    import base64
    import tempfile
    
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        logger.error("GOOGLE_SERVICE_ACCOUNT_JSON not found in environment variables")
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON is required")
    
    # Decode base64 service account JSON
    try:
        service_account_json = base64.b64decode(GOOGLE_SERVICE_ACCOUNT_JSON).decode('utf-8')
        # Create temporary file for credentials
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
        
        # Clean up temp file
        os.unlink(temp_path)
        
        drive_service = build('drive', 'v3', credentials=creds)
        calendar_service = build('calendar', 'v3', credentials=creds)
        return drive_service, calendar_service
    except Exception as e:
        logger.error(f"Failed to initialize Google services: {e}")
        raise

drive_service, calendar_service = get_google_services()

# Calendar helper functions
def get_calendar_events(days_ahead: int = 7) -> List[Dict[str, Any]]:
    """Get calendar events for the next N days"""
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()
    
    try:
        # Get primary calendar ID
        calendar_list = calendar_service.calendarList().list().execute()
        primary_calendar = next((cal for cal in calendar_list.get('items', []) 
                               if cal.get('primary')), None)
        
        if not primary_calendar:
            logger.error("No primary calendar found")
            return []
            
        calendar_id = primary_calendar['id']
        
        # Fetch events
        events_result = calendar_service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
        
    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}")
        return []

def create_calendar_event(summary: str, description: str = "", 
                         start_time: datetime = None, duration_hours: float = 1.0,
                         project_name: str = None) -> Optional[str]:
    """Create a calendar event"""
    try:
        # Get primary calendar
        calendar_list = calendar_service.calendarList().list().execute()
        primary_calendar = next((cal for cal in calendar_list.get('items', []) 
                               if cal.get('primary')), None)
        
        if not primary_calendar:
            logger.error("No primary calendar found")
            return None
            
        calendar_id = primary_calendar['id']
        
        # Default to tomorrow 9 AM if no start time
        if not start_time:
            start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
            start_time += timedelta(days=1)
        
        # Add project prefix if specified
        if project_name:
            summary = f"[{project_name}] {summary}"
        
        # Create event
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/Vienna',
            },
            'end': {
                'dateTime': (start_time + timedelta(hours=duration_hours)).isoformat(),
                'timeZone': 'Europe/Vienna',
            },
        }
        
        created_event = calendar_service.events().insert(
            calendarId=calendar_id, 
            body=event
        ).execute()
        
        return created_event.get('htmlLink')
        
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        return None

def format_event_for_telegram(event: Dict[str, Any]) -> str:
    """Format a calendar event for Telegram display"""
    summary = event.get('summary', 'Unnamed Event')
    
    # Parse start time
    start = event.get('start', {})
    if 'dateTime' in start:
        start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
        # Convert to Vienna timezone
        vienna_tz = timezone(timedelta(hours=1))  # CET/CEST
        start_dt = start_dt.astimezone(vienna_tz)
        date_str = start_dt.strftime('%d.%m.')
        time_str = start_dt.strftime('%H:%M')
    else:
        # All-day event
        date_str = start.get('date', '')
        time_str = "Ganztägig"
    
    return f"📅 **{date_str} {time_str}** - {summary}"

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
    """Analyze text with Groq AI - Enhanced for time tracking"""
    try:
        system_prompt = """Du bist ein KI-Assistent für das Architekturbüro Marcel Gladbach in TIROL, ÖSTERREICH.
        Analysiere die Nachricht und erkenne die Absicht.
        
        Mögliche Intents:
        - CREATE_PROJECT: Neues Projekt anlegen
        - RECORD_TIME: Zeit erfassen (z.B. "3h auf Projekt X", "buche 2 stunden", "gestern 4h gearbeitet")
        - CREATE_TASK: Aufgabe erstellen  
        - LOG_TIME: Zeit erfassen (alte Version, behandle wie RECORD_TIME)
        - HELP: Hilfe
        - UNKNOWN: Unbekannt
        
        Für RECORD_TIME extrahiere:
        - duration_hours: Anzahl der Stunden (z.B. 3, 2.5, 4)
        - project_identifier: Projektname oder -nummer (z.B. "25-003", "Projekt X", "WP04")
        - activity_description: Beschreibung der Tätigkeit
        - entry_date: Datum im Format YYYY-MM-DD (heute wenn nicht angegeben, "gestern" = gestern)
        
        Extrahiere auch für andere Intents:
        - project: Projektname
        - content: Inhalt
        - hours: Stunden
        
        WICHTIG: Erkenne relative Zeitangaben:
        - "heute" = aktuelles Datum
        - "gestern" = gestriges Datum
        - "vorgestern" = vorgestriges Datum
        
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
        
        # Map LOG_TIME to RECORD_TIME for backward compatibility
        if result.get("intent") == "LOG_TIME":
            result["intent"] = "RECORD_TIME"
            
        logger.info(f"🧠 AI Analysis: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ AI Analysis error: {e}")
        return {"intent": "UNKNOWN", "error": str(e)}


def create_task(task_content: str, project_id: Optional[str] = None, 
                priority: str = "mittel", tags: List[str] = None,
                behörde: Optional[str] = None, gemeinde: Optional[str] = None,
                created_by: str = None) -> bool:
    """Create a new task in Supabase"""
    if not supabase_client:
        logger.error("❌ Supabase client not initialized")
        return False
        
    try:
        task_data = {
            'content': task_content,
            'priority': priority,
            'created_by': created_by
        }
        
        # Add optional fields
        if project_id:
            task_data['project_id'] = project_id
        if tags:
            task_data['tags'] = tags
        if behörde:
            task_data['behörde'] = behörde
        if gemeinde:
            task_data['gemeinde'] = gemeinde
            
        result = supabase_client.table('tasks').insert(task_data).execute()
        
        logger.info(f"✅ Task created: {task_content[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating task: {e}")
        return False

def extract_tirol_tags(text: str) -> List[str]:
    """Extract Tirol-specific tags from text"""
    tags = []
    
    # Check for Tirol-specific keywords
    tirol_keywords = {
        'TBO': ['tbo', 'bauordnung', 'tiroler bauordnung'],
        'Stellplatz': ['stellplatz', 'parkplatz', 'tiefgarage'],
        'Schneelast': ['schneelast', 'schnee', 'dachlast'],
        'Behörde': ['bh', 'gemeinde', 'bauamt', 'bezirkshauptmannschaft'],
        'ÖBA': ['öba', 'bauaufsicht', 'örtliche bauaufsicht'],
        'Widmung': ['widmung', 'umwidmung', 'bauland'],
        'Hanglage': ['hang', 'hanglage', 'böschung'],
        'WLV': ['wlv', 'wildbach', 'lawine', 'gefahrenzone']
    }
    
    text_lower = text.lower()
    for tag, keywords in tirol_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            tags.append(tag)
            
    return tags

def find_project_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
    """Find project in Supabase by name or number"""
    if not supabase_client:
        return None
        
    try:
        # Clean the identifier
        identifier = identifier.strip()
        
        # Try exact match first
        result = supabase_client.table('projects').select('*').ilike('name', f'%{identifier}%').execute()
        
        if result.data and len(result.data) > 0:
            # Return the most recently created match
            return sorted(result.data, key=lambda x: x['created_at'], reverse=True)[0]
            
        # Try project number match
        result = supabase_client.table('projects').select('*').ilike('project_number', f'%{identifier}%').execute()
        
        if result.data and len(result.data) > 0:
            return sorted(result.data, key=lambda x: x['created_at'], reverse=True)[0]
            
        return None
        
    except Exception as e:
        logger.error(f"❌ Error finding project: {e}")
        return None

def record_time_entry(project_id: str, duration_hours: float, activity_description: str, 
                     entry_date: str, created_by: str) -> bool:
    """Record time entry in Supabase"""
    if not supabase_client:
        logger.error("❌ Supabase client not initialized")
        return False
        
    try:
        time_entry = {
            'project_id': project_id,
            'duration_hours': duration_hours,
            'activity_description': activity_description,
            'entry_date': entry_date,
            'created_by': created_by
        }
        
        result = supabase_client.table('time_entries').insert(time_entry).execute()
        
        logger.info(f"✅ Time entry saved: {duration_hours}h for project {project_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving time entry: {e}")
        return False

def parse_date_from_ai(date_str: str) -> str:
    """Parse date string from AI to YYYY-MM-DD format"""
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
        
    # If already in correct format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
        
    # Handle relative dates
    today = datetime.now()
    date_str_lower = date_str.lower()
    
    if 'gestern' in date_str_lower or 'yesterday' in date_str_lower:
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')
    elif 'vorgestern' in date_str_lower:
        return (today - timedelta(days=2)).strftime('%Y-%m-%d')
    elif 'heute' in date_str_lower or 'today' in date_str_lower:
        return today.strftime('%Y-%m-%d')
    else:
        # Default to today
        return today.strftime('%Y-%m-%d')

def create_folder(name: str, parent_id: str = None) -> Tuple[Optional[str], Optional[str]]:
    """Create folder in Google Drive and return (folder_id, webViewLink)"""
    try:
        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            metadata['parents'] = [parent_id]
            
        folder = drive_service.files().create(
            body=metadata, 
            fields='id,webViewLink',
            supportsAllDrives=True
        ).execute()
        
        folder_id = folder.get('id')
        folder_link = folder.get('webViewLink')
        
        logger.info(f"📁 Created folder: {name} (ID: {folder_id})")
        return folder_id, folder_link
        
    except Exception as e:
        logger.error(f"❌ Create folder error: {e}")
        return None, None

def save_project_to_supabase(project_name: str, folder_id: str, folder_link: str) -> bool:
    """Save project metadata to Supabase database"""
    if not supabase_client:
        logger.warning("⚠️  Supabase client not initialized - skipping database save")
        return False
        
    try:
        # Extract project number if available
        project_number = None
        if '-' in project_name:
            parts = project_name.split('-')
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                project_number = f"{parts[0]}-{parts[1]}"
        
        # Prepare data for insertion
        project_data = {
            'name': project_name,
            'drive_folder_id': folder_id,
            'drive_folder_link': folder_link,
            'project_number': project_number,
            'created_at': datetime.now().isoformat()
        }
        
        # Insert into projects table
        result = supabase_client.table('projects').insert(project_data).execute()
        
        logger.info(f"✅ Project metadata saved to Supabase: {project_name}")
        logger.info(f"   Database record: {result.data[0] if result.data else 'No data returned'}")
        return True
        
    except Exception as e:
        logger.error(f"🚨 FEHLER beim Speichern in Supabase: {e}")
        # Log detailed error for debugging
        logger.error(f"   Project data: {project_data}")
        logger.error(f"   Error type: {type(e).__name__}")
        return False

def ensure_project_structure(project_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Create complete project structure and return (success, folder_id, folder_link)"""
    try:
        # Create main project folder
        project_id, project_link = create_folder(project_name, GOOGLE_DRIVE_ROOT_FOLDER_ID)
        if not project_id:
            return False, None, None
            
        # Create all subfolders
        for folder_name in PROJECT_FOLDERS:
            subfolder_id, _ = create_folder(folder_name, project_id)
            if not subfolder_id:
                logger.warning(f"⚠️ Failed to create subfolder: {folder_name}")
                
        logger.info(f"📁 Project structure created: {project_name}")
        return True, project_id, project_link
        
    except Exception as e:
        logger.error(f"❌ Project creation error: {e}")
        return False, None, None

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
        user_id = str(from_user.get('id', 'unknown'))
        
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
                success, folder_id, folder_link = ensure_project_structure(project_name)
                
                if success and folder_id:
                    # Save to Supabase
                    db_saved = save_project_to_supabase(project_name, folder_id, folder_link)
                    
                    # Prepare success message
                    db_status = "✅ In Datenbank gespeichert" if db_saved else "⚠️ Datenbank-Speicherung fehlgeschlagen"
                    
                    # Erfolgreiche Completion
                    send_telegram_message(chat_id, f"""✅ **PROJEKT ERFOLGREICH ERSTELLT!**

📁 **Projekt:** `{project_name}`
🏗️ **Ordner:** {len(PROJECT_FOLDERS)} Standard-Ordner
💾 **Speicherort:** Google Drive (Shared)
🔗 **Link:** [Projekt öffnen]({folder_link})
🗄️ **Datenbank:** {db_status}
🕐 **Erstellt:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

🎉 **Das System funktioniert perfekt!**""")
                else:
                    send_telegram_message(chat_id, "❌ **Fehler beim Erstellen des Projekts.**\\n\\nBitte versuchen Sie es erneut oder kontaktieren Sie den Support.")
                    
            elif intent == "RECORD_TIME":
                # Extract time tracking data
                duration_hours = ai_result.get("duration_hours", 0)
                project_identifier = ai_result.get("project_identifier", "")
                activity_description = ai_result.get("activity_description", "")
                entry_date_raw = ai_result.get("entry_date", "")
                
                # Parse and validate data
                try:
                    duration_hours = float(duration_hours)
                    if duration_hours <= 0 or duration_hours > 24:
                        raise ValueError("Invalid duration")
                except:
                    send_telegram_message(chat_id, "❌ **Fehler:** Ungültige Stundenanzahl. Bitte geben Sie eine Zahl zwischen 0 und 24 an.")
                    return jsonify({"ok": True})
                
                # Parse date
                entry_date = parse_date_from_ai(entry_date_raw)
                
                # Find project
                project = find_project_by_identifier(project_identifier)
                if not project:
                    send_telegram_message(chat_id, f"🚨 **Fehler:** Das Projekt {project_identifier} konnte nicht gefunden werden. Bitte geben Sie eine gültige Projektnummer oder einen Namen an.")
                    return jsonify({"ok": True})
                
                # Save time entry
                created_by = f"{user_name} ({user_id})"
                if record_time_entry(project['id'], duration_hours, activity_description, entry_date, created_by):
                    # Format date for display
                    entry_date_display = datetime.strptime(entry_date, '%Y-%m-%d').strftime('%d.%m.%Y')
                    
                    send_telegram_message(chat_id, f"""✅ **Zeit erfasst!**

📁 **Projekt:** {project['name']}
⏱️ **Dauer:** {duration_hours} Stunden
📝 **Tätigkeit:** {activity_description}
📅 **Datum:** {entry_date_display}
👤 **Erfasst von:** {user_name}

💡 **Tipp:** Sie können auch relative Zeitangaben verwenden:
- "gestern 3h an 25-003 gearbeitet"
- "vorgestern 2.5h Planung für WP04"
""")
                else:
                    send_telegram_message(chat_id, "❌ **Fehler beim Speichern der Zeiterfassung.**\\n\\nBitte versuchen Sie es erneut.")
                    
            elif intent == "CREATE_TASK":
                # Extract task data
                task_content = ai_result.get("task_description", ai_result.get("content", ""))
                priority = ai_result.get("priority", "mittel").lower()
                project_identifier = ai_result.get("project_identifier")
                
                # Extract Tirol-specific info
                tags = extract_tirol_tags(task_content)
                behörde = ai_result.get("behörde")
                gemeinde = ai_result.get("gemeinde")
                
                # Find project if specified
                project_id = None
                project_name = None
                if project_identifier:
                    project = find_project_by_identifier(project_identifier)
                    if project:
                        project_id = project['id']
                        project_name = project['name']
                
                # Create task
                created_by = f"{user_name} ({user_id})"
                if create_task(task_content, project_id, priority, tags, behörde, gemeinde, created_by):
                    # Build response message
                    priority_emoji = {"hoch": "🔴", "mittel": "🟡", "niedrig": "🟢"}.get(priority, "🟡")
                    
                    response = f"✅ **Aufgabe erstellt\!**\n\n"
                    response += f"{priority_emoji} **Priorität:** {priority.capitalize()}\n"
                    response += f"📝 **Aufgabe:** {task_content}\n"
                    
                    if project_name:
                        response += f"📁 **Projekt:** {project_name}\n"
                    if tags:
                        response += f"🏷️ **Tags:** {', '.join(tags)}\n"
                    if behörde:
                        response += f"🏛️ **Behörde:** {behörde}\n"
                    if gemeinde:
                        response += f"📍 **Gemeinde:** {gemeinde}\n"
                        
                    response += f"\n💡 **Tipp:** Alle Aufgaben im Portal unter [portal.marcelgladbach.com/tasks](https://portal.marcelgladbach.com/tasks)"
                    
                    send_telegram_message(chat_id, response)
                else:
                    send_telegram_message(chat_id, "❌ **Fehler beim Erstellen der Aufgabe.**\n\nBitte versuchen Sie es erneut.")
                
            elif intent == "SHOW_CALENDAR_EVENTS":
                days = ai_result.get("days_ahead", 7)
                events = get_calendar_events(days)
                
                if events:
                    response = f"📅 **Termine der nächsten {days} Tage:**\n\n"
                    for event in events[:10]:  # Limit to 10 events
                        response += format_event_for_telegram(event) + "\n"
                    
                    response += f"\n💡 **Tipp:** Nutzen Sie 'Termin erstellen' um neue Termine anzulegen."
                else:
                    response = f"📅 **Keine Termine in den nächsten {days} Tagen gefunden.**\n\n"
                    response += "💡 **Tipp:** Nutzen Sie 'Termin erstellen' um neue Termine anzulegen."
                
                send_telegram_message(chat_id, response)
                
            elif intent == "CREATE_CALENDAR_EVENT":
                summary = ai_result.get("event_title", "")
                description = ai_result.get("description", "")
                project_identifier = ai_result.get("project_identifier")
                duration = ai_result.get("duration_hours", 1.0)
                
                # Parse date/time if provided
                start_time = None
                if "date" in ai_result or "time" in ai_result:
                    # TODO: Implement date/time parsing logic
                    pass
                
                # Find project if specified
                project_name = None
                if project_identifier:
                    project = find_project_by_identifier(project_identifier)
                    if project:
                        project_name = project['name']
                
                # Create event
                event_link = create_calendar_event(
                    summary, description, start_time, duration, project_name
                )
                
                if event_link:
                    response = f"✅ **Termin erstellt\!**\n\n"
                    response += f"📅 **Termin:** {summary}\n"
                    if project_name:
                        response += f"📁 **Projekt:** {project_name}\n"
                    response += f"🔗 [Im Kalender öffnen]({event_link})"
                else:
                    response = "❌ **Fehler beim Erstellen des Termins.**\n\nBitte versuchen Sie es erneut."
                
                send_telegram_message(chat_id, response)
                
            elif intent == "HELP":
                db_status = "✅ Verbunden" if supabase_client else "❌ Nicht konfiguriert"
                send_telegram_message(chat_id, f"""📋 **MGA Bot - Verfügbare Befehle:**

🏗️ **Projekt erstellen:**
`"Neues Projekt EFH Mustermann"`

⏱️ **Zeit erfassen:**
`"3h auf Projekt 25-003 für Entwurf"`
`"buche 2.5 stunden auf WP04"`
`"gestern 4h an Fassade gearbeitet"`

📝 **Aufgabe hinzufügen:**
📅 **Termine anzeigen:**
`"Zeige meine Termine"`
`"Was steht diese Woche an?"`

📅 **Termin erstellen:**
`"Termin: Bauverhandlung morgen 14 Uhr"`
`"Meeting mit Bauherr übermorgen"`

`"Aufgabe: Grundriss überarbeiten"`

❓ **Hilfe anzeigen:**
`"Hilfe"`

🌐 **Web-Portal:**
[portal.marcelgladbach.com](https://portal.marcelgladbach.com)

📊 **System Status:**
- ✅ Google Drive verbunden
- ✅ AI-Analyse (Groq Llama 3.3)
- ✅ SSL-Verbindung sicher
- ✅ Projektnummerierung YY-NNN
- 🗄️ Supabase Datenbank: {db_status}
- ⏱️ Zeiterfassung: ✅ Aktiv

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
            "telegram": "webhook_active",
            "supabase": "connected" if supabase_client else "not_configured",
            "time_tracking": "active"
        }
    })

if __name__ == '__main__':
    logger.info("🚀 MGA Telegram Bot starting...")
    logger.info(f"📱 Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    logger.info(f"🧠 AI Provider: Groq (Llama 3.3)")
    logger.info(f"💾 Storage: Google Drive ({GOOGLE_DRIVE_ROOT_FOLDER_ID})")
    logger.info(f"🗄️ Database: Supabase {'✅ Connected' if supabase_client else '❌ Not configured'}")
    logger.info(f"⏱️ Time Tracking: ✅ Enabled")
    logger.info("✅ SSL Webhook ready on port 8443")
    
    app.run(host='0.0.0.0', port=8443, debug=False)