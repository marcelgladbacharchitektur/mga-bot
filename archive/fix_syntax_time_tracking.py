#!/usr/bin/env python3
# Fix the syntax error in the time tracking bot

import sys

# Read the file
with open(sys.argv[1], 'r') as f:
    content = f.read()

# Fix the problematic line
old_line = 'send_telegram_message(chat_id, f"🚨 **Fehler:** Das Projekt \\"{project_identifier}\\" konnte nicht gefunden werden.\\n\\nBitte geben Sie eine gültige Projektnummer oder einen Namen an.\\n\\n💡 Verfügbare Projekte im Portal anzeigen: [portal.marcelgladbach.com](https://portal.marcelgladbach.com)")'

new_line = 'send_telegram_message(chat_id, f"🚨 **Fehler:** Das Projekt \\"{project_identifier}\\" konnte nicht gefunden werden.\\n\\nBitte geben Sie eine gültige Projektnummer oder einen Namen an.\\n\\n💡 Verfügbare Projekte im Portal anzeigen: [portal.marcelgladbach.com](https://portal.marcelgladbach.com)")'

# Replace with proper escaping
content = content.replace(
    'f"🚨 **Fehler:** Das Projekt \\"{project_identifier}\\" konnte nicht gefunden werden.',
    'f"🚨 **Fehler:** Das Projekt \\"{project_identifier}\\" konnte nicht gefunden werden.'
)

# Write back
with open(sys.argv[1], 'w') as f:
    f.write(content)

print("✅ Fixed syntax error")