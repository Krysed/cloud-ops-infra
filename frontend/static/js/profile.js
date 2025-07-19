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
      document.getElementById('member-since').textContent = data.stats.member_since;
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
      activityHtml += '<h5>Your Recent Applications:</h5><ul class="list-group">';
      data.recent_applications.forEach(app => {
        activityHtml += `<li class="list-group-item">Applied to posting ID: ${app.posting_id}</li>`;
      });
      activityHtml += '</ul>';
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
