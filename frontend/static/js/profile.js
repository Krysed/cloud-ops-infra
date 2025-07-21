document.addEventListener('DOMContentLoaded', function() {
  loadProfileData();
});

async function loadProfileData() {
  try {
    const response = await fetch('/api/profile/data', {
      credentials: 'include'
    });
    const data = await response.json();
    
    // Populate form fields
    if (data.user) {
      document.getElementById('name').value = data.user.name || '';
      document.getElementById('surname').value = data.user.surname || '';
      document.getElementById('username').value = data.user.username || '';
      document.getElementById('email').value = data.user.email || '';
    }
    
    // Display stats
    if (data.stats) {
      document.getElementById('total-postings').textContent = data.stats.total_postings;
      document.getElementById('total-applications').textContent = data.stats.total_applications;
      
      // Format member since date properly
      let memberSince = data.stats.member_since;
      if (memberSince && memberSince.includes('T')) {
        const date = new Date(memberSince);
        memberSince = date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        });
      }
      document.getElementById('member-since').textContent = memberSince;
    }
    
    // Generate and display activity HTML
    let activityHtml = '';
    
    if (data.recent_postings && data.recent_postings.length > 0) {
      activityHtml += '<h5>Your Recent Postings:</h5><ul class="list-group mb-3">';
      data.recent_postings.forEach(posting => {
        activityHtml += `<li class="list-group-item">${posting.title} - ${posting.category}</li>`;
      });
      activityHtml += '</ul>';
    }
    
    if (data.recent_applications && data.recent_applications.length > 0) {
      activityHtml += '<h5>Your Recent Applications:</h5><div class="list-group">';
      data.recent_applications.forEach(app => {
        const appliedDate = new Date(app.applied_at).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
        
        // Status badge styling
        let statusBadge = '';
        switch(app.status.toLowerCase()) {
          case 'accepted':
            statusBadge = '<span class="badge bg-success">Accepted</span>';
            break;
          case 'rejected':
            statusBadge = '<span class="badge bg-danger">Rejected</span>';
            break;
          case 'pending':
            statusBadge = '<span class="badge bg-warning text-dark">Pending</span>';
            break;
          default:
            statusBadge = '<span class="badge bg-secondary">Unknown</span>';
        }
        
        activityHtml += `
          <div class="list-group-item d-flex justify-content-between align-items-center">
            <div>
              <h6 class="mb-1">${app.title} ${statusBadge}</h6>
              <p class="mb-1 text-muted">${app.category}</p>
              <small class="text-muted">Applied on ${appliedDate}</small>
            </div>
            <div>
              <button class="btn btn-outline-primary btn-sm" onclick="showJobDetails(${JSON.stringify(app).replace(/"/g, '&quot;')})">
                <i class="bi bi-eye"></i> View Details
              </button>
            </div>
          </div>
        `;
      });
      activityHtml += '</div>';
    }
    
    if ((!data.recent_postings || data.recent_postings.length === 0) && 
        (!data.recent_applications || data.recent_applications.length === 0)) {
      activityHtml = '<p class="text-center text-muted">No recent activity found.</p>';
    }
    
    document.getElementById('recent-activity').innerHTML = activityHtml;
    
  } catch (error) {
    document.getElementById('recent-activity').innerHTML = '<p class="text-center text-danger">Error loading profile data.</p>';
  }
}

function showJobDetails(application) {
  const modal = new bootstrap.Modal(document.getElementById('jobDetailsModal'));
  
  const postingDate = new Date(application.posting_created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  
  const appliedDate = new Date(application.applied_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  
  // Status badge styling for modal
  let statusBadge = '';
  switch(application.status.toLowerCase()) {
    case 'accepted':
      statusBadge = '<span class="badge bg-success">Accepted</span>';
      break;
    case 'rejected':
      statusBadge = '<span class="badge bg-danger">Rejected</span>';
      break;
    case 'pending':
      statusBadge = '<span class="badge bg-warning text-dark">Pending</span>';
      break;
    default:
      statusBadge = '<span class="badge bg-secondary">Unknown</span>';
  }

  const modalContent = `
    <div class="bg-white text-dark p-0">
      <div class="mb-3">
        <h4 class="text-primary">${application.title}</h4>
        <p class="text-dark mb-2">
          <span class="badge bg-secondary me-2">${application.category}</span>
          Posted by ${application.posting_creator_name} on ${postingDate}
        </p>
      </div>
      
      <div class="mb-4">
        <h6 class="text-dark">Job Description:</h6>
        <div class="border-start border-primary border-3 ps-3">
          <p class="text-dark">${application.post_description.replace(/\n/g, '<br>')}</p>
        </div>
      </div>
      
      <div class="mb-3">
        <h6 class="text-dark">Your Application:</h6>
        <div class="bg-light p-3 rounded">
          <p class="mb-2 text-dark"><strong>Applied on:</strong> ${appliedDate}</p>
          <p class="mb-2 text-dark"><strong>Status:</strong> ${statusBadge}</p>
          ${application.message ? `<p class="mb-2 text-dark"><strong>Your Message:</strong><br>${application.message}</p>` : ''}
          ${application.cover_letter ? `<p class="mb-0 text-dark"><strong>Cover Letter:</strong><br>${application.cover_letter}</p>` : ''}
        </div>
      </div>
    </div>
  `;
  
  document.getElementById('job-details-content').innerHTML = modalContent;
  modal.show();
}
