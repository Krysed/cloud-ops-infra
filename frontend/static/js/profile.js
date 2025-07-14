document.addEventListener('DOMContentLoaded', function() {
  const profileForm = document.getElementById('profile-form');
  
  // For demo purposes, using user_id = 1. In real app, this would come from session/login
  const currentUserId = 1;
  
  // Load all data on page load
  loadUserProfile();
  loadUserStats();
  loadRecentActivity();
  
  // Profile form submission
  if (profileForm) {
    profileForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const formData = new FormData(profileForm);
      const submitBtn = profileForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      
      submitBtn.innerHTML = 'Updating...';
      submitBtn.disabled = true;
      
      try {
        const response = await fetch(`/api/users/${currentUserId}`, {
          method: 'PUT',
          body: formData
        });
        
        if (response.ok) {
          const result = await response.json();
          showPopup('Profile Updated!', result.message || 'Your profile has been updated successfully.', 'success');
        } else {
          const error = await response.json();
          showPopup('Update Failed', error.detail || 'Unable to update profile. Please try again.', 'error');
        }
      } catch (error) {
        showPopup('Error', 'Connection error. Please try again.', 'error');
      } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
      }
    });
  }
  
  async function loadUserStats() {
    try {
      const [postingsResponse, applicationsResponse] = await Promise.all([
        fetch(`/api/postings/by_user/${currentUserId}`),
        fetch(`/api/applications/by_user/${currentUserId}`)
      ]);
      
      const postings = await postingsResponse.json();
      const applications = await applicationsResponse.json();
      
      document.getElementById('total-postings').textContent = postings.length || 0;
      document.getElementById('total-applications').textContent = applications.length || 0;
      document.getElementById('member-since').textContent = 'Jan 2024'; // This could come from user data
    } catch (error) {
      document.getElementById('total-postings').textContent = 'Error';
      document.getElementById('total-applications').textContent = 'Error';
      document.getElementById('member-since').textContent = 'Error';
    }
  }
  
  async function loadRecentActivity() {
    try {
      const [postingsResponse, applicationsResponse] = await Promise.all([
        fetch(`/api/postings/by_user/${currentUserId}`),
        fetch(`/api/applications/by_user/${currentUserId}`)
      ]);
      
      const postings = await postingsResponse.json();
      const applications = await applicationsResponse.json();
      
      const activityDiv = document.getElementById('recent-activity');
      let activityHtml = '';
      
      if (postings.length > 0) {
        activityHtml += '<h5>Your Recent Postings:</h5><ul class="list-group mb-3">';
        postings.slice(0, 3).forEach(posting => {
          activityHtml += `<li class="list-group-item">${posting.title} - ${posting.category}</li>`;
        });
        activityHtml += '</ul>';
      }
      
      if (applications.length > 0) {
        activityHtml += '<h5>Your Recent Applications:</h5><ul class="list-group">';
        applications.slice(0, 3).forEach(app => {
          activityHtml += `<li class="list-group-item">Applied to posting ID: ${app.posting_id}</li>`;
        });
        activityHtml += '</ul>';
      }
      
      if (postings.length === 0 && applications.length === 0) {
        activityHtml = '<p class="text-center text-muted">No recent activity found.</p>';
      }
      
      activityDiv.innerHTML = activityHtml;
    } catch (error) {
      document.getElementById('recent-activity').innerHTML = '<p class="text-center text-danger">Error loading recent activity.</p>';
    }
  }
  
  async function loadUserProfile() {
    try {
      const response = await fetch(`/api/users/${currentUserId}`);
      if (response.ok) {
        const user = await response.json();
        
        document.getElementById('name').value = user.name || '';
        document.getElementById('surname').value = user.surname || '';
        document.getElementById('username').value = user.username || '';
        document.getElementById('email').value = user.email || '';
      }
    } catch (error) {
      console.log('Unable to load user profile');
    }
  }
});

function showPopup(title, message, type) {
  const overlay = document.createElement('div');
  overlay.className = 'popup-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
  `;
  
  const popup = document.createElement('div');
  popup.className = 'popup';
  popup.style.cssText = `
    background: white;
    padding: 2rem;
    border-radius: 10px;
    max-width: 400px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  `;
  
  const iconClass = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle';
  const iconColor = type === 'success' ? '#28a745' : '#dc3545';
  
  popup.innerHTML = `
    <div style="font-size: 3rem; margin-bottom: 1rem; color: ${iconColor};">
      <i class="${iconClass}"></i>
    </div>
    <h3 style="margin-bottom: 1rem; color: ${iconColor};">${title}</h3>
    <p style="margin-bottom: 1.5rem;">${message}</p>
    <button class="btn btn-primary" onclick="this.closest('.popup-overlay').remove()">OK</button>
  `;
  
  overlay.appendChild(popup);
  document.body.appendChild(overlay);
  
  setTimeout(() => {
    if (overlay.parentNode) {
      overlay.remove();
    }
  }, 5000);
}