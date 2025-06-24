#!/usr/bin/env python3
"""
Local test script to verify if required environment variables are set.
This helps test the deployment setup locally.
"""

import os
import json
import sys
from typing import Dict, Tuple

def check_env_var(name: str) -> Tuple[bool, str]:
    """Check if an environment variable is set and return status."""
    value = os.environ.get(name, "")
    if not value:
        return False, "NOT SET"
    
    # Show partial value for security
    length = len(value)
    if length > 6:
        partial = f"{value[:3]}...{value[-3:]} (length: {length})"
    else:
        partial = f"(length: {length})"
    
    return True, partial

def validate_json(json_str: str) -> bool:
    """Validate if a string is valid JSON."""
    try:
        json.loads(json_str)
        return True
    except:
        return False

def main():
    print("🔍 Testing Environment Variables Configuration")
    print("=" * 45)
    
    # Define required secrets
    secrets = {
        "Telegram Configuration": ["TELEGRAM_BOT_TOKEN"],
        "API Keys": ["GROQ_API_KEY"],
        "Google Configuration": ["GOOGLE_SERVICE_ACCOUNT_JSON", "GOOGLE_DRIVE_ROOT_FOLDER_ID"],
        "Supabase Configuration": ["SUPABASE_URL", "SUPABASE_ANON_KEY"],
        "SSH Configuration": ["SSH_PRIVATE_KEY", "SSH_HOST", "SSH_USER", "TARGET_DIR"]
    }
    
    all_set = True
    results: Dict[str, Dict[str, Tuple[bool, str]]] = {}
    
    # Check each category
    for category, vars in secrets.items():
        print(f"\n📋 {category}:")
        results[category] = {}
        
        for var in vars:
            is_set, info = check_env_var(var)
            results[category][var] = (is_set, info)
            
            if is_set:
                print(f"  ✅ {var}: {info}")
            else:
                print(f"  ❌ {var}: {info}")
                all_set = False
    
    # Additional validations
    print("\n📋 Additional Validations:")
    
    # Validate JSON
    google_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if google_json:
        if validate_json(google_json):
            print("  ✅ GOOGLE_SERVICE_ACCOUNT_JSON is valid JSON")
        else:
            print("  ⚠️  GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON")
    
    # Validate SSH_HOST format
    ssh_host = os.environ.get("SSH_HOST", "")
    if ssh_host:
        import re
        if re.match(r'^[a-zA-Z0-9.-]+$', ssh_host):
            print("  ✅ SSH_HOST format looks valid")
        else:
            print("  ⚠️  SSH_HOST format might be invalid")
    
    # Validate TARGET_DIR
    target_dir = os.environ.get("TARGET_DIR", "")
    if target_dir:
        if target_dir.startswith("/"):
            print("  ✅ TARGET_DIR is an absolute path")
        else:
            print("  ⚠️  TARGET_DIR should be an absolute path")
    
    # Summary
    print("\n" + "=" * 45)
    if all_set:
        print("✅ All environment variables are set!")
        print("\nTo test the deployment workflow:")
        print("1. Commit and push these changes")
        print("2. Go to Actions tab in GitHub")
        print("3. Run the 'Test Secrets Configuration' workflow")
        return 0
    else:
        print("❌ Some environment variables are missing!")
        print("\nTo set them locally, create a .env file or export them:")
        print("export VARIABLE_NAME='value'")
        return 1

if __name__ == "__main__":
    sys.exit(main())