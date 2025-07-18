// Dynamic navigation based on authentication status
document.addEventListener('DOMContentLoaded', function() {
    const navContainer = document.querySelector('.offcanvas-body nav ul');
    if (!navContainer) return;
    
    // Get current page from URL
    const currentPath = window.location.pathname;
    
    // Check authentication status
    fetch('/api/auth/status', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        let navItems = '';
        
        if (data.authenticated) {
            // Navigation for authenticated users
            navItems = `
                <li><a href="/data-view" ${currentPath === '/data-view' ? 'class="active"' : ''}>Data View</a></li>
                <li><a href="/contact" ${currentPath === '/contact' ? 'class="active"' : ''}>Contact Form</a></li>
                <li><a href="/profile" ${currentPath === '/profile' ? 'class="active"' : ''}>User Profile</a></li>
            `;
        } else {
            // Navigation for unauthenticated users
            navItems = `
                <li><a href="/login" ${currentPath === '/login' ? 'class="active"' : ''}>Login Form</a></li>
                <li><a href="/register" ${currentPath === '/register' ? 'class="active"' : ''}>Create an account</a></li>
                <li><a href="/contact" ${currentPath === '/contact' ? 'class="active"' : ''}>Contact Form</a></li>
            `;
        }
        
        navContainer.innerHTML = navItems;
    })
    .catch(error => {
        console.error('Failed to load navigation:', error);
        // Fallback to unauthenticated navigation
        navContainer.innerHTML = `
            <li><a href="/login" ${currentPath === '/login' ? 'class="active"' : ''}>Login Form</a></li>
            <li><a href="/register" ${currentPath === '/register' ? 'class="active"' : ''}>Create an account</a></li>
            <li><a href="/contact" ${currentPath === '/contact' ? 'class="active"' : ''}>Contact Form</a></li>
        `;
    });
});