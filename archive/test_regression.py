#!/usr/bin/env python3
"""
Regression test for WP-07
Tests that CREATE_PROJECT functionality still works after calendar implementation
"""

import requests
import json

# Test CREATE_PROJECT
webhook_url = "https://portal.marcelgladbach.com/telegram-webhook"

test_message = {
    "message": {
        "text": "Neues Projekt Testhaus Innsbruck",
        "chat": {"id": 123456789},
        "from": {"first_name": "Test", "id": 987654321}
    }
}

print("Testing CREATE_PROJECT functionality...")
print(f"Sending: {test_message['message']['text']}")

try:
    response = requests.post(webhook_url, json=test_message, timeout=10)
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        print("✅ CREATE_PROJECT test passed - bot responded successfully")
    else:
        print(f"❌ CREATE_PROJECT test failed - status code: {response.status_code}")
except Exception as e:
    print(f"❌ CREATE_PROJECT test failed - error: {e}")