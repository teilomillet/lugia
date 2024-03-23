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
            // Wrapping code in <pre> and <code> tags for formatting
            const preElement = document.createElement('pre');
            const codeElement = document.createElement('code');
            codeElement.textContent = segment;
            preElement.appendChild(codeElement);
            messageElement.appendChild(preElement);

            // Apply syntax highlighting
            hljs.highlightElement(codeElement);
        }
    });

    const conversationPlaceholder = document.getElementById('conversation-placeholder');
    conversationPlaceholder.appendChild(messageElement);
    conversationPlaceholder.scrollTop = conversationPlaceholder.scrollHeight; // Auto-scroll to the latest message
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

// Conversation selection persistence
function saveSelectedConversation(conversationFile) {
    localStorage.setItem('selectedConversation', conversationFile);
}

function getSelectedConversation() {
    return localStorage.getItem('selectedConversation');
}

// Conversation search
function searchConversations(searchTerm) {
    const conversationItems = document.querySelectorAll('#conversation-list li');
    conversationItems.forEach(item => {
        const conversationName = item.textContent.toLowerCase();
        if (conversationName.includes(searchTerm.toLowerCase())) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// Load more conversations (lazy loading)
async function loadMoreConversations() {
    const nextPage = currentPage + 1;
    const conversations = await listConversations(nextPage);
    displayConversations(conversations);
    currentPage = nextPage;
}

async function listConversations(page = 1) {
    const response = await fetch(`http://127.0.0.1:8000/conversations/?page=${page}`);
    const data = await response.json();
    return data.conversations;
}

async function switchConversation(conversationFile) {
    await fetch(`http://127.0.0.1:8000/conversations/switch/?conversation_file=${conversationFile}`, { method: 'POST' });
    saveSelectedConversation(conversationFile);
    await loadConversation(conversationFile);

    // Update selected conversation styling
    const conversationItems = document.querySelectorAll('#conversation-list li');
    conversationItems.forEach(item => {
        if (item.textContent === conversationFile) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
}

async function loadConversation(conversationFile) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/conversations/history/?conversation_file=${conversationFile}`);
        const data = await response.json();
        const messages = data.messages;

        const conversationPlaceholder = document.getElementById('conversation-placeholder');
        conversationPlaceholder.innerHTML = '';

        messages.forEach(message => {
            const sender = message.role === 'user' ? 'user' : 'bot';
            displayMessage(message.content, sender);
        });

        // Update conversation header
        const conversationHeader = document.getElementById('conversation-header');
        conversationHeader.textContent = conversationFile;

        // Scroll to the bottom of the conversation placeholder
        conversationPlaceholder.scrollTop = conversationPlaceholder.scrollHeight;
    } catch (error) {
        console.error('Error:', error);
    }
}

async function createNewConversation() {
    await fetch('http://127.0.0.1:8000/conversations/new/', { method: 'POST' });
    await loadConversations();

    // Provide visual cue for new conversation
    const conversationList = document.getElementById('conversation-list');
    const newConversationItem = conversationList.lastElementChild;
    newConversationItem.classList.add('new-conversation');
    setTimeout(() => {
        newConversationItem.classList.remove('new-conversation');
    }, 3000);
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

async function loadChat(conversationFile) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/conversations/history/?conversation_file=${conversationFile}`);
        const data = await response.json();
        const messages = data.messages;

        clearChatBox();

        messages.forEach(message => {
            const sender = message.role === 'user' ? 'user' : 'bot';
            displayMessage(message.content, sender);
        });

        // Scroll to the bottom of the chat box
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error('Error:', error);
    }
}

document.getElementById('conversation-search').addEventListener('input', function() {
    const searchTerm = this.value;
    searchConversations(searchTerm);
});

document.getElementById('load-more-btn').addEventListener('click', loadMoreConversations);

document.getElementById('new-conversation-btn').addEventListener('click', createNewConversation);



// Load conversations when the page loads
loadConversations();

