document.addEventListener('DOMContentLoaded', function() {
    // Initialize DataTables where needed
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.data-table').DataTable({
            responsive: true,
            pageLength: 25,
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search records..."
            }
        });
    }
    
    // Initialize Select2 for enhanced select boxes where needed
    if (typeof $.fn.select2 !== 'undefined') {
        $('.select2').select2({
            theme: 'bootstrap-5',
            width: '100%'
        });
        
        // Multi-select with tags
        $('.select2-tags').select2({
            theme: 'bootstrap-5',
            width: '100%',
            tags: true
        });
    }
    
    // Dashboard charts initialization
    const setupCharts = function() {
        if (typeof Chart === 'undefined') return;
        
        // Users registration chart
        const userCtx = document.getElementById('userRegistrationChart');
        if (userCtx) {
            new Chart(userCtx, {
                type: 'line',
                data: {
                    labels: userChartData.labels,
                    datasets: [{
                        label: 'New Users',
                        data: userChartData.data,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            precision: 0
                        }
                    }
                }
            });
        }
        
        // Content statistics chart
        const contentCtx = document.getElementById('contentStatsChart');
        if (contentCtx) {
            new Chart(contentCtx, {
                type: 'bar',
                data: {
                    labels: contentChartData.labels,
                    datasets: [{
                        label: 'Count',
                        data: contentChartData.data,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(255, 206, 86, 0.2)',
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(153, 102, 255, 0.2)',
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)',
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            precision: 0
                        }
                    }
                }
            });
        }
    };
    
    // Initialize charts if the dashboard page is loaded
    if (document.getElementById('admin-dashboard')) {
        setupCharts();
    }
    
    // Image URL preview
    document.querySelectorAll('.image-url-input').forEach(function(input) {
        input.addEventListener('input', function() {
            const previewId = this.getAttribute('data-preview');
            const previewElement = document.getElementById(previewId);
            if (previewElement) {
                if (this.value) {
                    previewElement.src = this.value;
                    previewElement.classList.remove('d-none');
                } else {
                    previewElement.classList.add('d-none');
                }
            }
        });
    });
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Confirm delete actions
    document.querySelectorAll('.confirm-delete').forEach(function(button) {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                event.preventDefault();
            }
        });
    });
    
    // Toggle visibility buttons
    document.querySelectorAll('.toggle-visibility').forEach(function(button) {
        button.addEventListener('click', function() {
            const formId = this.getAttribute('data-form-id');
            const form = document.getElementById(formId);
            if (form) {
                form.submit();
            }
        });
    });
    
    // Date pickers
    if (typeof $.fn.datepicker !== 'undefined') {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true
        });
    }
});

// Function to handle bulk actions
function bulkAction(action, formId) {
    const form = document.getElementById(formId);
    const selectedItems = document.querySelectorAll('input[name="selected_items"]:checked');
    
    if (selectedItems.length === 0) {
        alert('Please select at least one item');
        return false;
    }
    
    if (action === 'delete' && !confirm('Are you sure you want to delete all selected items? This action cannot be undone.')) {
        return false;
    }
    
    document.getElementById('bulk_action').value = action;
    form.submit();
    return true;
}

// Toggle all checkboxes in bulk selection
function toggleAll(source, checkboxName) {
    const checkboxes = document.getElementsByName(checkboxName);
    for (let i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = source.checked;
    }
}
