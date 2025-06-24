// src/routes/+page.server.ts
import { supabase } from '$lib/supabase'

export const load = async () => {
  // Fetch all projects sorted by created_at descending
  const { data: projects, error } = await supabase
    .from('projects')
    .select('*')
    .order('created_at', { ascending: false })

  if (error) {
    console.error('Error fetching projects:', error)
    return {
      projects: []
    }
  }

  return {
    projects: projects || []
  }
}