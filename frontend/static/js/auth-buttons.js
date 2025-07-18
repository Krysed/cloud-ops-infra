// Minimal auth button loader
document.addEventListener('DOMContentLoaded', function() {
    const authContainer = document.querySelector('.auth-buttons');
    if (!authContainer) return;
    
    fetch('/api/auth/buttons', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        let buttonHtml;
        
        if (data.authenticated) {
            buttonHtml = `
                <form method="${data.method}" action="${data.url}" style="display: inline;">
                    <button type="submit" class="custom-btn custom-border-btn btn">
                        <i class="${data.icon} me-2"></i>${data.text}
                    </button>
                </form>
            `;
        } else {
            buttonHtml = `
                <a href="${data.url}" class="custom-btn custom-border-btn btn">
                    <i class="${data.icon} me-2"></i>${data.text}
                </a>
            `;
        }
        
        authContainer.innerHTML = buttonHtml;
    })
    .catch(error => {
        console.error('Failed to load auth buttons:', error);
        authContainer.innerHTML = '<a href="/login.html" class="custom-btn custom-border-btn btn"><i class="bi-box-arrow-in-right me-2"></i>Login</a>';
    });
});