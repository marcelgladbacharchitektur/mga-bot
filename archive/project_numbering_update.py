#!/usr/bin/env python3
"""
Update Bot with Project Numbering System YY-NNN
Starting with 25-000 for test project
"""

import json
import os
from datetime import datetime

# Project numbering configuration
PROJECT_NUMBERING_CONFIG = '''
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
            # Initialize with test project 25-000
            counter_data = {
                "year": 25,
                "counter": 0,
                "last_number": "25-000"
            }
        
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
        # Fallback to timestamp
        return f"25-{datetime.now().strftime('%H%M%S')}"

def format_project_name(base_name: str = None):
    """Format project name with number and optional description"""
    project_number = get_next_project_number()
    
    if base_name:
        # Clean the base name
        base_name = base_name.replace("neues projekt", "").replace("projekt", "").strip()
        if base_name:
            return f"{project_number}-{base_name}"
    
    return project_number
'''

# Update function for AI analysis
AI_UPDATE = '''
            if intent == "CREATE_PROJECT":
                # Extract base name from AI result
                base_name = ai_result.get("project", "").strip()
                project_name = format_project_name(base_name)
                
                # Status Update
                send_telegram_message(chat_id, f"🏗️ **Projekt wird erstellt...**\\n\\n📁 Projektnummer: `{project_name}`\\n🔧 Erstelle Ordnerstruktur in Google Drive...")
'''

print("📝 Project Numbering Update Script")
print("==================================")
print()
print("This script will update the bot to use YY-NNN numbering:")
print("- Format: YY-NNN (e.g., 25-001, 25-002)")
print("- Starting: 25-000 (test project)")
print("- Auto-increment with persistent counter")
print("- Year rollover support")
print()
print("Add the following code to telegram_agent_google.py:")
print()
print("1. After imports, add:")
print(PROJECT_NUMBERING_CONFIG)
print()
print("2. Update the CREATE_PROJECT handler:")
print(AI_UPDATE)
print()
print("3. Initialize counter file:")
print("""
# Run once to create initial counter
cat > /var/www/mga-portal/project_counter.json << 'EOF'
{
  "year": 25,
  "counter": 0,
  "last_number": "25-000"
}
EOF
""")