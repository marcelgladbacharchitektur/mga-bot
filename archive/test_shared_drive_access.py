#!/usr/bin/env python3
"""Test Shared Drive Access"""
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration
SHARED_DRIVE_ID = "0ACJnhb0V10tKUk9PVA"
SERVICE_ACCOUNT_FILE = "service-account-key.json"

def test_access():
    # Load service account
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)
    
    print(f"🔍 Testing Shared Drive ID: {SHARED_DRIVE_ID}")
    print()
    
    # Test 1: Get Shared Drive info
    try:
        drive = service.drives().get(driveId=SHARED_DRIVE_ID).execute()
        print(f"✅ Shared Drive found: {drive.get('name')}")
    except Exception as e:
        print(f"❌ Shared Drive access error: {e}")
        if "404" in str(e):
            print("   → Service Account has NO access to this Shared Drive")
            print("   → Solution: Add Service Account to Shared Drive members")
    
    # Test 2: List Shared Drives accessible to Service Account
    try:
        drives = service.drives().list().execute()
        print(f"\n📋 Shared Drives accessible to Service Account:")
        for drive in drives.get('drives', []):
            print(f"   - {drive['name']} (ID: {drive['id']})")
        if not drives.get('drives'):
            print("   ❌ No Shared Drives accessible!")
    except Exception as e:
        print(f"❌ List drives error: {e}")
    
    # Test 3: Try to create in Shared Drive
    try:
        metadata = {
            'name': 'Test-Access-Check',
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [SHARED_DRIVE_ID]
        }
        folder = service.files().create(
            body=metadata,
            supportsAllDrives=True,
            fields='id,name'
        ).execute()
        print(f"\n✅ Write access confirmed! Created: {folder.get('name')}")
        # Clean up
        service.files().delete(fileId=folder['id'], supportsAllDrives=True).execute()
    except Exception as e:
        print(f"\n❌ Cannot create in Shared Drive: {e}")
        if "403" in str(e):
            print("   → Permission denied - Service Account needs Content Manager role")

if __name__ == "__main__":
    test_access()