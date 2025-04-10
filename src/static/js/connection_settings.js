import { initializeNotifications } from '/static/js/messages.js';

// Store the original endpoint value when the page loads
document.addEventListener('htmx:load', function() {
    const hostInput = document.getElementById('endpoint-input');
    const geminiInput = document.getElementById('gemini-api-key');
    if (hostInput) {
        window.originalEndpoint = hostInput.value;
        updateSaveButtonState();

        // Add input event listener to check for changes
        hostInput.addEventListener('input', updateSaveButtonState);
    }

    if (geminiInput) {
        window.originalGeminiApiKey = geminiInput.value;
        updateSaveButtonState();

        // Add input event listener to check for changes
        geminiInput.addEventListener('input', updateSaveButtonState);
    }
});

function updateSaveButtonState() {
    const hostInput = document.getElementById('endpoint-input');
    const geminiInput = document.getElementById('gemini-api-key');
    const saveButton = document.getElementById('connection-settings-save-button');

    if (saveButton) { // check if we are in the correct page
        const changes = hostInput.value !== window.originalEndpoint || geminiInput.value !== window.originalGeminiApiKey;
        saveButton.disabled = !changes;

        // Optional: Add visual feedback with opacity
        saveButton.style.opacity = changes ? '1' : '0.5';
        saveButton.style.cursor = changes ? 'pointer' : 'not-allowed';
    }
}

// Update the stored value after successful save
document.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.successful) {
        const hostInput = document.getElementById('endpoint-input');
        const geminiInput = document.getElementById('gemini-api-key');
        if (hostInput) {
            window.originalEndpoint = hostInput.value;
            updateSaveButtonState(); // Update button state after save
        }
        if (geminiInput) {
            window.originalGeminiApiKey = geminiInput.value;
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
        const hostInput = document.getElementById('endpoint-input');
        const geminiInput = document.getElementById('gemini-api-key');
        if (hostInput) {
            hostInput.value = window.originalEndpoint;
            updateSaveButtonState(); // Update button state after cancel
        }
        if (geminiInput) {
            geminiInput.value = window.originalGeminiApiKey;
            updateSaveButtonState(); // Update button state after cancel
        }
    }
});
