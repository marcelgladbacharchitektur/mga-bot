#!/usr/bin/env python3
import json
import os
from datetime import datetime

# Test the numbering function
PROJECT_COUNTER_FILE = "project_counter.json"

def get_next_project_number():
    with open(PROJECT_COUNTER_FILE, 'r') as f:
        counter_data = json.load(f)
    
    current_year = int(datetime.now().strftime("%y"))
    counter_data["counter"] += 1
    
    project_number = f"{current_year:02d}-{counter_data['counter']:03d}"
    counter_data["last_number"] = project_number
    
    with open(PROJECT_COUNTER_FILE, 'w') as f:
        json.dump(counter_data, f, indent=2)
    
    return project_number

# Test generating numbers
print("🧪 Testing project numbering:")
print("   First should be: 25-001")
for i in range(3):
    num = get_next_project_number()
    print(f"   Generated: {num}")

print("\n📊 Final counter state:")
with open(PROJECT_COUNTER_FILE, 'r') as f:
    print(json.dumps(json.load(f), indent=2))