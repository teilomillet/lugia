const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const modelDropdown = document.getElementById('model-dropdown');

// AddEventListener to the send button
sendBtn.addEventListener('click', sendMessage);

async function sendMessage() {
    const userText = userInput.value;
    const selectedModel = modelDropdown.value;
    if (!userText.trim()) return;

    displayMessage(userText, 'user');
    userInput.value = '';

    try {
        const response = await fetch('http://127.0.0.1:8000/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ model: selectedModel, content: userText }),
        });
        const data = await response.json();
        displayMessage(data.response, 'bot');
    } catch (error) {
        console.error('Error:', error);
    }
}

function displayMessage(text, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);

    // Splitting the text by triple backticks to separate plain text and code blocks
    const segments = text.split('```');

    segments.forEach((segment, index) => {
        if (index % 2 === 0) { // Even indices are treated as plain text
            if (segment.trim().length > 0) {
                const textElement = document.createElement('div'); // Use 'div' for block-level container
                // Replace line breaks with <br> tags for visual representation
                textElement.innerHTML = segment.replace(/\n/g, '<br>');
                messageElement.appendChild(textElement);
            }
        } else { // Odd indices are code blocks
            // Wrapping code in <pre><code> tags for formatting
            const preElement = document.createElement('pre');
            const codeElement = document.createElement('code');
            codeElement.textContent = segment;
            preElement.appendChild(codeElement);
            messageElement.appendChild(preElement);

            // Apply syntax highlighting
            hljs.highlightElement(codeElement);
        }
    });

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the latest message
}
// New code for dynamically adjusting the textarea height
document.addEventListener('input', function(event) {
    if (event.target.id === 'user-input') {
        event.target.style.height = 'auto'; // Reset height to recalculate
        event.target.style.height = event.target.scrollHeight + 'px';
    }
}, false);

// Night mode switcher
document.addEventListener('DOMContentLoaded', function() {
    const themeSwitcher = document.getElementById('theme-switcher');

    themeSwitcher.addEventListener('click', () => {
        document.body.classList.toggle('night-mode');
        
        // Update the button text based on the current theme
        if (document.body.classList.contains('night-mode')) {
            themeSwitcher.textContent = 'Switch to Day Mode';
        } else {
            themeSwitcher.textContent = 'Switch to Night Mode';
        }
    });
});

// New functions for conversation management
async function listConversations() {
    const response = await fetch('http://127.0.0.1:8000/conversations/');
    const data = await response.json();
    return data.conversations;
}

async function createNewConversation() {
    await fetch('http://127.0.0.1:8000/conversations/new/', { method: 'POST' });
    await loadConversations();
}

async function switchConversation(conversationFile) {
    await fetch(`http://127.0.0.1:8000/conversations/switch/?conversation_file=${conversationFile}`, { method: 'POST' });
    clearChatBox();
    await loadChat();
}

async function loadConversations() {
    const conversations = await listConversations();
    const conversationList = document.getElementById('conversation-list');
    conversationList.innerHTML = '';

    conversations.forEach(conversation => {
        const listItem = document.createElement('li');
        listItem.textContent = conversation;
        listItem.addEventListener('click', () => switchConversation(conversation));
        conversationList.appendChild(listItem);
    });
}

function clearChatBox() {
    chatBox.innerHTML = '';
}

async function loadChat() {
    try {
        const response = await fetch('http://127.0.0.1:8000/conversations/history/');
        const data = await response.json();
        const messages = data.messages;

        clearChatBox();

        messages.forEach(message => {
            const sender = message.role === 'user' ? 'user' : 'bot';
            displayMessage(message.content, sender);
        });
    } catch (error) {
        console.error('Error:', error);
    }
}

document.getElementById('new-conversation-btn').addEventListener('click', createNewConversation);

// Load conversations when the page loads
loadConversations();