import { createErrorNotification, initializeNotifications } from '/static/js/messages.js';

const messageClasses = {
  base: "max-w-[70%] p-4 rounded-[20px] mb-4",
  user: "ml-auto bg-blue-500 text-white rounded-br-[5px]",
  assistant: "mr-auto bg-gray-100 dark:bg-gray-800 rounded-bl-[5px]",
  indicator: "inline-flex items-center gap-2 ml-2 align-middle"
};

document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('chat-messages');
    const initialText = localStorage.getItem('initial_text');
    const conversationData = messagesContainer?.dataset?.conversation;

    initializeNotifications();

    if (messagesContainer && conversationData) {
        const conversation = JSON.parse(conversationData);
        if (conversation.messages && conversation.messages.length > 0) {
            renderExistingMessages(conversation.messages);
        }
    }

    if (initialText) {
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            const userMessage = document.createElement('div');
            userMessage.className = `${messageClasses.base} ${messageClasses.user}`;
            userMessage.textContent = initialText;
            messagesContainer.appendChild(userMessage);

            const assistantMessage = document.createElement('div');
            assistantMessage.className = `${messageClasses.base} ${messageClasses.assistant}`;

            const textContainer = document.createElement('div');
            textContainer.className = 'inline';
            assistantMessage.appendChild(textContainer);

            const typingIndicator = createTypingIndicator();
            assistantMessage.appendChild(typingIndicator);

            messagesContainer.appendChild(assistantMessage);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            currentAssistantMessage = assistantMessage;
            currentTextContainer = textContainer;
            currentTypingIndicator = typingIndicator;
            accumulatedContent = '';

            setupSSE(initialText);

            localStorage.removeItem('initial_text');
        }
    }
});

function createTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = messageClasses.indicator;

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce';
        dot.style.animationDelay = `${i * 0.2}s`;
        indicator.appendChild(dot);
    }

    return indicator;
}

let currentAssistantMessage = null;
let currentTextContainer = null;
let currentTypingIndicator = null;
let accumulatedContent = '';
let eventSource = null;

window.addEventListener('beforeunload', function() {
    if (eventSource) {
        eventSource.close();
    }
});

function setupSSE(text) {
    if (eventSource) eventSource.close();

    const url = new URL(window.location.href);
    const conversationId = url.pathname.split('/conversation/')[1];
    const sseUrl = `/api/chat?text=${encodeURIComponent(text)}${conversationId ? `&conversation_id=${conversationId}` : ''}`;
    const chatInput = document.getElementById('chat-input');

    chatInput.disabled = true;
    chatInput.placeholder = "AI is thinking...";

    eventSource = new EventSource(sseUrl);
    console.log('SSE connection established');

    eventSource.onopen = function() {
        console.log('SSE connection opened');
    };

    eventSource.onmessage = function(event) {
        console.log('Message received:', event);
        if (!currentTextContainer) return;

        accumulatedContent += event.data;
        currentTextContainer.innerHTML = accumulatedContent;

        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    };

    eventSource.addEventListener('content', function(event) {
        console.log('Content event received:', event);
        if (!currentTextContainer) return;

        accumulatedContent += event.data;
        currentTextContainer.innerHTML = accumulatedContent;

        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    });

    eventSource.addEventListener('end_of_response', function(event) {
        console.log('End of response received');
        if (currentTypingIndicator) {
            currentTypingIndicator.remove();
        }

        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        const chatInput = document.getElementById('chat-input');
        chatInput.disabled = false;
        chatInput.placeholder = "Ask me anything...";

        currentAssistantMessage = null;
        currentTextContainer = null;
        currentTypingIndicator = null;
        eventSource.close();
    });

    eventSource.onerror = function(error) {
        console.error('SSE error:', error);
        // Only show error if we haven't received any content
        if (currentTextContainer && !accumulatedContent) {
            currentTextContainer.textContent = 'Error: Could not connect to the assistant.';
        }
        if (currentTypingIndicator) {
            currentTypingIndicator.remove();
        }
        if (!accumulatedContent) {
            currentAssistantMessage = null;
            currentTextContainer = null;
            currentTypingIndicator = null;
        }
        const chatInput = document.getElementById('chat-input');
        chatInput.disabled = false;
        chatInput.placeholder = "Ask me anything...";
        eventSource.close();
    };
}

document.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.elt.id === 'chat-input') {
        const chatInput = document.getElementById('chat-input');
        const messagesContainer = document.getElementById('chat-messages');
        const text = chatInput.value;

        chatInput.value = '';

        if (!evt.detail.successful) {
            createErrorNotification('Failed to create conversation');
            return;
        }

        if (evt.detail.xhr.response) {
            if (evt.detail.xhr.response.includes("'status': 'error'")) {
                const errorMatch = evt.detail.xhr.response.match(/'message': '([^']+)'/);
                const errorMessage = errorMatch ? errorMatch[1] : 'An error occurred';
                createErrorNotification(errorMessage);
                return;
            }

            try {
                const response = JSON.parse(evt.detail.xhr.response);

                if (response.status === 'error') {
                    createErrorNotification(response.message || 'An error occurred');
                    return;
                }

                if (response.conversation_id) {
                    localStorage.setItem('initial_text', response.initial_text);
                    window.location.href = `/conversation/${response.conversation_id}`;
                    return;
                }
            } catch (e) {
                console.error('Error parsing response:', e);
            }
        }

        // If we get here, proceed with creating the message UI
        const userMessage = document.createElement('div');
        userMessage.className = `${messageClasses.base} ${messageClasses.user}`;
        userMessage.textContent = text;
        messagesContainer.appendChild(userMessage);

        const assistantMessage = document.createElement('div');
        assistantMessage.className = `${messageClasses.base} ${messageClasses.assistant}`;

        const textContainer = document.createElement('div');
        textContainer.className = 'inline';
        assistantMessage.appendChild(textContainer);

        const typingIndicator = createTypingIndicator();
        assistantMessage.appendChild(typingIndicator);

        messagesContainer.appendChild(assistantMessage);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        currentAssistantMessage = assistantMessage;
        currentTextContainer = textContainer;
        currentTypingIndicator = typingIndicator;
        accumulatedContent = '';

        setupSSE(text);
    }
});

function renderExistingMessages(messages) {
    const messagesContainer = document.getElementById('chat-messages');
    let currentSenderType = null;
    let currentMessageContent = '';

    function createMessageBubble(content, senderType) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${messageClasses.base} ${senderType.toLowerCase() === 'user' ? messageClasses.user : messageClasses.assistant}`;

        if (senderType.toLowerCase() === 'user') {
            messageDiv.textContent = content;
        } else {
            const textContainer = document.createElement('div');
            textContainer.className = 'inline';
            textContainer.innerHTML = content;
            messageDiv.appendChild(textContainer);
        }

        return messageDiv;
    }

    messages.forEach((message, index) => {
        if (currentSenderType === null) {
            currentSenderType = message.senderType;
            currentMessageContent = message.content;
        } else if (currentSenderType === message.senderType) {
            currentMessageContent += message.content;
        } else {
            messagesContainer.appendChild(createMessageBubble(currentMessageContent, currentSenderType));
            currentSenderType = message.senderType;
            currentMessageContent = message.content;
        }

        if (index === messages.length - 1) {
            messagesContainer.appendChild(createMessageBubble(currentMessageContent, currentSenderType));
        }
    });

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
