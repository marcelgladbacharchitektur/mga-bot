#!/usr/bin/env python3
"""
Test Shared Drive Integration
"""

import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# Configuration
SHARED_DRIVE_ID = "0ACJnhb0V10tKUk9PVA"
SERVICE_ACCOUNT_FILE = "service-account-key.json"  # You'll need to copy this locally

def test_shared_drive():
    """Test creating a folder in Shared Drive"""
    
    # Initialize Google Drive
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=creds)
    
    # Test folder name
    test_folder = f"WP01-Test-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create folder in Shared Drive
    metadata = {
        'name': test_folder,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [SHARED_DRIVE_ID]
    }
    
    try:
        # CRITICAL: Add supportsAllDrives=True
        folder = service.files().create(
            body=metadata,
            fields='id,name,webViewLink',
            supportsAllDrives=True
        ).execute()
        
        print(f"✅ Success! Folder created in Shared Drive")
        print(f"📁 Name: {folder.get('name')}")
        print(f"🔗 ID: {folder.get('id')}")
        print(f"🌐 Link: {folder.get('webViewLink')}")
        
        # List files in Shared Drive to verify
        print("\n📊 Verifying - Files in Shared Drive:")
        results = service.files().list(
            q=f"'{SHARED_DRIVE_ID}' in parents and mimeType='application/vnd.google-apps.folder'",
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        for file in results.get('files', []):
            print(f"   📁 {file['name']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Shared Drive Integration...")
    print(f"📍 Shared Drive ID: {SHARED_DRIVE_ID}")
    print()
    test_shared_drive()