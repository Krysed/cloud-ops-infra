// Simple navigation display - backend provides all logic
document.addEventListener('DOMContentLoaded', function() {
    const navContainer = document.querySelector('.offcanvas-body nav ul');
    if (!navContainer) return;
    
    const currentPath = window.location.pathname;
    
    fetch('/api/navigation', {
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        let navItems = '';
        data.nav_items.forEach(item => {
            const isActive = currentPath.includes(item.path_check) ? 'class="active"' : '';
            navItems += `<li><a href="${item.url}" ${isActive}>${item.text}</a></li>`;
        });
        navContainer.innerHTML = navItems;
    })
    .catch(error => {
        navContainer.innerHTML = '<li><a href="/data-view.html">View Postings</a></li>';
    });
});