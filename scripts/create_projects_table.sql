-- Create projects table for MGA Bot
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    name TEXT NOT NULL,
    drive_folder_id TEXT NOT NULL,
    drive_folder_link TEXT,
    
    -- Additional useful fields
    project_number TEXT,
    description TEXT,
    status TEXT DEFAULT 'active',
    
    -- Indexes for performance
    UNIQUE(drive_folder_id)
);

-- Create index on name for faster searches
CREATE INDEX idx_projects_name ON projects(name);

-- Create index on project_number
CREATE INDEX idx_projects_number ON projects(project_number);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all operations for now
-- (You can make this more restrictive later)
CREATE POLICY "Enable all operations for authenticated users" ON projects
    FOR ALL USING (true);

-- Insert test record to verify
INSERT INTO projects (name, drive_folder_id, drive_folder_link, project_number)
VALUES ('TEST-PROJECT', 'test-id-123', 'https://drive.google.com/test', '00-000')
RETURNING *;