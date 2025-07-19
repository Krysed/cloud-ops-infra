document.addEventListener('DOMContentLoaded', function() {
    loadMyPostings();
});

async function loadMyPostings() {
    try {
        const response = await fetch('/api/postings/my-postings', {
            credentials: 'include'
        });
        const postings = await response.json();
        displayPostings(postings);
    } catch (error) {
        document.getElementById('postings-tbody').innerHTML = 
            '<tr><td colspan="7" class="text-center text-danger">Failed to load your postings</td></tr>';
    }
}

function displayPostings(postings) {
    const tbody = document.getElementById('postings-tbody');
    
    if (!postings || postings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No postings found</td></tr>';
        return;
    }
    
    let html = '';
    postings.forEach(function(posting) {
        // Generate HTML based on backend data
        const statusBadge = `<span class="badge bg-success">${posting.status}</span>`;
        const viewsBadge = `<span class="badge bg-info">${posting.views || 0}</span>`;
        const applicationsBadge = `<span class="badge bg-success">${posting.applications_count || 0}</span>`;
        const actionButton = `<a href="/posting-detail.html?hash=${posting.hash || posting.id}" class="btn btn-outline-primary btn-sm">View</a>`;
        
        html += `
            <tr>
                <td><strong>${posting.title}</strong></td>
                <td><span class="badge bg-secondary">${posting.category}</span></td>
                <td>${statusBadge}</td>
                <td>${viewsBadge}</td>
                <td>${applicationsBadge}</td>
                <td>${posting.formatted_date}</td>
                <td>${actionButton}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}
