// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const suggestionsContainer = document.getElementById('suggestions');
const statusBadge = document.getElementById('status-badge');
const statusText = document.getElementById('status-text');
const statusIcon = document.getElementById('status-icon');
const aiModeText = document.getElementById('ai-mode');
const memoryCount = document.getElementById('memory-count');
const responseCount = document.getElementById('response-count');

// State
let messageCount = 0;

// Initialize
window.onload = function() {
    loadSuggestions();
    checkStatus();
    updateStats();
    
    // Set up event listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Focus on input
    userInput.focus();
    
    // Auto-check status every 30 seconds
    setInterval(checkStatus, 30000);
};

// Load suggestions from server
function loadSuggestions() {
    fetch('/suggestions')
        .then(response => response.json())
        .then(data => {
            if (data.suggestions) {
                suggestionsContainer.innerHTML = '';
                data.suggestions.forEach(suggestion => {
                    const button = document.createElement('button');
                    button.textContent = suggestion;
                    button.onclick = () => sendSuggestion(suggestion);
                    suggestionsContainer.appendChild(button);
                });
            }
        })
        .catch(error => {
            console.error('Error loading suggestions:', error);
        });
}

// Send message
function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) {
        showToast('Please type a message!', 'warning');
        return;
    }
    
    // Add user message
    addMessage(message, 'user');
    userInput.value = '';
    
    // Disable input while processing
    userInput.disabled = true;
    sendBtn.disabled = true;
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to server
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        removeTypingIndicator();
        
        if (data.response === 'clear_chat') {
            clearChat();
            return;
        }
        
        if (data.error) {
            addMessage('Sorry, there was an error. Please try again.', 'bot');
        } else {
            addMessage(data.response, 'bot', data.timestamp, data.ai_generated);
        }
        
        // Update stats
        messageCount++;
        updateStats();
    })
    .catch(error => {
        removeTypingIndicator();
        addMessage('Network error. Please check your connection.', 'bot');
        console.error('Error:', error);
    })
    .finally(() => {
        // Re-enable input
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    });
}

// Handle Enter key
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Send suggestion
function sendSuggestion(text) {
    userInput.value = text;
    sendMessage();
}

// Send topic
function sendTopic(topic) {
    const questions = {
        'math': 'Explain calculus concepts and provide examples',
        'science': 'Explain the scientific method with real-world examples',
        'programming': 'Explain Python functions with code examples',
        'history': 'Explain the causes of World War II',
        'writing': 'How to write a good essay introduction?',
        'study tips': 'What are the most effective study techniques?'
    };
    
    userInput.value = questions[topic] || `Tell me about ${topic}`;
    sendMessage();
}

// Add message to chat
function addMessage(text, sender, timestamp = null, aiGenerated = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const time = timestamp || getCurrentTime();
    const aiBadge = aiGenerated ? '<span class="ai-badge">AI</span>' : '';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${sender === 'user' ? 'You' : 'StudyBot'}</span>
                ${aiBadge}
            </div>
            <div class="message-text">${formatResponse(text)}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Format response text
function formatResponse(text) {
    // Convert markdown-like formatting
    let formatted = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h3>$1</h3>')
        .replace(/^# (.*$)/gm, '<h3>$1</h3>')
        .replace(/\n/g, '<br>')
        .replace(/•\s*(.*?)(<br>|$)/g, '• $1<br>');
    
    return formatted;
}

// Get current time
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Scroll to bottom
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">StudyBot</span>
                <span class="ai-badge">AI</span>
            </div>
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Clear chat
function clearChat() {
    fetch('/clear', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear UI
            const messages = chatMessages.querySelectorAll('.message:not(.welcome)');
            messages.forEach(message => message.remove());
            
            // Reset counters
            messageCount = 0;
            updateStats();
            
            showToast('Chat cleared successfully!', 'success');
            
            // Add welcome message
            setTimeout(() => {
                addMessage('Chat cleared! How can I help you with your studies today?', 'bot');
            }, 500);
        }
    });
}

// Check status
function checkStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            if (data.ai_enabled) {
                statusText.textContent = 'AI Enabled';
                aiModeText.textContent = 'Gemini AI Active';
                statusIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
                statusIcon.style.background = 'linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%)';
            } else {
                statusText.textContent = 'Fallback Mode';
                aiModeText.textContent = 'Basic Mode Active';
                statusIcon.innerHTML = '<i class="fas fa-info-circle"></i>';
                statusIcon.style.background = 'linear-gradient(135deg, #ff9800 0%, #ffc107 100%)';
            }
            
            memoryCount.textContent = data.conversation_history;
        })
        .catch(error => {
            console.error('Status check failed:', error);
            statusText.textContent = 'Offline';
            aiModeText.textContent = 'Connection Error';
            statusIcon.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
            statusIcon.style.background = 'linear-gradient(135deg, #f44336 0%, #e53935 100%)';
        });
}

// Update stats
function updateStats() {
    responseCount.textContent = messageCount;
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.display = 'block';
    
    // Set color based on type
    switch(type) {
        case 'success':
            toast.style.background = '#4CAF50';
            break;
        case 'warning':
            toast.style.background = '#ff9800';
            break;
        case 'error':
            toast.style.background = '#f44336';
            break;
        default:
            toast.style.background = '#333';
    }
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// Show help
function showHelp() {
    const helpText = `
    **StudyBot Help Guide**
    
    **Features:**
    • AI-powered study assistance
    • Subject explanations (Math, Science, Programming, etc.)
    • Study techniques and tips
    • Assignment guidance
    • Conversation memory
    
    **How to use:**
    1. Ask specific questions for best results
    2. Use the quick suggestion buttons
    3. Click topic buttons on the right
    4. Type "help" for more options
    5. Type "clear" to reset conversation
    
    **Example Questions:**
    • "Explain photosynthesis"
    • "How to solve quadratic equations?"
    • "Python function examples"
    • "Best study methods for exams"
    • "How to write a research paper?"
    
    **Tips:**
    • The more specific your question, the better the answer
    • Use the sidebar topics for quick access
    • AI mode requires an API key in .env file
    `;
    
    addMessage(helpText, 'bot', null, false);
}

// Add typing animation style
const style = document.createElement('style');
style.textContent = `
    .typing-dots {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 10px 0;
    }
    
    .typing-dots span {
        width: 8px;
        height: 8px;
        background: #667eea;
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out;
    }
    
    .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
    .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
    .typing-dots span:nth-child(3) { animation-delay: 0s; }
    
    @keyframes bounce {
        0%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-6px); }
    }
`;
document.head.appendChild(style);