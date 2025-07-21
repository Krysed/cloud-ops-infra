document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const postingHash = urlParams.get('hash');
    
    if (!postingHash) {
        document.getElementById('posting-content').innerHTML = '<div class="alert alert-danger">No posting hash provided</div>';
        return;
    }
    
    loadPostingDetails(postingHash);
});

async function loadPostingDetails(postingHash) {
    try {
        const response = await fetch(`/api/postings/view/${postingHash}`, {
            credentials: 'include'
        });
        const data = await response.json();
        displayPostingDetails(data);
    } catch (error) {
        document.getElementById('loading-container').style.display = 'none';
        document.getElementById('posting-content').innerHTML = '<div class="alert alert-danger">Failed to load posting details</div>';
        document.getElementById('posting-content').style.display = 'block';
    }
}

function displayPostingDetails(data) {
    // Handle both old format (direct posting data) and new format (wrapped data)
    const posting = data.posting || data;
    const isWrapped = !!data.posting;
    
    // Hide loading and show content
    document.getElementById('loading-container').style.display = 'none';
    document.getElementById('posting-content').style.display = 'block';
    
    // Populate posting details with backend data
    document.getElementById('posting-title').textContent = posting.title;
    document.getElementById('posting-category').textContent = posting.category;
    document.getElementById('posting-description').innerHTML = posting.post_description.replace(/\n/g, '<br>');
    document.getElementById('posting-views').textContent = posting.views || 0;
    document.getElementById('posting-applications').textContent = posting.application_count || posting.applications_count || 0;
    
    // Set formatted date
    if (posting.created_at) {
        const date = new Date(posting.created_at);
        document.getElementById('posting-date').textContent = date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long', 
            day: 'numeric'
        });
    }
    
    // Set author
    document.getElementById('posting-author').textContent = posting.creator_name || 'Anonymous';
    
    // Handle action buttons based on backend logic
    const actionContainer = document.getElementById('action-buttons');
    
    if (isWrapped) {
        // Use backend-provided logic
        if (data.is_owner) {
            actionContainer.innerHTML = `
                <div class="alert alert-info" role="alert">
                    <i class="bi bi-info-circle me-2"></i>This is your posting
                </div>
                <a href="/my-postings.html" class="btn btn-outline-primary">
                    <i class="bi bi-gear me-2"></i>Manage Posting
                </a>
            `;
        } else if (data.can_apply) {
            actionContainer.innerHTML = `
                <button type="button" class="btn btn-primary btn-lg" onclick="showApplicationForm()">
                    <i class="bi bi-envelope me-2"></i>Apply Now
                </button>
                <div id="application-form" style="display: none;" class="mt-3 p-3 border rounded">
                    <h5>Apply for this Position</h5>
                    <form action="/api/applications" method="post">
                        <input type="hidden" name="posting_id" value="${posting.id}">
                        <div class="mb-3">
                            <label for="message" class="form-label">Message (Optional)</label>
                            <textarea class="form-control" name="message" rows="3" placeholder="Brief message to the employer..."></textarea>
                        </div>
                        <div class="mb-3">
                            <label for="cover_letter" class="form-label">Cover Letter (Optional)</label>
                            <textarea class="form-control" name="cover_letter" rows="5" placeholder="Tell them why you're interested in this position..."></textarea>
                        </div>
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-success">Submit Application</button>
                            <button type="button" class="btn btn-secondary" onclick="hideApplicationForm()">Cancel</button>
                        </div>
                    </form>
                </div>
            `;
        } else if (data.has_applied) {
            actionContainer.innerHTML = `
                <div class="alert alert-success" role="alert">
                    <i class="bi bi-check-circle me-2"></i>You have already applied to this position
                </div>
                <button class="btn btn-outline-secondary" disabled>
                    <i class="bi bi-check me-2"></i>Application Submitted
                </button>
            `;
        } else if (!data.is_authenticated) {
            actionContainer.innerHTML = `
                <a href="/login.html" class="btn btn-primary btn-lg">
                    <i class="bi bi-box-arrow-in-right me-2"></i>Login to Apply
                </a>
            `;
        }
    } else {
        // Fallback for old format
        actionContainer.innerHTML = `
            <button type="button" class="btn btn-primary btn-lg" onclick="showApplicationForm()">
                <i class="bi bi-envelope me-2"></i>Apply Now
            </button>
            <div id="application-form" style="display: none;" class="mt-3 p-3 border rounded">
                <h5>Apply for this Position</h5>
                <form action="/api/applications" method="post">
                    <input type="hidden" name="posting_id" value="${posting.id}">
                    <div class="mb-3">
                        <label for="message" class="form-label">Message (Optional)</label>
                        <textarea class="form-control" name="message" rows="3" placeholder="Brief message to the employer..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label for="cover_letter" class="form-label">Cover Letter (Optional)</label>
                        <textarea class="form-control" name="cover_letter" rows="5" placeholder="Tell them why you're interested in this position..."></textarea>
                    </div>
                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-success">Submit Application</button>
                        <button type="button" class="btn btn-secondary" onclick="hideApplicationForm()">Cancel</button>
                    </div>
                </form>
            </div>
        `;
    }
}

function showApplicationForm() {
    document.getElementById('application-form').style.display = 'block';
}

function hideApplicationForm() {
    document.getElementById('application-form').style.display = 'none';
}
