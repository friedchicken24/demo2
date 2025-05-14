document.addEventListener('DOMContentLoaded', function() {
    // Handle adding manga to user list
    const mangaListForms = document.querySelectorAll('.manga-list-form');
    
    mangaListForms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            // If the form has no list selected and it's a new addition, show the list selection modal
            const listIdInput = form.querySelector('input[name="list_id"]');
            const existingItemInput = form.querySelector('input[name="existing_item"]');
            
            if (!listIdInput.value && (!existingItemInput || existingItemInput.value !== 'true')) {
                event.preventDefault();
                
                // Show list selection modal
                const listModal = new bootstrap.Modal(document.getElementById('listSelectionModal'));
                listModal.show();
                
                // Store the form ID in the modal for reference
                document.getElementById('listSelectionModal').setAttribute('data-source-form', form.id);
            }
        });
    });
    
    // Handle list selection from modal
    const listSelectionForm = document.getElementById('listSelectionForm');
    if (listSelectionForm) {
        listSelectionForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Get selected list ID and status
            const listId = document.getElementById('modal_list_id').value;
            const status = document.getElementById('modal_status').value;
            
            // Get source form ID from modal
            const sourceFormId = document.getElementById('listSelectionModal').getAttribute('data-source-form');
            const sourceForm = document.getElementById(sourceFormId);
            
            // Update source form inputs
            if (sourceForm) {
                sourceForm.querySelector('input[name="list_id"]').value = listId;
                sourceForm.querySelector('input[name="status"]').value = status;
                
                // Close the modal
                bootstrap.Modal.getInstance(document.getElementById('listSelectionModal')).hide();
                
                // Submit the original form
                sourceForm.submit();
            }
        });
    }
    
    // Handle rating submissions
    const ratingForms = document.querySelectorAll('.rating-form');
    
    ratingForms.forEach(function(form) {
        const ratingInputs = form.querySelectorAll('input[name="score"]');
        
        ratingInputs.forEach(function(input) {
            input.addEventListener('click', function() {
                // Auto-submit the form when a rating is selected
                form.submit();
            });
        });
    });
    
    // Manga filter functionality
    const mangaFilterForm = document.getElementById('mangaFilterForm');
    
    if (mangaFilterForm) {
        const filterInputs = mangaFilterForm.querySelectorAll('select, input:not([type="submit"])');
        
        filterInputs.forEach(function(input) {
            input.addEventListener('change', function() {
                mangaFilterForm.submit();
            });
        });
    }
    
    // Handle chapter progress updates
    const progressInput = document.getElementById('chapter_progress');
    const totalChapters = document.getElementById('total_chapters');
    
    if (progressInput && totalChapters) {
        const max = parseInt(totalChapters.value);
        
        progressInput.addEventListener('change', function() {
            const val = parseInt(this.value);
            
            // Ensure the value is within valid range
            if (isNaN(val) || val < 0) {
                this.value = 0;
            } else if (max > 0 && val > max) {
                this.value = max;
            }
            
            // If progress reaches max chapters, offer to mark as completed
            if (max > 0 && val === max) {
                const statusSelect = document.getElementById('status_in_list');
                if (statusSelect && statusSelect.value !== 'completed_manga') {
                    if (confirm('You\'ve reached the final chapter. Mark this manga as completed?')) {
                        statusSelect.value = 'completed_manga';
                    }
                }
            }
        });
    }
    
    // Volume progress handling
    const volumeInput = document.getElementById('volume_progress');
    const totalVolumes = document.getElementById('total_volumes');
    
    if (volumeInput && totalVolumes) {
        const max = parseInt(totalVolumes.value);
        
        volumeInput.addEventListener('change', function() {
            const val = parseInt(this.value);
            
            // Ensure the value is within valid range
            if (isNaN(val) || val < 0) {
                this.value = 0;
            } else if (max > 0 && val > max) {
                this.value = max;
            }
        });
    }
});

// Function to show/hide comment replies
function toggleReplies(commentId) {
    const repliesContainer = document.getElementById('replies-' + commentId);
    if (repliesContainer) {
        repliesContainer.classList.toggle('d-none');
        
        const toggleButton = document.querySelector(`.toggle-replies[data-comment-id="${commentId}"]`);
        if (toggleButton) {
            if (repliesContainer.classList.contains('d-none')) {
                toggleButton.textContent = 'Show Replies';
            } else {
                toggleButton.textContent = 'Hide Replies';
            }
        }
    }
}
