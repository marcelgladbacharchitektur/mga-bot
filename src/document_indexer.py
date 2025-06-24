"""
Document indexing module for RAG pipeline
Handles chunking and embedding of documents
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
import uuid
from datetime import datetime
import numpy as np

# Import required libraries
from groq import Groq
from supabase import create_client, Client

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

# Initialize clients
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
supabase_client: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL and SUPABASE_ANON_KEY else None

# Constants
CHUNK_SIZE = 500  # Characters per chunk
CHUNK_OVERLAP = 100  # Overlap between chunks
EMBEDDING_MODEL = "nomic-embed-text"  # Groq's embedding model
EMBEDDING_DIMENSION = 1024  # Nomic embed dimension

def create_text_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Tuple[str, int]]:
    """
    Split text into overlapping chunks
    Returns list of tuples (chunk_text, chunk_index)
    """
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at a sentence boundary
        if end < len(text):
            # Look for sentence endings
            for delimiter in ['. ', '! ', '? ', '\n\n', '\n']:
                delimiter_pos = text.rfind(delimiter, start, end)
                if delimiter_pos != -1:
                    end = delimiter_pos + len(delimiter)
                    break
        
        chunk = text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append((chunk, chunk_index))
            chunk_index += 1
        
        # Move start position with overlap
        start = end - overlap if end < len(text) else end
    
    logger.info(f"Created {len(chunks)} chunks from text of length {len(text)}")
    return chunks

def get_embedding(text: str) -> Optional[List[float]]:
    """
    Get embedding vector for text using Groq's API
    """
    if not groq_client:
        logger.error("Groq client not initialized")
        return None
    
    try:
        # Create embedding using Groq
        response = groq_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        
        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding of dimension {len(embedding)}")
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None

def index_document(file_content: str, document_name: str, project_id: str) -> Dict[str, any]:
    """
    Index a document by chunking it and storing with embeddings
    
    Args:
        file_content: The text content of the document
        document_name: Name of the source document
        project_id: UUID of the project this document belongs to
    
    Returns:
        Dict with indexing results
    """
    if not supabase_client:
        return {"success": False, "error": "Supabase client not initialized"}
    
    if not groq_client:
        return {"success": False, "error": "Groq client not initialized"}
    
    try:
        # Create text chunks
        chunks = create_text_chunks(file_content)
        
        if not chunks:
            return {"success": False, "error": "No chunks created from document"}
        
        indexed_chunks = []
        failed_chunks = []
        
        # Process each chunk
        for chunk_text, chunk_index in chunks:
            try:
                # Get embedding for chunk
                embedding = get_embedding(chunk_text)
                
                if not embedding:
                    failed_chunks.append(chunk_index)
                    continue
                
                # Prepare data for insertion
                chunk_data = {
                    "project_id": project_id,
                    "source_document_name": document_name,
                    "content": chunk_text,
                    "embedding": embedding,
                    "chunk_index": chunk_index
                }
                
                # Insert into Supabase
                result = supabase_client.table('document_chunks').insert(chunk_data).execute()
                
                if result.data:
                    indexed_chunks.append(chunk_index)
                    logger.info(f"Indexed chunk {chunk_index} for document {document_name}")
                else:
                    failed_chunks.append(chunk_index)
                    
            except Exception as e:
                logger.error(f"Error indexing chunk {chunk_index}: {e}")
                failed_chunks.append(chunk_index)
        
        # Return results
        return {
            "success": True,
            "document_name": document_name,
            "project_id": project_id,
            "total_chunks": len(chunks),
            "indexed_chunks": len(indexed_chunks),
            "failed_chunks": len(failed_chunks),
            "chunk_indices": {
                "indexed": indexed_chunks,
                "failed": failed_chunks
            }
        }
        
    except Exception as e:
        logger.error(f"Error indexing document: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def search_similar_chunks(query: str, project_id: Optional[str] = None, limit: int = 5) -> List[Dict]:
    """
    Search for similar chunks using vector similarity
    
    Args:
        query: Search query text
        project_id: Optional project ID to filter results
        limit: Maximum number of results
    
    Returns:
        List of similar chunks with metadata
    """
    if not supabase_client or not groq_client:
        logger.error("Required clients not initialized")
        return []
    
    try:
        # Get embedding for query
        query_embedding = get_embedding(query)
        if not query_embedding:
            return []
        
        # Build query
        query_builder = supabase_client.table('document_chunks').select('*')
        
        # Add project filter if specified
        if project_id:
            query_builder = query_builder.eq('project_id', project_id)
        
        # Use vector similarity search (this is a placeholder - actual implementation
        # depends on Supabase's vector search capabilities)
        # For now, we'll fetch all and calculate similarity client-side
        results = query_builder.execute()
        
        if not results.data:
            return []
        
        # Calculate similarities (simplified cosine similarity)
        chunks_with_similarity = []
        query_embedding_np = np.array(query_embedding)
        
        for chunk in results.data:
            if chunk.get('embedding'):
                chunk_embedding_np = np.array(chunk['embedding'])
                similarity = np.dot(query_embedding_np, chunk_embedding_np) / (
                    np.linalg.norm(query_embedding_np) * np.linalg.norm(chunk_embedding_np)
                )
                chunks_with_similarity.append({
                    **chunk,
                    'similarity': float(similarity)
                })
        
        # Sort by similarity and return top results
        chunks_with_similarity.sort(key=lambda x: x['similarity'], reverse=True)
        return chunks_with_similarity[:limit]
        
    except Exception as e:
        logger.error(f"Error searching chunks: {e}")
        return []

# Export functions
__all__ = ['index_document', 'search_similar_chunks', 'create_text_chunks', 'get_embedding']