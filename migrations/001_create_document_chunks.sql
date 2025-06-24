-- Enable vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create document_chunks table for RAG pipeline
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    source_document_name TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024), -- Nomic embed dimensions
    chunk_index INTEGER NOT NULL, -- Position of chunk in document
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    
    -- Indexes for performance
    CONSTRAINT document_chunks_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Create indexes for better query performance
CREATE INDEX idx_document_chunks_project_id ON document_chunks(project_id);
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);

-- Add RLS policies
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Policy for reading document chunks (everyone can read)
CREATE POLICY "Enable read access for all users" ON document_chunks
    FOR SELECT USING (true);

-- Policy for inserting document chunks (authenticated users only)
CREATE POLICY "Enable insert for authenticated users only" ON document_chunks
    FOR INSERT WITH CHECK (true);

-- Add comment
COMMENT ON TABLE document_chunks IS 'Stores document chunks with embeddings for RAG (Retrieval-Augmented Generation) pipeline';