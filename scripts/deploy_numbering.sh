#!/bin/bash
cd /var/www/mga-portal

# Create project counter file
cat > project_counter.json << 'EOF'
{
  "year": 25,
  "counter": 0,
  "last_number": "25-000"
}
EOF

echo "✅ Counter file created"

# Create updated bot file with numbering
cp telegram_agent_google.py telegram_agent_google_numbered.py

# Add import if missing
grep -q "import os" telegram_agent_google_numbered.py || sed -i '1a import os' telegram_agent_google_numbered.py

# Insert numbering code after the PROJECT_FOLDERS definition (around line 50)
cat > numbering_insert.py << 'EOF'

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

EOF

# Find line with PROJECT_FOLDERS and insert after it
line_num=$(grep -n "PROJECT_FOLDERS = \[" telegram_agent_google_numbered.py | cut -d: -f1)
sed -i "${line_num}r numbering_insert.py" telegram_agent_google_numbered.py

# Update the CREATE_PROJECT section
sed -i '/if intent == "CREATE_PROJECT":/,/project_name = ai_result.get/ {
    s/project_name = ai_result.get.*/base_name = ai_result.get("project", "").strip()\
                project_name = format_project_name(base_name)/
}' telegram_agent_google_numbered.py

# Replace original file
mv telegram_agent_google_numbered.py telegram_agent_google.py

# Restart bot
pm2 restart telegram-google

echo "✅ Deployment complete!"
echo ""
echo "📊 Testing project numbering..."
python3 -c "
import json
with open('project_counter.json', 'r') as f:
    data = json.load(f)
    print(f'Current counter: {data}')
"