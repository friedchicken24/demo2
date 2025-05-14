document.addEventListener('DOMContentLoaded', function() {
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle spoiler toggles
    document.querySelectorAll('.spoiler-toggle').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const spoilerContent = this.nextElementSibling;
            spoilerContent.classList.toggle('spoiler-hidden');
            
            if (spoilerContent.classList.contains('spoiler-hidden')) {
                this.textContent = "Show Spoiler";
            } else {
                this.textContent = "Hide Spoiler";
            }
        });
    });

    // Handle comment replies
    document.querySelectorAll('.reply-button').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const commentId = this.getAttribute('data-comment-id');
            const replyForm = document.getElementById('reply-form-' + commentId);
            
            // Hide all other reply forms first
            document.querySelectorAll('.reply-form').forEach(form => {
                if (form.id !== 'reply-form-' + commentId) {
                    form.classList.add('d-none');
                }
            });
            
            // Toggle the clicked form
            replyForm.classList.toggle('d-none');
            
            // Update the parent comment ID in the form
            const parentCommentInput = replyForm.querySelector('input[name="parent_comment_id"]');
            if (parentCommentInput) {
                parentCommentInput.value = commentId;
            }
        });
    });

    // Handle mobile navigation menu
    const mobileMenuToggle = document.querySelector('.navbar-toggler');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            document.querySelector('.navbar-collapse').classList.toggle('show');
        });
    }

    // Initialize lazy loading for images
    if ('loading' in HTMLImageElement.prototype) {
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
            img.src = img.dataset.src;
        });
    } else {
        // Fallback for browsers that don't support lazy loading
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
        document.body.appendChild(script);
    }

    // Set active navigation item based on current page
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });
});

// Format date function for use throughout the site
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

// Format datetime function for use throughout the site
function formatDateTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Handle confirmation dialogs
function confirmAction(message, formId) {
    if (confirm(message)) {
        document.getElementById(formId).submit();
    }
    return false;
}

// Flash message dismissal
setTimeout(function() {
    const alertList = document.querySelectorAll('.alert-auto-dismiss');
    alertList.forEach(function(alert) {
        new bootstrap.Alert(alert).close();
    });
}, 5000);
