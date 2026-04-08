document.addEventListener('DOMContentLoaded', function () {
    const chatbotWidget = document.getElementById('c-chatbot-widget');
    const chatbotOpen = document.getElementById('c-chatbot-open');
    const chatbotToggle = document.getElementById('c-chatbot-toggle');
    const chatbotInput = document.getElementById('c-chatbot-input');
    const chatbotSend = document.getElementById('c-chatbot-send');
    const chatbotReset = document.getElementById('c-chatbot-reset');
    const chatbotMessages = document.getElementById('c-chatbot-messages');

    function toggleChat() {
        if (chatbotWidget.classList.contains('chatbot-hidden')) {
            chatbotWidget.classList.remove('chatbot-hidden');
            chatbotOpen.style.display = 'none';
            chatbotInput.focus();
        } else {
            chatbotWidget.classList.add('chatbot-hidden');
            chatbotOpen.style.display = 'flex';
        }
    }

    chatbotOpen.addEventListener('click', toggleChat);
    chatbotToggle.addEventListener('click', toggleChat);

    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        msgDiv.textContent = text;
        chatbotMessages.appendChild(msgDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    function showTyping() {
        const typing = document.createElement('div');
        typing.classList.add('typing-indicator');
        typing.id = 'typing-dots';
        typing.innerHTML = '<span></span><span></span><span></span>';
        chatbotMessages.appendChild(typing);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    function hideTyping() {
        const t = document.getElementById('typing-dots');
        if (t) t.remove();
    }

    function sendMessage() {
        const text = chatbotInput.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        chatbotInput.value = '';
        chatbotSend.disabled = true;
        chatbotInput.disabled = true;
        showTyping();

        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        })
        .then(response => response.json())
        .then(data => {
            hideTyping();
            addMessage(data.response, 'bot');
            chatbotSend.disabled = false;
            chatbotInput.disabled = false;
            chatbotInput.focus();
        })
        .catch(error => {
            hideTyping();
            addMessage('Connection error. Please try again.', 'bot');
            chatbotSend.disabled = false;
            chatbotInput.disabled = false;
        });
    }

    chatbotSend.addEventListener('click', sendMessage);
    chatbotInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    chatbotReset.addEventListener('click', function () {
        addMessage('Switching context...', 'user');
        showTyping();
        fetch('/reset_chat', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                hideTyping();
                addMessage(data.response, 'bot');
            });
    });
});
