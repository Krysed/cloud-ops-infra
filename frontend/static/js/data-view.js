document.addEventListener('DOMContentLoaded', function() {
  loadPostings();
  
  async function loadPostings() {
    const tbody = document.getElementById('postings-tbody');
    try {
      const response = await fetch('/api/postings-data', {
        credentials: 'include'
      });
      const data = await response.json();
      
      tbody.innerHTML = '';
      
      if (data.postings && data.postings.length > 0) {
        data.postings.forEach(posting => {
          const row = document.createElement('tr');
          
          // Generate action button based on backend logic
          let actionButton = '';
          if (posting.is_own) {
            actionButton = '<span class="badge bg-primary">Your Posting</span>';
          } else {
            actionButton = `<a href="/posting-detail.html?hash=${posting.hash || posting.id}" class="btn btn-primary btn-sm">View Details</a>`;
          }
          
          row.innerHTML = `
            <td>${posting.id}</td>
            <td><strong>${posting.title}</strong></td>
            <td><span class="badge bg-secondary">${posting.category}</span></td>
            <td>${posting.post_description.substring(0, 100)}...</td>
            <td>${actionButton}</td>
          `;
          tbody.appendChild(row);
        });
      } else {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No postings found</td></tr>';
      }
    } catch (error) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading data</td></tr>';
    }
  }
});
