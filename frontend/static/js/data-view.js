document.addEventListener('DOMContentLoaded', function() {
  const loadBtn = document.getElementById('load-data-btn');
  const tbody = document.getElementById('postings-tbody');
  
  if (loadBtn && tbody) {
    loadBtn.addEventListener('click', async function() {
      loadBtn.innerHTML = 'Loading... <i class="bi-hourglass-split ms-2"></i>';
      loadBtn.disabled = true;
      
      try {
        const response = await fetch('/api/postings');
        const postings = await response.json();
        
        tbody.innerHTML = '';
        
        if (postings && postings.length > 0) {
          postings.forEach(posting => {
            const row = document.createElement('tr');
            row.innerHTML = `
              <td>${posting.id || 'N/A'}</td>
              <td>${posting.title || 'N/A'}</td>
              <td>${posting.category || 'N/A'}</td>
              <td>${posting.post_description || 'N/A'}</td>
            `;
            tbody.appendChild(row);
          });
        } else {
          tbody.innerHTML = '<tr><td colspan="4" class="text-center">No postings found</td></tr>';
        }
        
        loadBtn.innerHTML = 'Load Postings <i class="bi-check-circle ms-2"></i>';
      } catch (error) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Error loading data</td></tr>';
        loadBtn.innerHTML = 'Error <i class="bi-exclamation-triangle ms-2"></i>';
      } finally {
        setTimeout(() => {
          loadBtn.innerHTML = 'Load Postings <i class="bi-arrow-clockwise ms-2"></i>';
          loadBtn.disabled = false;
        }, 2000);
      }
    });
  }
});