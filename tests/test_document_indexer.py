"""
Tests for document indexing functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from document_indexer import create_text_chunks, get_embedding, index_document

class TestDocumentIndexer:
    """Test cases for document indexing"""
    
    def test_create_text_chunks_basic(self):
        """Test basic text chunking"""
        text = "This is a test. " * 50  # 800 characters
        chunks = create_text_chunks(text, chunk_size=200, overlap=50)
        
        assert len(chunks) > 0
        assert all(len(chunk[0]) <= 300 for chunk in chunks)  # Allow some flexibility
        assert all(isinstance(chunk[1], int) for chunk in chunks)  # Check index
        
    def test_create_text_chunks_sentence_boundary(self):
        """Test chunking respects sentence boundaries"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = create_text_chunks(text, chunk_size=30, overlap=10)
        
        # Should break at sentence boundaries
        assert any(chunk[0].endswith('. ') for chunk in chunks)
        
    def test_create_text_chunks_empty_text(self):
        """Test chunking with empty text"""
        chunks = create_text_chunks("", chunk_size=100, overlap=20)
        assert len(chunks) == 0
        
    @patch('document_indexer.groq_client')
    def test_get_embedding_success(self, mock_groq):
        """Test successful embedding generation"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1024)]
        mock_groq.embeddings.create.return_value = mock_response
        
        result = get_embedding("test text")
        
        assert result is not None
        assert len(result) == 1024
        assert all(isinstance(x, float) for x in result)
        
    @patch('document_indexer.groq_client')
    def test_get_embedding_failure(self, mock_groq):
        """Test embedding generation failure"""
        mock_groq.embeddings.create.side_effect = Exception("API Error")
        
        result = get_embedding("test text")
        assert result is None
        
    @patch('document_indexer.groq_client')
    @patch('document_indexer.supabase_client')
    def test_index_document_success(self, mock_supabase, mock_groq):
        """Test successful document indexing"""
        # Mock embedding response
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=[0.1] * 1024)]
        mock_groq.embeddings.create.return_value = mock_embedding_response
        
        # Mock Supabase insert
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
        
        # Test document
        content = "This is a test document. It has multiple sentences. Each sentence is important."
        
        result = index_document(content, "test.txt", "project-123")
        
        assert result['success'] is True
        assert result['document_name'] == "test.txt"
        assert result['project_id'] == "project-123"
        assert result['total_chunks'] > 0
        assert result['indexed_chunks'] > 0
        assert result['failed_chunks'] == 0
        
    @patch('document_indexer.groq_client', None)
    def test_index_document_no_groq_client(self):
        """Test indexing when Groq client is not initialized"""
        result = index_document("test content", "test.txt", "project-123")
        
        assert result['success'] is False
        assert 'Groq client not initialized' in result['error']
        
    @patch('document_indexer.supabase_client', None)
    def test_index_document_no_supabase_client(self):
        """Test indexing when Supabase client is not initialized"""
        result = index_document("test content", "test.txt", "project-123")
        
        assert result['success'] is False
        assert 'Supabase client not initialized' in result['error']
        
    @patch('document_indexer.groq_client')
    @patch('document_indexer.supabase_client')
    def test_index_document_partial_failure(self, mock_supabase, mock_groq):
        """Test document indexing with some chunks failing"""
        # Mock embedding - fail on second call
        mock_groq.embeddings.create.side_effect = [
            MagicMock(data=[MagicMock(embedding=[0.1] * 1024)]),
            Exception("API Error"),
            MagicMock(data=[MagicMock(embedding=[0.2] * 1024)])
        ]
        
        # Mock Supabase insert
        mock_table = MagicMock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
        
        # Test with content that will create multiple chunks
        content = "First chunk content. " * 30 + "Second chunk content. " * 30 + "Third chunk content. " * 30
        
        result = index_document(content, "test.txt", "project-123")
        
        assert result['success'] is True
        assert result['failed_chunks'] > 0
        assert result['indexed_chunks'] > 0
        
class TestWebhookDocumentHandling:
    """Test document handling in webhook"""
    
    @patch('telegram_agent_google.send_telegram_message')
    @patch('telegram_agent_google.pending_documents', {})
    def test_document_upload_creates_pending(self, mock_send):
        """Test that document upload creates pending entry"""
        from telegram_agent_google import webhook
        
        # Mock Flask request
        with patch('telegram_agent_google.request') as mock_request:
            mock_request.json = {
                'message': {
                    'chat': {'id': 12345},
                    'document': {
                        'file_id': 'doc123',
                        'file_name': 'test.txt'
                    },
                    'from': {'id': 123, 'first_name': 'Test'}
                }
            }
            
            # Import after patching
            from telegram_agent_google import pending_documents
            
            response = webhook()
            
            # Check pending documents
            assert 12345 in pending_documents
            assert pending_documents[12345]['file_id'] == 'doc123'
            assert pending_documents[12345]['file_name'] == 'test.txt'
            
            # Check message sent
            mock_send.assert_called()
            call_args = mock_send.call_args[0]
            assert '📄 **Dokument empfangen:**' in call_args[1]