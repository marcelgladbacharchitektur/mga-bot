// src/routes/+page.server.ts
import { supabase } from '$lib/supabase'
import type { PageServerLoad } from './$types'
import type { Project } from '$lib/supabase'

export const load: PageServerLoad = async () => {
  // Fetch all projects sorted by created_at descending
  const { data: projects, error } = await supabase
    .from('projects')
    .select('*')
    .order('created_at', { ascending: false })

  if (error) {
    console.error('Error fetching projects:', error)
    return {
      projects: [] as Project[]
    }
  }

  return {
    projects: projects as Project[]
  }
}