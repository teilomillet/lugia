const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const modelDropdown = document.getElementById('model-dropdown');
const conversationPlaceholder = document.getElementById('conversation-placeholder');
const conversationHeader = document.getElementById('conversation-header');
const conversationList = document.getElementById('conversation-list');


sendBtn.addEventListener('click', sendMessage);
document.addEventListener('input', adjustTextareaHeight, false);
document.addEventListener('DOMContentLoaded', initThemeSwitcher);
document.getElementById('conversation-search').addEventListener('input', searchConversations);
document.getElementById('load-more-btn').addEventListener('click', loadMoreConversations);
document.getElementById('new-conversation-btn').addEventListener('click', createNewConversation);

const toggleButton = document.getElementById('toggle-conversation-manager');
const conversationManagerContainer = document.getElementById('conversation-manager-container');
const chatArea = document.getElementById('chat-area');


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
    userInput.style.height = 'auto'; // Reset the height of the text input

    try {
        const response = await fetch('http://127.0.0.1:8000/chat/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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

    const segments = text.split('```');

    segments.forEach((segment, index) => {
        if (index % 2 === 0) {
            // Regular text
            const lines = segment.split('\n');
            let lineContent = '';

            lines.forEach((line, lineIndex) => {
                const indentLevel = (line.match(/^(\s*)/)[1] || '').length / 4;
                lineContent += `<span style="margin-left: ${indentLevel * 15}px;">${line.trim()}</span>`;

                if (lineIndex < lines.length - 1) {
                    lineContent += '<br>';
                }
            });

            const lineElement = document.createElement('div');
            lineElement.classList.add('message-line');
            lineElement.innerHTML = lineContent;
            messageElement.appendChild(lineElement);
        } else {
            // Code block
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
    const response = await fetch(`http://127.0.0.1:8000/conversations/?page=${page}`);
    const data = await response.json();
    return data.conversations;
}

async function switchConversation(conversationFile) {
    await fetch(`http://127.0.0.1:8000/conversations/switch/?conversation_file=${conversationFile}`, { method: 'POST' });
    saveSelectedConversation(conversationFile);
    await loadConversation(conversationFile);

    const conversationItems = conversationList.querySelectorAll('li');
    conversationItems.forEach(item => {
        item.classList.toggle('selected', item.textContent === conversationFile);
    });
}

async function loadConversation(conversationFile) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/conversations/history/?conversation_file=${conversationFile}`);
        const data = await response.json();
        const messages = data.messages;

        conversationPlaceholder.innerHTML = '';

        messages.forEach(message => {
            const sender = message.role === 'user' ? 'user' : 'bot';
            displayMessage(message.content, sender);
        });

        conversationHeader.textContent = conversationFile;
        conversationPlaceholder.scrollTop = conversationPlaceholder.scrollHeight;
    } catch (error) {
        console.error('Error:', error);
    }
}

async function createNewConversation() {
    await fetch('http://127.0.0.1:8000/conversations/new/', { method: 'POST' });
    await loadConversations();

    const newConversationItem = conversationList.lastElementChild;
    newConversationItem.classList.add('new-conversation');
    setTimeout(() => {
        newConversationItem.classList.remove('new-conversation');
    }, 3000);
}

async function loadConversations() {
    const conversations = await listConversations();
    conversationList.innerHTML = '';

    conversations.forEach(conversation => {
        const listItem = document.createElement('li');
        listItem.textContent = conversation;
        listItem.addEventListener('click', () => switchConversation(conversation));
        conversationList.appendChild(listItem);
    });
}

async function loadChat(conversationFile) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/conversations/history/?conversation_file=${conversationFile}`);
        const data = await response.json();
        const messages = data.messages;

        chatBox.innerHTML = '';

        messages.forEach(message => {
            const sender = message.role === 'user' ? 'user' : 'bot';
            displayMessage(message.content, sender);
        });

        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error('Error:', error);
    }
}

loadConversations();