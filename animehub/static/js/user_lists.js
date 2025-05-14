document.addEventListener('DOMContentLoaded', function() {
    // Initialize sortable lists (if browser supports drag and drop)
    if (typeof Sortable !== 'undefined') {
        document.querySelectorAll('.sortable-list').forEach(function(list) {
            Sortable.create(list, {
                animation: 150,
                ghostClass: 'sortable-ghost',
                onEnd: function(evt) {
                    updateItemOrder(evt.to.id);
                }
            });
        });
    }

    // Handle list item status changes
    document.querySelectorAll('.list-item-status').forEach(function(select) {
        select.addEventListener('change', function() {
            const form = this.closest('form');
            form.submit();
        });
    });
    
    // Handle progress updates with debounce
    let progressUpdateTimeout;
    document.querySelectorAll('.list-item-progress').forEach(function(input) {
        input.addEventListener('input', function() {
            clearTimeout(progressUpdateTimeout);
            const form = this.closest('form');
            
            progressUpdateTimeout = setTimeout(function() {
                form.submit();
            }, 1000);
        });
    });
    
    // Handle list score updates
    document.querySelectorAll('.list-item-score').forEach(function(select) {
        select.addEventListener('change', function() {
            const form = this.closest('form');
            form.submit();
        });
    });
    
    // Handle list visibility toggle
    const visibilityToggles = document.querySelectorAll('.list-visibility-toggle');
    
    visibilityToggles.forEach(function(toggle) {
        toggle.addEventListener('change', function() {
            const listId = this.getAttribute('data-list-id');
            const form = document.getElementById('visibility-form-' + listId);
            if (form) {
                form.submit();
            }
        });
    });
    
    // Confirm list deletion
    document.querySelectorAll('.delete-list-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this list? All items in this list will be removed.')) {
                e.preventDefault();
            }
        });
    });
    
    // Confirm list item removal
    document.querySelectorAll('.remove-item-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to remove this item from your list?')) {
                e.preventDefault();
            }
        });
    });
    
    // Handle list filter
    const listFilter = document.getElementById('list-item-filter');
    if (listFilter) {
        listFilter.addEventListener('input', function() {
            const filterValue = this.value.toLowerCase();
            const listItems = document.querySelectorAll('.list-item');
            
            listItems.forEach(function(item) {
                const titleElement = item.querySelector('.item-title');
                if (titleElement) {
                    const title = titleElement.textContent.toLowerCase();
                    if (title.indexOf(filterValue) > -1) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                }
            });
        });
    }
    
    // Handle list type tabs
    const listTypeTabs = document.querySelectorAll('.list-type-tab');
    
    listTypeTabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            listTypeTabs.forEach(function(t) {
                t.classList.remove('active');
            });
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Hide all lists
            document.querySelectorAll('.list-type-content').forEach(function(content) {
                content.classList.add('d-none');
            });
            
            // Show selected list
            const listType = this.getAttribute('data-list-type');
            const listContent = document.querySelector('.list-type-content[data-list-type="' + listType + '"]');
            if (listContent) {
                listContent.classList.remove('d-none');
            }
        });
    });
    
    // Load list content when tab is clicked
    document.querySelectorAll('.list-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            const listId = this.getAttribute('data-list-id');
            loadListContent(listId);
        });
    });
});

// Function to update item order after drag and drop
function updateItemOrder(listId) {
    const list = document.getElementById(listId);
    if (!list) return;
    
    const items = list.querySelectorAll('.list-item');
    const orderData = Array.from(items).map(function(item, index) {
        return {
            id: item.getAttribute('data-item-id'),
            position: index + 1
        };
    });
    
    // Send order data to server via fetch
    fetch('/lists/update-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            list_id: listId.replace('list-items-', ''),
            items: orderData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('List order updated successfully');
        } else {
            showToast('Failed to update list order', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating list order:', error);
        showToast('Error updating list order', 'error');
    });
}

// Function to load list contents dynamically
function loadListContent(listId) {
    const contentContainer = document.getElementById('list-content-' + listId);
    if (!contentContainer) return;
    
    // Show loading indicator
    contentContainer.innerHTML = '<div class="text-center py-4"><div class="spinner-border" role="status"></div><p class="mt-2">Loading list items...</p></div>';
    
    // Fetch list content
    fetch('/lists/' + listId + '/content')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            renderListItems(contentContainer, data.items);
        } else {
            contentContainer.innerHTML = '<div class="alert alert-danger">Failed to load list items</div>';
        }
    })
    .catch(error => {
        console.error('Error loading list content:', error);
        contentContainer.innerHTML = '<div class="alert alert-danger">Error loading list items</div>';
    });
}

// Function to render list items
function renderListItems(container, items) {
    if (items.length === 0) {
        container.innerHTML = '<div class="alert alert-info">This list is empty</div>';
        return;
    }
    
    let html = '<ul class="list-group sortable-list" id="list-items-' + items[0].list_id + '">';
    
    items.forEach(function(item) {
        html += `
            <li class="list-group-item list-item" data-item-id="${item.list_item_id}">
                <div class="row align-items-center">
                    <div class="col-md-2">
                        <img src="${item.cover_image_url || '/static/img/placeholder.svg'}" 
                             alt="${item.title}" class="img-fluid rounded" style="max-height: 70px;">
                    </div>
                    <div class="col-md-4">
                        <h5 class="item-title mb-1">${item.title}</h5>
                        <span class="badge bg-${item.content_type === 'anime' ? 'primary' : 'success'}">${item.content_type}</span>
                        <span class="badge bg-secondary">${item.status_text}</span>
                    </div>
                    <div class="col-md-4">
                        <div class="d-flex gap-2">
                            <form action="/update-list-item" method="post" class="row g-2">
                                <input type="hidden" name="list_item_id" value="${item.list_item_id}">
                                <input type="hidden" name="csrf_token" value="${getCsrfToken()}">
                                <div class="col-4">
                                    <input type="number" name="progress" value="${item.progress}" 
                                           class="form-control form-control-sm list-item-progress" min="0"
                                           max="${item.max_progress || ''}" placeholder="Progress">
                                </div>
                                <div class="col-4">
                                    <select name="user_score" class="form-select form-select-sm list-item-score">
                                        <option value="">Score</option>
                                        ${generateScoreOptions(item.user_score)}
                                    </select>
                                </div>
                            </form>
                        </div>
                    </div>
                    <div class="col-md-2 text-end">
                        <form action="/remove-from-list" method="post" id="remove-item-form-${item.list_item_id}">
                            <input type="hidden" name="list_item_id" value="${item.list_item_id}">
                            <input type="hidden" name="csrf_token" value="${getCsrfToken()}">
                            <button type="button" class="btn btn-sm btn-danger remove-item-btn" 
                                    onclick="confirmRemoveItem(${item.list_item_id})">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </form>
                    </div>
                </div>
            </li>
        `;
    });
    
    html += '</ul>';
    container.innerHTML = html;
    
    // Initialize sortable on the new list
    if (typeof Sortable !== 'undefined') {
        Sortable.create(document.getElementById('list-items-' + items[0].list_id), {
            animation: 150,
            ghostClass: 'sortable-ghost',
            onEnd: function(evt) {
                updateItemOrder(evt.to.id);
            }
        });
    }
}

// Function to generate score options
function generateScoreOptions(selectedScore) {
    let options = '';
    for (let i = 1; i <= 10; i++) {
        options += `<option value="${i}"${i == selectedScore ? ' selected' : ''}>${i}</option>`;
    }
    return options;
}

// Function to get CSRF token
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Function to confirm item removal
function confirmRemoveItem(itemId) {
    if (confirm('Are you sure you want to remove this item from your list?')) {
        document.getElementById('remove-item-form-' + itemId).submit();
    }
}

// Function to show toast notification
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}
