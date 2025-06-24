<!-- src/routes/+page.svelte -->
<script>
  export let data
  
  // Format date for display
  function formatDate(dateString) {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }
</script>

<div class="container">
  <h1>MGA Portal - Projektübersicht</h1>
  
  <div class="stats">
    <p>Anzahl Projekte: <strong>{data.projects.length}</strong></p>
  </div>

  <div class="project-list">
    <table>
      <thead>
        <tr>
          <th>Projektnummer</th>
          <th>Name</th>
          <th>Erstellt am</th>
          <th>Status</th>
          <th>Aktionen</th>
        </tr>
      </thead>
      <tbody>
        {#each data.projects as project}
          <tr>
            <td>{project.project_number || project.name.split('-')[0] + '-' + project.name.split('-')[1] || 'N/A'}</td>
            <td>
              <a href={project.drive_folder_link} target="_blank" rel="noopener noreferrer">
                {project.name}
              </a>
            </td>
            <td>{formatDate(project.created_at)}</td>
            <td>
              <span class="status {project.status}">{project.status}</span>
            </td>
            <td>
              <a href={project.drive_folder_link} target="_blank" class="button">
                📁 Öffnen
              </a>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
    
    {#if data.projects.length === 0}
      <p class="no-projects">Noch keine Projekte vorhanden.</p>
    {/if}
  </div>
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
    background: #f5f5f5;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 2rem;
  }
  
  .project-list {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    overflow: hidden;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
  }
  
  th {
    background: #4a5568;
    color: white;
    padding: 1rem;
    text-align: left;
    font-weight: 600;
  }
  
  td {
    padding: 1rem;
    border-bottom: 1px solid #e2e8f0;
  }
  
  tr:hover {
    background: #f7fafc;
  }
  
  a {
    color: #3182ce;
    text-decoration: none;
  }
  
  a:hover {
    text-decoration: underline;
  }
  
  .button {
    display: inline-block;
    padding: 0.5rem 1rem;
    background: #4299e1;
    color: white;
    border-radius: 4px;
    text-decoration: none;
  }
  
  .button:hover {
    background: #3182ce;
    text-decoration: none;
  }
  
  .status {
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
  }
  
  .status.active {
    background: #c6f6d5;
    color: #22543d;
  }
  
  .no-projects {
    text-align: center;
    padding: 3rem;
    color: #718096;
  }
</style>