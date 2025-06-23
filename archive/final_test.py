#!/usr/bin/env python3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

creds = service_account.Credentials.from_service_account_file(
    "service-account-key.json",
    scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=creds)

# Correct Shared Drive from test
SHARED_DRIVE_ID = "0ADxsi_12PIVhUk9PVA"

# Create test folder
metadata = {
    "name": f"WP01-Test-{datetime.now().strftime('%H%M%S')}",
    "mimeType": "application/vnd.google-apps.folder",
    "parents": [SHARED_DRIVE_ID]
}

try:
    folder = service.files().create(
        body=metadata,
        supportsAllDrives=True,
        fields="id,name,webViewLink"
    ).execute()
    print(f"✅ SUCCESS! Folder created in Shared Drive 'MGA'")
    print(f"📁 Name: {folder.get('name')}")
    print(f"🔗 Link: {folder.get('webViewLink')}")
    print(f"\n✨ The bot can now create projects in the Shared Drive!")
except Exception as e:
    print(f"❌ Error: {e}")