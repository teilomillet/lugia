const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const modelDropdown = document.getElementById('model-dropdown');

// AddEventListener to the send button
sendBtn.addEventListener('click', () => {
    const userText = userInput.value;
    const selectedModel = modelDropdown.value;
    if (!userText.trim()) return;

    displayMessage(userText, 'user');
    userInput.value = '';

    // Fetch request to your API endpoint
    fetch('http://127.0.0.1:8000/chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model: selectedModel, content: userText }),
    })
    .then(response => response.json())
    .then(data => {
        displayMessage(data.response, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

function displayMessage(text, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);

    // Splitting the text by triple backticks to separate plain text and code blocks
    const segments = text.split('```');

    segments.forEach((segment, index) => {
        if (index % 2 === 0) { // Even indices are treated as plain text
            // Adding plain text directly or wrapped in <p> tags
            if (segment.trim().length > 0) { // Ensure segment is not just empty or whitespace
                const textElement = document.createElement('p');
                textElement.textContent = segment;
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

