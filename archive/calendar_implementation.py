#!/usr/bin/env python3
"""
Calendar Implementation for WP-07
Following Stateful-Context Protocol
"""

# 1. Update get_drive_service to include calendar service
# Replace the existing get_drive_service function (around line 56)

def get_google_services():
    """Initialize both Drive and Calendar services"""
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=[
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/calendar'
        ]
    )
    drive_service = build('drive', 'v3', credentials=creds)
    calendar_service = build('calendar', 'v3', credentials=creds)
    return drive_service, calendar_service

# Update the initialization (around line 62)
drive_service, calendar_service = get_google_services()

# 2. Add calendar helper functions (insert after get_google_services)

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

# 3. Add new intent handlers (insert before "elif intent == 'HELP'" around line 571)

            elif intent == "SHOW_CALENDAR_EVENTS":
                days = ai_result.get("days_ahead", 7)
                events = get_calendar_events(days)
                
                if events:
                    response = f"📅 **Termine der nächsten {days} Tage:**\\n\\n"
                    for event in events[:10]:  # Limit to 10 events
                        response += format_event_for_telegram(event) + "\\n"
                    
                    response += f"\\n💡 **Tipp:** Nutzen Sie 'Termin erstellen' um neue Termine anzulegen."
                else:
                    response = f"📅 **Keine Termine in den nächsten {days} Tagen gefunden.**\\n\\n"
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
                    response = f"✅ **Termin erstellt!**\\n\\n"
                    response += f"📅 **Termin:** {summary}\\n"
                    if project_name:
                        response += f"📁 **Projekt:** {project_name}\\n"
                    response += f"🔗 [Im Kalender öffnen]({event_link})"
                else:
                    response = "❌ **Fehler beim Erstellen des Termins.**\\n\\nBitte versuchen Sie es erneut."
                
                send_telegram_message(chat_id, response)

# 4. Update the AI prompt to include calendar intents
# Update system_prompt in analyze_with_groq (around line 143)

UPDATED_SYSTEM_PROMPT = '''Du bist ein KI-Assistent für das Architekturbüro Marcel Gladbach in TIROL, ÖSTERREICH.

KONTEXT:
- Standort: Tirol, Österreich
- Relevante Bauordnung: Tiroler Bauordnung (TBO)
- Typische Projekte: EFH, MFH, Hotels, Almhütten, Sanierungen

TIROLER BEHÖRDEN:
- Gemeinde (Baubehörde)
- BH (Bezirkshauptmannschaft)
- Land Tirol (Abt. Raumordnung)
- WLV (Wildbach- und Lawinenverbauung)

INTENTS:
- CREATE_PROJECT: Neues Projekt (z.B. "Neues Projekt Hotel Sölden")
- RECORD_TIME: Zeit erfassen (z.B. "3h Bauverhandlung Gemeinde")
- CREATE_TASK: Aufgabe erstellen (z.B. "TODO Schneelastberechnung")
- SHOW_CALENDAR_EVENTS: Termine anzeigen (z.B. "Zeige meine Termine", "Was steht diese Woche an?")
- CREATE_CALENDAR_EVENT: Termin erstellen (z.B. "Termin: Bauverhandlung morgen 14 Uhr")
- HELP: Hilfe
- UNKNOWN: Unbekannt

FÜR RECORD_TIME extrahiere:
- duration_hours: Stunden (auch mit Komma: 2,5)
- project_identifier: Projekt-Nr oder Name
- activity_description: Was wurde gemacht
- entry_date: Datum (heute wenn nicht angegeben)

FÜR CREATE_TASK extrahiere:
- task_description: Aufgabenbeschreibung
- priority: hoch/mittel/niedrig (Standard: mittel)
- project_identifier: Projekt wenn angegeben
- behörde: Behörde wenn erwähnt (BH, Gemeinde, etc.)
- gemeinde: Gemeinde wenn erwähnt

FÜR SHOW_CALENDAR_EVENTS extrahiere:
- days_ahead: Anzahl Tage voraus (Standard: 7)

FÜR CREATE_CALENDAR_EVENT extrahiere:
- event_title: Terminbezeichnung
- description: Beschreibung (optional)
- date: Datum (morgen wenn nicht angegeben)
- time: Uhrzeit (9:00 wenn nicht angegeben)
- duration_hours: Dauer in Stunden (Standard: 1)
- project_identifier: Projekt wenn angegeben

TIROLER BEGRIFFE:
- TBO = Tiroler Bauordnung
- ÖBA = Örtliche Bauaufsicht
- Widmung, GFZ, BMZ
- Stellplatznachweis
- Schneelast, Hanglage
- Rote/Gelbe Zone

Antworte im JSON-Format.'''

# 5. Add necessary imports at the top of the file
# Add these to the existing imports (around line 10)
from datetime import timezone