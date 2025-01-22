import { initializeNotifications } from '/static/js/messages.js';

// Store the original endpoint value when the page loads
document.addEventListener('htmx:load', function() {
    const input = document.getElementById('endpoint-input');
    if (input) {
        window.originalEndpoint = input.value;
        updateSaveButtonState();

        // Add input event listener to check for changes
        input.addEventListener('input', updateSaveButtonState);
    }
});

// Function to update Save button state
function updateSaveButtonState() {
    const input = document.getElementById('endpoint-input');
    const saveButton = document.querySelector('button[type="submit"]');

    if (input && saveButton) {
        const hasChanged = input.value !== window.originalEndpoint;
        saveButton.disabled = !hasChanged;

        // Optional: Add visual feedback with opacity
        saveButton.style.opacity = hasChanged ? '1' : '0.5';
        saveButton.style.cursor = hasChanged ? 'pointer' : 'not-allowed';
    }
}

// Update the stored value after successful save
document.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful) {
        const input = document.getElementById('endpoint-input');
        if (input) {
            window.originalEndpoint = input.value;
            updateSaveButtonState(); // Update button state after save
        }
    }
});

// Initialize notifications after HTMX content swap
document.addEventListener('htmx:afterSwap', function() {
    initializeNotifications();
});

// Handle cancel button click
document.addEventListener('click', function(evt) {
    if (evt.target.type === 'reset') {
        evt.preventDefault();
        const input = document.getElementById('endpoint-input');
        if (input) {
            input.value = window.originalEndpoint;
            updateSaveButtonState(); // Update button state after cancel
        }
    }
});
