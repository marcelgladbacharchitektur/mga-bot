// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://glfwdqaubkbxndsyhmyd.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdsZndkcWF1YmtieG5kc3lobXlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2OTM4MTYsImV4cCI6MjA2NjI2OTgxNn0.6Dy0JkLQLNa2exTN9YDuHhs6rcD4SMG90fCOmzaETJk'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Type definitions for our projects table
export interface Project {
  id: string
  created_at: string
  name: string
  drive_folder_id: string
  drive_folder_link: string | null
  project_number: string | null
  description: string | null
  status: string
}