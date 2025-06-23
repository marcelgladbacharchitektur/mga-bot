// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import { PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY } from '$env/static/public'

export const supabase = createClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY)

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