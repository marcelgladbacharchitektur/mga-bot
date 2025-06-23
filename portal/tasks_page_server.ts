// src/routes/tasks/+page.server.ts
import { supabase } from '$lib/supabase'
import type { PageServerLoad } from './$types'

export const load: PageServerLoad = async () => {
  // Fetch all tasks with project info
  const { data: tasks, error } = await supabase
    .from('tasks_with_projects')
    .select('*')
    .order('is_done', { ascending: true })
    .order('created_at', { ascending: false })

  if (error) {
    console.error('Error fetching tasks:', error)
    return {
      tasks: []
    }
  }

  return {
    tasks: tasks || []
  }
}