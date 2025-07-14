document.addEventListener('DOMContentLoaded', function() {
  const registerForm = document.querySelector('form[action="/api/users"]');
  
  if (registerForm) {
    registerForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const formData = new FormData(registerForm);
      const submitBtn = registerForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      
      submitBtn.innerHTML = 'Creating Account...';
      submitBtn.disabled = true;
      
      try {
        const response = await fetch('/api/users', {
          method: 'POST',
          body: formData
        });
        
        if (response.ok) {
          const result = await response.json();
          showPopup('Account Created!', 'Your account has been created successfully. Redirecting to login...', 'success');
          setTimeout(() => {
            window.location.href = '/login';
          }, 1500);
        } else {
          const error = await response.json();
          showPopup('Registration Failed', error.detail || 'Unable to create account. Please try again.', 'error');
        }
      } catch (error) {
        showPopup('Error', 'Connection error. Please try again.', 'error');
      } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
      }
    });
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