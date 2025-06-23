#!/usr/bin/env python3
"""
Setup Supabase Schema for MGA Projects
"""
import os
from supabase import create_client
from datetime import datetime

# Get credentials from environment
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ Supabase credentials not found!")
    print("Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
    exit(1)

# Initialize client
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print("🔍 Checking Supabase schema...")

# Check if projects table exists and has required columns
try:
    # Try to select from projects table
    result = supabase.table('projects').select('*').limit(1).execute()
    print("✅ Projects table exists")
    
    # Check columns by inserting a test record
    test_data = {
        'name': 'SCHEMA_TEST_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
        'drive_folder_id': 'test_id_123',
        'drive_folder_link': 'https://drive.google.com/test'
    }
    
    # Try to insert
    try:
        result = supabase.table('projects').insert(test_data).execute()
        print("✅ All required columns exist")
        
        # Clean up test record
        if result.data:
            supabase.table('projects').delete().eq('id', result.data[0]['id']).execute()
            print("✅ Test record cleaned up")
            
    except Exception as e:
        if 'drive_folder_link' in str(e):
            print("⚠️  Column 'drive_folder_link' is missing")
            print("")
            print("Please add this column to your projects table:")
            print("1. Go to your Supabase dashboard")
            print("2. Navigate to Table Editor → projects")
            print("3. Click 'Add column'")
            print("4. Name: drive_folder_link")
            print("5. Type: text")
            print("6. Click 'Save'")
        else:
            print(f"❌ Error checking schema: {e}")
            
except Exception as e:
    if 'projects' in str(e) and 'not found' in str(e):
        print("❌ Projects table does not exist!")
        print("")
        print("Please create the table with these columns:")
        print("- id (uuid, primary key)")
        print("- created_at (timestamp)")
        print("- name (text)")
        print("- drive_folder_id (text)")
        print("- drive_folder_link (text)")
    else:
        print(f"❌ Error: {e}")

print("\n📊 Schema check complete!")