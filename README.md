# MGA Telegram Bot

Telegram Bot für Architekturbüro Marcel Gladbach mit Google Drive und Supabase Integration.

## Features

- **Projektverwaltung**: Automatische Projektnummerierung und Google Drive Ordnerstruktur
- **Zeiterfassung**: Stunden auf Projekte buchen mit natürlicher Spracheingabe
- **Aufgabenverwaltung**: Tasks mit Prioritäten und Tirol-spezifischen Tags
- **Calendar Integration**: Termine anzeigen und erstellen

## Deployment

Das Deployment erfolgt automatisch über GitHub Actions bei Push auf den `main` Branch.

### Voraussetzungen

1. GitHub Repository Secrets konfigurieren:
   - `TELEGRAM_BOT_TOKEN`
   - `GROQ_API_KEY`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` (Base64-encoded)
   - `GOOGLE_DRIVE_ROOT_FOLDER_ID`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SSH_PRIVATE_KEY`

2. Server-Konfiguration:
   - Python 3.10+
   - PM2 für Prozess-Management
   - SSH-Zugang für GitHub Actions

### Lokale Entwicklung

```bash
# Dependencies installieren
pip install -r requirements.txt

# Umgebungsvariablen setzen
export TELEGRAM_BOT_TOKEN="..."
export GROQ_API_KEY="..."
# etc.

# Tests ausführen
pytest

# Bot starten
python src/telegram_agent_google.py
```

## CI/CD Pipeline

Die Pipeline führt automatisch folgende Schritte aus:

1. **Test**: Führt alle Tests aus
2. **Deploy**: Bei erfolgreichen Tests wird auf den Server deployed
   - Code wird via Git gepullt
   - Dependencies werden aktualisiert
   - Bot wird via PM2 neu gestartet

## Architektur

- **Bot Framework**: Python Telegram Bot mit Flask Webhook
- **AI**: Groq API (Llama 3.3-70b)
- **Cloud Storage**: Google Drive API
- **Calendar**: Google Calendar API
- **Database**: Supabase (PostgreSQL)
- **Deployment**: GitHub Actions + PM2