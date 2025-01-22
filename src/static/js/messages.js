const notificationTimeouts = new Map();
const processedNotifications = new Set();

function clearNotificationTimeouts(cardId) {
    const timeouts = notificationTimeouts.get(cardId);
    if (timeouts) {
        timeouts.forEach(clearTimeout);
        notificationTimeouts.delete(cardId);
    }
}

export function createNotification(message, type = 'success') {
    const card = document.createElement('div');
    card.className = `p-4 rounded-lg shadow-lg transition-opacity duration-300 opacity-0 ${
        type === 'error'
            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
            : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'
    }`;
    card.id = `notification-card-${Date.now()}`;
    card.textContent = message;

    let notificationsContainer = document.querySelector('.notifications-container');
    if (!notificationsContainer) {
        notificationsContainer = document.createElement('div');
        notificationsContainer.className = 'notifications-container fixed bottom-0 right-0 z-50 flex flex-col-reverse gap-4 p-4 mb-4';
        document.body.appendChild(notificationsContainer);
    }

    notificationsContainer.appendChild(card);
    processedNotifications.add(card.id);

    const timeouts = [];

    timeouts.push(setTimeout(() => {
        card.classList.remove('opacity-0');
    }, 100));

    timeouts.push(setTimeout(() => {
        card.classList.add('opacity-0');
        timeouts.push(setTimeout(() => {
            card.remove();
            clearNotificationTimeouts(card.id);
            processedNotifications.delete(card.id);
            if (!notificationsContainer.children.length) {
                notificationsContainer.remove();
            }
        }, 300));
    }, 5000));

    notificationTimeouts.set(card.id, timeouts);
}

export function createErrorNotification(message) {
    createNotification(message, 'error');
}

export function createSuccessNotification(message) {
    createNotification(message, 'success');
}

export function initializeNotifications() {
    document.querySelectorAll('[id^="notification-card-"]').forEach((card) => {
        if (processedNotifications.has(card.id)) {
            return;
        }

        const type = card.dataset.messageType;
        const message = card.textContent;

        card.remove();

        createNotification(message, type);
    });
}
