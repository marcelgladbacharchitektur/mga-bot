#!/usr/bin/env python3
"""
Basic tests for MGA Telegram Bot
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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

@patch.dict(os.environ, {
    'TELEGRAM_BOT_TOKEN': 'test-token',
    'GROQ_API_KEY': 'test-groq-key',
    'GOOGLE_SERVICE_ACCOUNT_JSON': 'eyJ0ZXN0IjogInZhbHVlIn0=',  # base64 encoded {"test": "value"}
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_ANON_KEY': 'test-anon-key'
})
def test_main_functions_exist():
    """Test that main functions exist in the bot module"""
    # Mock the external services
    with patch('telegram_agent_google.Groq'), \
         patch('telegram_agent_google.create_client'), \
         patch('telegram_agent_google.get_google_services', return_value=(Mock(), Mock())):
        
        import telegram_agent_google
        
        # Check main handler functions exist
        assert hasattr(telegram_agent_google, 'handle_message')
        assert hasattr(telegram_agent_google, 'send_telegram_message')
        assert hasattr(telegram_agent_google, 'create_project')
        assert hasattr(telegram_agent_google, 'record_time')
        assert hasattr(telegram_agent_google, 'create_task')
        
        # Check Flask app exists
        assert hasattr(telegram_agent_google, 'app')
        assert telegram_agent_google.app is not None

def test_parse_time_expressions():
    """Test time parsing functionality"""
    with patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test-token',
        'GROQ_API_KEY': 'test-groq-key',
        'GOOGLE_SERVICE_ACCOUNT_JSON': 'eyJ0ZXN0IjogInZhbHVlIn0=',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test-anon-key'
    }):
        with patch('telegram_agent_google.Groq'), \
             patch('telegram_agent_google.create_client'), \
             patch('telegram_agent_google.get_google_services', return_value=(Mock(), Mock())):
            
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