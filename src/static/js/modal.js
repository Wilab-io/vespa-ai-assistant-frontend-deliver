// Initialize modal event listeners after HTMX content swap
document.addEventListener('htmx:afterSettle', function() {
    const modalBackdrop = document.querySelector('.modal-backdrop');
    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', closeModal);
    }
});
