const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const modelDropdown = document.getElementById('model-dropdown');
const conversationPlaceholder = document.getElementById('conversation-placeholder');
const conversationHeader = document.getElementById('conversation-header');
const conversationList = document.getElementById('conversation-list');
const BASE_URL = 'http://127.0.0.1:8000';

sendBtn.addEventListener('click', sendMessage);
document.addEventListener('input', adjustTextareaHeight, false);
document.addEventListener('DOMContentLoaded', initThemeSwitcher);
document.getElementById('conversation-search').addEventListener('input', debounce(searchConversations, 300));
document.getElementById('load-more-btn').addEventListener('click', loadMoreConversations);
document.getElementById('new-conversation-btn').addEventListener('click', createNewConversation);
document.getElementById('clear-conversation-btn').addEventListener('click', clearConversation);

const toggleButton = document.getElementById('toggle-conversation-manager');
const conversationManagerContainer = document.getElementById('conversation-manager-container');
const chatArea = document.getElementById('chat-area');
const loadingSpinner = document.getElementById('loading-spinner');
const errorMessage = document.getElementById('error-message');

toggleButton.addEventListener('click', () => {
    conversationManagerContainer.classList.toggle('collapsed');
    if (conversationManagerContainer.classList.contains('collapsed')) {
        chatArea.style.width = '100%';
    } else {
        chatArea.style.width = 'calc(100% - 300px)';
    }
});

async function sendMessage() {
    const userText = userInput.value.trim();
    const selectedModel = modelDropdown.value;
    if (!userText) return;

    displayMessage(userText, 'user');
    userInput.value = '';
    userInput.style.height = 'auto';

    loadingSpinner.style.display = 'block';
    errorMessage.style.display = 'none';

    try {
        const response = await fetch(`${BASE_URL}/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: selectedModel, content: userText }),
        });

        if (!response.ok) {
            throw new Error('Request failed');
        }

        const data = await response.json();
        displayMessage(data.response, 'bot');
    } catch (error) {
        console.error('Error:', error);
        errorMessage.textContent = 'An error occurred. Please try again.';
        errorMessage.style.display = 'block';
    } finally {
        loadingSpinner.style.display = 'none';
    }
}

function displayMessage(text, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);

    const segments = text.split('```');

    segments.forEach((segment, index) => {
        if (index % 2 === 0) {
            const lines = segment.split('\n');
            const lineElement = document.createElement('div');
            lineElement.classList.add('message-line');
            lines.forEach((line, lineIndex) => {
                const indentLevel = (line.match(/^(\s*)/)[1] || '').length / 4;
                const spanElement = document.createElement('span');
                spanElement.style.marginLeft = `${indentLevel * 15}px`;
                spanElement.textContent = line.trim();
                
                lineElement.appendChild(spanElement);
                
                if (lineIndex < lines.length - 1) {
                    lineElement.appendChild(document.createElement('br'));
                }
            });
            messageElement.appendChild(lineElement);
        } else {
            const preElement = document.createElement('pre');
            const codeElement = document.createElement('code');
            codeElement.textContent = segment;
            preElement.appendChild(codeElement);
            messageElement.appendChild(preElement);
            hljs.highlightElement(codeElement);
        }
    });

    conversationPlaceholder.appendChild(messageElement);
    conversationPlaceholder.scrollTop = conversationPlaceholder.scrollHeight;
}

function adjustTextareaHeight(event) {
    if (event.target.id === 'user-input') {
        event.target.style.height = 'auto';
        event.target.style.height = Math.min(event.target.scrollHeight, 500) + 'px';
    }
}

function initThemeSwitcher() {
    const themeSwitcher = document.getElementById('theme-switcher');

    themeSwitcher.addEventListener('click', () => {
        document.body.classList.toggle('night-mode');
        themeSwitcher.textContent = document.body.classList.contains('night-mode')
            ? 'Switch to Day Mode'
            : 'Switch to Night Mode';
    });
}

function saveSelectedConversation(conversationFile) {
    localStorage.setItem('selectedConversation', conversationFile);
}

function getSelectedConversation() {
    return localStorage.getItem('selectedConversation');
}

function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

function searchConversations(event) {
    const searchTerm = event.target.value.toLowerCase();
    const conversationItems = conversationList.querySelectorAll('li');
    conversationItems.forEach(item => {
        const conversationName = item.textContent.toLowerCase();
        item.style.display = conversationName.includes(searchTerm) ? 'block' : 'none';
    });
}

async function loadMoreConversations() {
    const nextPage = currentPage + 1;
    const conversations = await listConversations(nextPage);
    displayConversations(conversations);
    currentPage = nextPage;
}

async function listConversations(page = 1) {
    const response = await fetch(`${BASE_URL}/conversations/?page=${page}`);
    const data = await response.json();
    return data.conversations.reverse();
}

async function switchConversation(conversationFile) {
    await fetch(`${BASE_URL}/conversations/switch/?conversation_file=${conversationFile}`, { method: 'POST' });
    saveSelectedConversation(conversationFile);
    await loadConversation(conversationFile);

    const conversationItems = conversationList.querySelectorAll('li');
    conversationItems.forEach(item => {
        item.classList.toggle('selected', item.textContent === conversationFile);
    });
}

async function loadConversation(conversationFile) {
    try {
        const response = await fetch(`${BASE_URL}/conversations/history/?conversation_file=${conversationFile}`);
        const data = await response.json();
        const messages = data.messages;

        conversationPlaceholder.innerHTML = '';

        messages.forEach(message => {
            const sender = message.role === 'user' ? 'user' : 'bot';
            displayMessage(message.content, sender);
        });

        conversationHeader.textContent = conversationFile;
    } catch (error) {
        console.error('Error:', error);
    }
}

async function createNewConversation() {
    const response = await fetch(`${BASE_URL}/conversations/new/`, { method: 'POST' });
    const data = await response.json();
    const conversationFile = data.conversation_file;
    
    await loadConversations();

    const newConversationItem = conversationList.querySelector(`[data-conversation="${conversationFile}"]`);
    newConversationItem.classList.add('new-conversation');
    setTimeout(() => {
        newConversationItem.classList.remove('new-conversation');
    }, 3000);
}

async function deleteConversation(conversationFile) {
    try {
        const response = await fetch(`${BASE_URL}/conversations/${conversationFile}`, { method: 'DELETE' });
        if (response.ok) {
            await loadConversations();
            if (getSelectedConversation() === conversationFile) {
                await createNewConversation();
            }
        } else {
            throw new Error('Failed to delete conversation');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function createConversationItem(conversation) {
    const listItem = document.createElement('li');
    listItem.textContent = conversation;
    listItem.setAttribute('data-conversation', conversation);
    listItem.addEventListener('click', () => switchConversation(conversation));
    
    const deleteButton = document.createElement('button');
    deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
    deleteButton.classList.add('delete-conversation-btn');
    deleteButton.addEventListener('click', (event) => {
        event.stopPropagation();
        deleteConversation(conversation);
    });
    
    listItem.appendChild(deleteButton);
    return listItem;
}

async function loadConversations() {
    const conversations = await listConversations();
    conversationList.innerHTML = '';

    conversations.forEach(conversation => {
        const listItem = createConversationItem(conversation);
        conversationList.appendChild(listItem);
    });
}

async function loadChat() {
    const selectedConversation = getSelectedConversation();
    if (selectedConversation) {
        await switchConversation(selectedConversation);
    } else {
        await createNewConversation();
    }
}

function clearConversation() {
    conversationPlaceholder.innerHTML = '';
}

loadConversations();
loadChat();