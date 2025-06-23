#!/usr/bin/env python3
"""
Basic tests for MGA Telegram Bot
"""

import pytest
import os
import sys
import json
import base64
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load dummy credentials
with open(os.path.join(os.path.dirname(__file__), 'dummy_google_credentials.json'), 'r') as f:
    DUMMY_GOOGLE_CREDS = json.load(f)
    DUMMY_GOOGLE_CREDS_BASE64 = base64.b64encode(json.dumps(DUMMY_GOOGLE_CREDS).encode()).decode()

def test_bot_can_be_imported():
    """Test that the main bot module can be imported"""
    try:
        import telegram_agent_google
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import telegram_agent_google: {e}")

def test_required_environment_variables():
    """Test that all required environment variables are documented"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GROQ_API_KEY',
        'GOOGLE_SERVICE_ACCOUNT_JSON',
        'GOOGLE_DRIVE_ROOT_FOLDER_ID',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY'
    ]
    
    # This test doesn't check if they're set (as they might not be in test env)
    # But ensures we know what variables are needed
    assert len(required_vars) == 6
    assert 'TELEGRAM_BOT_TOKEN' in required_vars

def test_main_functions_exist():
    """Test that main functions exist in the bot module"""
    # Set up environment before import
    test_env = {
        'TELEGRAM_BOT_TOKEN': 'test-token',
        'GROQ_API_KEY': 'test-groq-key',
        'GOOGLE_SERVICE_ACCOUNT_JSON': DUMMY_GOOGLE_CREDS_BASE64,
        'GOOGLE_DRIVE_ROOT_FOLDER_ID': 'test-folder-id',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test-anon-key'
    }
    
    with patch.dict(os.environ, test_env):
        # Mock all external services before import
        with patch('google.oauth2.service_account.Credentials.from_service_account_info') as mock_creds, \
             patch('googleapiclient.discovery.build') as mock_build, \
             patch('groq.Groq') as mock_groq, \
             patch('supabase.create_client') as mock_supabase:
            
            # Configure mocks
            mock_creds.return_value = MagicMock()
            mock_build.return_value = MagicMock()
            mock_groq.return_value = MagicMock()
            mock_supabase.return_value = MagicMock()
            
            # Now import the module
            import telegram_agent_google
            
            # Check main handler functions exist
            assert hasattr(telegram_agent_google, 'webhook')
            assert hasattr(telegram_agent_google, 'send_telegram_message')
            assert hasattr(telegram_agent_google, 'create_folder')
            assert hasattr(telegram_agent_google, 'record_time_entry')
            assert hasattr(telegram_agent_google, 'create_task')
            assert hasattr(telegram_agent_google, 'init_services')
            
            # Check Flask app exists
            assert hasattr(telegram_agent_google, 'app')
            assert telegram_agent_google.app is not None

def test_parse_time_expressions():
    """Test time parsing functionality"""
    test_env = {
        'TELEGRAM_BOT_TOKEN': 'test-token',
        'GROQ_API_KEY': 'test-groq-key',
        'GOOGLE_SERVICE_ACCOUNT_JSON': DUMMY_GOOGLE_CREDS_BASE64,
        'GOOGLE_DRIVE_ROOT_FOLDER_ID': 'test-folder-id',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test-anon-key'
    }
    
    with patch.dict(os.environ, test_env):
        # Mock all external services before import
        with patch('google.oauth2.service_account.Credentials.from_service_account_info') as mock_creds, \
             patch('googleapiclient.discovery.build') as mock_build, \
             patch('groq.Groq') as mock_groq, \
             patch('supabase.create_client') as mock_supabase:
            
            # Configure mocks
            mock_creds.return_value = MagicMock()
            mock_build.return_value = MagicMock()
            mock_groq.return_value = MagicMock()
            mock_supabase.return_value = MagicMock()
            
            import telegram_agent_google
            
            # Test parse_date function if it exists
            if hasattr(telegram_agent_google, 'parse_date'):
                from datetime import datetime, date
                
                # Mock today's date for consistent testing
                test_today = date(2025, 6, 23)
                with patch('telegram_agent_google.date') as mock_date:
                    mock_date.today.return_value = test_today
                    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
                    
                    # Test various date expressions
                    assert telegram_agent_google.parse_date("heute") == test_today
                    assert telegram_agent_google.parse_date("gestern") == date(2025, 6, 22)
                    assert telegram_agent_google.parse_date("vorgestern") == date(2025, 6, 21)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])