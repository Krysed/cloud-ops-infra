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

        // Action buttons: View, Edit, Delete
        const actionButtons = `
            <div class="btn-group btn-group-sm" role="group">
                <a href="/posting-detail.html?hash=${posting.hash || posting.id}" class="btn btn-outline-primary" title="View">
                    <i class="bi bi-eye"></i>
                </a>
                <a href="/manage-posting.html?id=${posting.id}" class="btn btn-outline-warning" title="Edit">
                    <i class="bi bi-pencil"></i>
                </a>
                <button onclick="deletePosting(${posting.id}, '${posting.title.replace(/'/g, "\\'")}')" class="btn btn-outline-danger" title="Delete">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;

        html += `
            <tr id="posting-row-${posting.id}">
                <td><strong>${posting.title}</strong></td>
                <td><span class="badge bg-secondary">${posting.category}</span></td>
                <td>${statusBadge}</td>
                <td>${viewsBadge}</td>
                <td>${applicationsBadge}</td>
                <td>${posting.formatted_date}</td>
                <td>${actionButtons}</td>
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

async function deletePosting(postingId, postingTitle) {
    // Confirm deletion
    if (!confirm(`Are you sure you want to delete "${postingTitle}"?\n\nThis action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/postings/${postingId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            // Remove the row from the table
            const row = document.getElementById(`posting-row-${postingId}`);
            if (row) {
                row.remove();
            }

            // Reload stats to reflect the deletion
            loadDashboardStats();

            // Show success message
            showAlert('success', 'Posting deleted successfully!');

            // Reload postings to update the list
            loadMyPostings();
        } else {
            const error = await response.json();
            showAlert('danger', error.detail || 'Failed to delete posting');
        }
    } catch (error) {
        console.error('Error deleting posting:', error);
        showAlert('danger', 'An error occurred while deleting the posting');
    }
}

function showAlert(type, message) {
    const alertContainer = document.getElementById('alert-container');
    const alert = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    alertContainer.innerHTML = alert;

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alertElement = alertContainer.querySelector('.alert');
        if (alertElement) {
            alertElement.classList.remove('show');
            setTimeout(() => alertElement.remove(), 150);
        }
    }, 5000);
}
