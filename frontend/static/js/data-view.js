document.addEventListener('DOMContentLoaded', function () {
  const ITEMS_PER_PAGE = 10;
  let allPostings = [];
  let currentPage = 1;

  loadPostings();

  document.getElementById('load-data-btn').addEventListener('click', loadPostings);

  async function loadPostings() {
    const tbody = document.getElementById('postings-tbody');
    tbody.innerHTML = `
      <tr><td colspan="5" class="text-center">
        <div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>
        <p class="mt-2">Loading postings...</p>
      </td></tr>`;
    try {
      const response = await fetch('/api/postings-data', { credentials: 'include' });
      const data = await response.json();
      allPostings = (data.postings && data.postings.length > 0) ? data.postings : [];
      currentPage = 1;
      renderPage();
    } catch (error) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading data</td></tr>';
      document.getElementById('pagination-controls').innerHTML = '';
    }
  }

  function renderPage() {
    const tbody = document.getElementById('postings-tbody');
    const controls = document.getElementById('pagination-controls');

    if (allPostings.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center">No postings found</td></tr>';
      controls.innerHTML = '';
      return;
    }

    const totalPages = Math.ceil(allPostings.length / ITEMS_PER_PAGE);
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const pageItems = allPostings.slice(start, start + ITEMS_PER_PAGE);

    tbody.innerHTML = '';
    pageItems.forEach(posting => {
      const actionButton = posting.is_own
        ? '<span class="badge bg-primary">Your Posting</span>'
        : `<a href="/posting-detail.html?hash=${posting.hash || posting.id}" class="btn btn-primary btn-sm">View Details</a>`;

      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${posting.id}</td>
        <td><strong>${posting.title}</strong></td>
        <td><span class="badge bg-secondary">${posting.category}</span></td>
        <td>${posting.post_description.substring(0, 100)}...</td>
        <td>${actionButton}</td>`;
      tbody.appendChild(row);
    });

    controls.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mt-3">
        <span class="text-muted">
          Showing ${start + 1}–${Math.min(start + ITEMS_PER_PAGE, allPostings.length)}
          of ${allPostings.length} postings
        </span>
        <nav>
          <ul class="pagination mb-0">
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
              <button class="page-link" id="prev-btn">Previous</button>
            </li>
            <li class="page-item disabled">
              <span class="page-link">Page ${currentPage} of ${totalPages}</span>
            </li>
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
              <button class="page-link" id="next-btn">Next</button>
            </li>
          </ul>
        </nav>
      </div>`;

    if (currentPage > 1) {
      document.getElementById('prev-btn').addEventListener('click', () => {
        currentPage--;
        renderPage();
        document.querySelector('.bg-white.postings-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
    if (currentPage < totalPages) {
      document.getElementById('next-btn').addEventListener('click', () => {
        currentPage++;
        renderPage();
        document.querySelector('.bg-white.postings-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
  }
});
