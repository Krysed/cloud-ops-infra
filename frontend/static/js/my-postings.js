document.addEventListener('DOMContentLoaded', function() {
    loadDashboardStats();
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
        const applicationsBadge = `<span class="badge bg-success">${posting.application_count || 0}</span>`;
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

async function loadDashboardStats() {
    try {
        const response = await fetch('/api/dashboard/stats', {
            credentials: 'include'
        });
        const data = await response.json();
        displayDashboardStats(data);
    } catch (error) {
        // Keep default "-" values if stats fail to load
        console.error('Failed to load dashboard stats:', error);
    }
}

function displayDashboardStats(data) {
    if (data.overview) {
        const overview = data.overview;
        
        // Update stats cards with backend data
        document.getElementById('total-postings').textContent = overview.total_postings || 0;
        document.getElementById('total-views').textContent = overview.total_views || 0;
        document.getElementById('total-applications').textContent = overview.total_applications || 0;
        
        // Calculate average applications per posting
        const avgApplications = overview.total_postings > 0 
            ? Math.round((overview.total_applications || 0) / overview.total_postings * 10) / 10
            : 0;
        document.getElementById('avg-applications').textContent = avgApplications;
    }
}
