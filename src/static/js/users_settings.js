// Export functions to make them available globally
window.togglePasswordVisibility = function(inputName, show) {
    const input = document.querySelector(`input[name="${inputName}"]`);
    if (input) {
        input.type = show ? 'text' : 'password';
    }
}

window.closeModal = function() {
    const modal = document.querySelector('#modal');
    if (modal) {
        modal.innerHTML = '';
    }
}

function updateSaveButtonState(form) {
    const password = form.querySelector('input[name="password"]').value;
    const confirm = form.querySelector('input[name="password_confirm"]').value;
    const saveButton = form.querySelector('button[type="submit"]');

    if (password || confirm) {
        const passwordsMatch = password === confirm;
        saveButton.disabled = !passwordsMatch;
        saveButton.style.opacity = passwordsMatch ? '1' : '0.5';
        saveButton.style.cursor = passwordsMatch ? 'pointer' : 'not-allowed';
    } else {
        saveButton.disabled = false;
        saveButton.style.opacity = '1';
        saveButton.style.cursor = 'pointer';
    }
}

function validatePasswordsAndSubmit(form) {
    const password = form.querySelector('input[name="password"]').value;
    const confirm = form.querySelector('input[name="password_confirm"]').value;

    if (password || confirm) {
        if (password !== confirm) {
            return false;
        }
    }

    closeModal();
    return true;
}

document.addEventListener('htmx:afterSettle', function() {
    const form = document.querySelector('form');
    if (form) {
        const passwordInputs = form.querySelectorAll('input[type="password"]');
        passwordInputs.forEach(input => {
            input.addEventListener('input', () => updateSaveButtonState(form));
        });
        updateSaveButtonState(form);
    }
});
