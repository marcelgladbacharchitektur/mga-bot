#!/usr/bin/env python3
"""
Supabase Configuration for MGA Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase credentials - use environment variables for security
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')

# For testing - you need to set these
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠️  WARNING: Supabase credentials not found in environment variables!")
    print("Please set:")
    print("  export SUPABASE_URL='your-project-url'")
    print("  export SUPABASE_ANON_KEY='your-anon-key'")
    print("")
    print("You can find these in your Supabase project settings:")
    print("1. Go to https://app.supabase.com")
    print("2. Select your project")
    print("3. Go to Settings → API")
    print("4. Copy the Project URL and anon public key")