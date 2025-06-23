-- Create time_entries table for MGA Bot
CREATE TABLE IF NOT EXISTS time_entries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Core fields
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    duration_hours DECIMAL(5,2) NOT NULL CHECK (duration_hours > 0),
    activity_description TEXT NOT NULL,
    entry_date DATE NOT NULL,
    
    -- Additional tracking fields
    created_by TEXT, -- Can store Telegram user ID or name
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT valid_duration CHECK (duration_hours <= 24) -- Max 24 hours per entry
);

-- Create indexes for performance
CREATE INDEX idx_time_entries_project_id ON time_entries(project_id);
CREATE INDEX idx_time_entries_entry_date ON time_entries(entry_date);
CREATE INDEX idx_time_entries_created_at ON time_entries(created_at);

-- Enable Row Level Security
ALTER TABLE time_entries ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all operations for now
CREATE POLICY "Enable all operations for time entries" ON time_entries
    FOR ALL USING (true);

-- Create a view for convenient reporting
CREATE OR REPLACE VIEW time_entries_with_projects AS
SELECT 
    te.id,
    te.created_at,
    te.project_id,
    p.name as project_name,
    p.project_number,
    te.duration_hours,
    te.activity_description,
    te.entry_date,
    te.created_by
FROM time_entries te
JOIN projects p ON te.project_id = p.id
ORDER BY te.entry_date DESC, te.created_at DESC;

-- Test the structure
INSERT INTO time_entries (project_id, duration_hours, activity_description, entry_date, created_by)
SELECT 
    id as project_id,
    2.5 as duration_hours,
    'Test time entry' as activity_description,
    CURRENT_DATE as entry_date,
    'Test User' as created_by
FROM projects 
LIMIT 1
RETURNING *;