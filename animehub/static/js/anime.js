document.addEventListener('DOMContentLoaded', function() {
    // Handle adding anime to user list
    const animeListForms = document.querySelectorAll('.anime-list-form');
    
    animeListForms.forEach(function(form) {
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
    
    // Video player for YouTube trailer
    const trailerContainer = document.getElementById('anime-trailer');
    if (trailerContainer && trailerContainer.dataset.videoId) {
        const videoId = trailerContainer.dataset.videoId;
        
        // Load YouTube API
        const tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        const firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        
        // Create player when API is ready
        window.onYouTubeIframeAPIReady = function() {
            new YT.Player('anime-trailer', {
                height: '360',
                width: '640',
                videoId: videoId,
                playerVars: {
                    'playsinline': 1,
                    'rel': 0
                }
            });
        };
    }
    
    // Anime filter functionality
    const animeFilterForm = document.getElementById('animeFilterForm');
    
    if (animeFilterForm) {
        const filterInputs = animeFilterForm.querySelectorAll('select, input:not([type="submit"])');
        
        filterInputs.forEach(function(input) {
            input.addEventListener('change', function() {
                animeFilterForm.submit();
            });
        });
    }
    
    // Handle episode progress updates
    const progressInput = document.getElementById('episode_progress');
    const totalEpisodes = document.getElementById('total_episodes');
    
    if (progressInput && totalEpisodes) {
        const max = parseInt(totalEpisodes.value);
        
        progressInput.addEventListener('change', function() {
            const val = parseInt(this.value);
            
            // Ensure the value is within valid range
            if (isNaN(val) || val < 0) {
                this.value = 0;
            } else if (max > 0 && val > max) {
                this.value = max;
            }
            
            // If progress reaches max episodes, offer to mark as completed
            if (max > 0 && val === max) {
                const statusSelect = document.getElementById('status_in_list');
                if (statusSelect && statusSelect.value !== 'completed') {
                    if (confirm('You\'ve reached the final episode. Mark this anime as completed?')) {
                        statusSelect.value = 'completed';
                    }
                }
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
