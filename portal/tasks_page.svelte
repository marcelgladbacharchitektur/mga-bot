<!-- src/routes/tasks/+page.svelte -->
<script lang="ts">
  import type { PageData } from './$types'
  
  export let data: PageData
  
  function formatDate(dateString: string): string {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('de-AT', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).format(date)
  }
  
  function getPriorityEmoji(priority: string): string {
    return {
      'hoch': '🔴',
      'mittel': '🟡', 
      'niedrig': '🟢'
    }[priority] || '🟡'
  }
  
  // Group tasks by status
  $: openTasks = data.tasks.filter(t => !t.is_done)
  $: doneTasks = data.tasks.filter(t => t.is_done)
</script>

<div class="container">
  <h1>📋 Aufgaben - MGA Portal</h1>
  
  <div class="stats">
    <div class="stat">
      <span class="stat-value">{openTasks.length}</span>
      <span class="stat-label">Offene Aufgaben</span>
    </div>
    <div class="stat">
      <span class="stat-value">{doneTasks.length}</span>
      <span class="stat-label">Erledigt</span>
    </div>
  </div>

  <!-- Open Tasks -->
  <div class="section">
    <h2>📌 Offene Aufgaben</h2>
    
    {#if openTasks.length === 0}
      <p class="empty-state">Keine offenen Aufgaben! 🎉</p>
    {:else}
      <div class="task-grid">
        {#each openTasks as task}
          <div class="task-card">
            <div class="task-header">
              <span class="priority">{getPriorityEmoji(task.priority)}</span>
              <span class="date">{formatDate(task.created_at)}</span>
            </div>
            
            <div class="task-content">
              {task.content}
            </div>
            
            {#if task.project_name}
              <div class="task-project">
                📁 {task.project_name}
              </div>
            {/if}
            
            <div class="task-meta">
              {#if task.tags && task.tags.length > 0}
                <div class="tags">
                  {#each task.tags as tag}
                    <span class="tag">{tag}</span>
                  {/each}
                </div>
              {/if}
              
              {#if task.behörde}
                <div class="behörde">🏛️ {task.behörde}</div>
              {/if}
              
              {#if task.gemeinde}
                <div class="gemeinde">📍 {task.gemeinde}</div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Completed Tasks -->
  {#if doneTasks.length > 0}
    <div class="section completed">
      <h2>✅ Erledigte Aufgaben</h2>
      
      <div class="task-grid">
        {#each doneTasks.slice(0, 5) as task}
          <div class="task-card done">
            <div class="task-content">
              <s>{task.content}</s>
            </div>
            {#if task.project_name}
              <div class="task-project">
                📁 {task.project_name}
              </div>
            {/if}
          </div>
        {/each}
      </div>
      
      {#if doneTasks.length > 5}
        <p class="more-link">Und {doneTasks.length - 5} weitere erledigte Aufgaben...</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  
  h1 {
    color: #333;
    margin-bottom: 2rem;
  }
  
  .stats {
    display: flex;
    gap: 2rem;
    margin-bottom: 3rem;
  }
  
  .stat {
    background: #f5f5f5;
    padding: 1.5rem;
    border-radius: 8px;
    text-align: center;
    flex: 1;
  }
  
  .stat-value {
    display: block;
    font-size: 2.5rem;
    font-weight: 600;
    color: #4a5568;
  }
  
  .stat-label {
    display: block;
    font-size: 0.875rem;
    color: #718096;
    margin-top: 0.5rem;
  }
  
  .section {
    margin-bottom: 3rem;
  }
  
  .section.completed {
    opacity: 0.7;
  }
  
  h2 {
    color: #4a5568;
    margin-bottom: 1.5rem;
  }
  
  .task-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }
  
  .task-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s;
  }
  
  .task-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
  
  .task-card.done {
    background: #f7fafc;
    opacity: 0.8;
  }
  
  .task-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .priority {
    font-size: 1.5rem;
  }
  
  .date {
    font-size: 0.875rem;
    color: #718096;
  }
  
  .task-content {
    font-size: 1rem;
    color: #2d3748;
    margin-bottom: 1rem;
    line-height: 1.5;
  }
  
  .task-project {
    font-size: 0.875rem;
    color: #4299e1;
    margin-bottom: 0.5rem;
  }
  
  .task-meta {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #e2e8f0;
  }
  
  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  .tag {
    background: #e6fffa;
    color: #047857;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
  }
  
  .behörde, .gemeinde {
    font-size: 0.875rem;
    color: #718096;
    margin-top: 0.25rem;
  }
  
  .empty-state {
    text-align: center;
    padding: 3rem;
    color: #718096;
    background: #f7fafc;
    border-radius: 8px;
  }
  
  .more-link {
    text-align: center;
    color: #718096;
    font-size: 0.875rem;
    margin-top: 1rem;
  }
</style>