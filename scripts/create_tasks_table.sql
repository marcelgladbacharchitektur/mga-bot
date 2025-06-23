-- Create tasks table for MGA Bot
CREATE TABLE IF NOT EXISTS tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Core fields
    content TEXT NOT NULL,
    is_done BOOLEAN DEFAULT FALSE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Additional fields
    priority TEXT DEFAULT 'mittel' CHECK (priority IN ('hoch', 'mittel', 'niedrig')),
    due_date DATE,
    created_by TEXT,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Tirol-specific fields
    behörde TEXT, -- z.B. "BH Innsbruck", "Gemeinde Kitzbühel"
    gemeinde TEXT, -- Tiroler Gemeinde
    tags TEXT[] -- Array für Tags wie ["TBO", "Schneelast", "Stellplatz"]
);

-- Create indexes
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_is_done ON tasks(is_done);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);

-- Enable Row Level Security
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY "Enable all operations for tasks" ON tasks
    FOR ALL USING (true);

-- Create view for convenient display
CREATE OR REPLACE VIEW tasks_with_projects AS
SELECT 
    t.id,
    t.created_at,
    t.content,
    t.is_done,
    t.priority,
    t.due_date,
    t.project_id,
    p.name as project_name,
    p.project_number,
    t.behörde,
    t.gemeinde,
    t.tags,
    t.created_by
FROM tasks t
LEFT JOIN projects p ON t.project_id = p.id
ORDER BY 
    t.is_done ASC,
    CASE t.priority 
        WHEN 'hoch' THEN 1 
        WHEN 'mittel' THEN 2 
        WHEN 'niedrig' THEN 3 
    END,
    t.created_at DESC;

-- Test insert
INSERT INTO tasks (content, priority, tags)
VALUES ('Test-Aufgabe: Stellplatznachweis nach TBO prüfen', 'hoch', ARRAY['TBO', 'Stellplatz'])
RETURNING *;