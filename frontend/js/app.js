// app.js - behavior & network calls (moved from inline script)

const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatHistory = document.getElementById('chat-history');
const voiceInputButton = document.getElementById('voice-input-button');
const fileUploadButton = document.getElementById('file-upload-button');
const resultImageInput = document.getElementById('result-image-input');
const typingIndicator = document.getElementById('typing-indicator');
const BOT_AVATAR_PATH = 'IMG/gemsbotblue.png'; // Change path if you use another bot logo
const typingAvatar = typingIndicator?.querySelector('.bot-reply-avatar');

function showTypingIndicator() {
  if (!typingIndicator) return;
  if (typingAvatar) typingAvatar.src = BOT_AVATAR_PATH;
  // Keep loading row at the bottom, after the latest user message.
  chatHistory.appendChild(typingIndicator);
  typingIndicator.style.display = 'block';
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function hideTypingIndicator() {
  if (!typingIndicator) return;
  typingIndicator.style.display = 'none';
}

function appendMessage(message, sender) {
  const messageDiv = document.createElement('div');
  const messageBubble = document.createElement('div');
  messageBubble.textContent = message;
  messageBubble.style.whiteSpace = 'pre-wrap';
  messageBubble.classList.add('fade-in');

  if (sender === 'user') {
    messageDiv.className = 'flex justify-end';
    messageBubble.className += ' chat-bubble user-bubble';
    messageDiv.appendChild(messageBubble);
  } else {
    messageDiv.className = 'bot-reply-row';
    chatHistory
      .querySelectorAll('.bot-reply-avatar--active')
      .forEach((avatar) => avatar.classList.remove('bot-reply-avatar--active'));
    const botAvatar = document.createElement('img');
    botAvatar.src = BOT_AVATAR_PATH;
    botAvatar.alt = 'GEMS Bot';
    botAvatar.className = 'bot-reply-avatar bot-reply-avatar--active';
    messageDiv.appendChild(botAvatar);
    messageBubble.className += ' chat-bubble bot-bubble';
    messageDiv.appendChild(messageBubble);
  }

  chatHistory.appendChild(messageDiv);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const userMessage = userInput.value.trim();
  if (!userMessage) return;

  appendMessage(userMessage, 'user');
  userInput.value = '';

  showTypingIndicator();

  try {
    // if you later change API path, update here
    const response = await fetch('https://gems-chatbot-docker.onrender.com/chat', {


      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage }),
    });

    hideTypingIndicator();

    if (!response.ok) {
      appendMessage(`Error: Server returned ${response.status}`, 'gemini');
      return;
    }

    const data = await response.json();
    if (data.response) {
      appendMessage(data.response, 'gemini');
    } else if (data.error) {
      appendMessage(`⚠️ ${data.error}`, 'gemini');
    } else {
      appendMessage('⚠️ Unexpected response from server.', 'gemini');
    }
  } catch (err) {
    hideTypingIndicator();
    appendMessage(
      '🚨 Failed to connect to backend. Make sure Flask is running.',
      'gemini'
    );
    console.error('Fetch error:', err);
  }
});

voiceInputButton.addEventListener('click', () => {
  alert('Voice input is not yet implemented, but it will be soon!');
});

fileUploadButton.addEventListener('click', () => {
  if (resultImageInput) {
    resultImageInput.click();
  }
});

if (resultImageInput) {
  resultImageInput.addEventListener('change', async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowedTypes = ['image/jpeg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
      appendMessage('Please upload a valid JPG or PNG image.', 'gemini');
      resultImageInput.value = '';
      return;
    }

    appendMessage(`Uploaded result image: ${file.name}`, 'user');
    showTypingIndicator();

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('https://gems-chatbot-docker.onrender.com/analyze-result', {
        method: 'POST',
        body: formData,
      });

      hideTypingIndicator();
      const data = await response.json();

      if (!response.ok) {
        appendMessage(`OCR Error: ${data.error || 'Request failed.'}`, 'gemini');
        return;
      }

      const courses = Array.isArray(data.recommended_courses)
        ? data.recommended_courses
        : [];
      const strengths = Array.isArray(data.strength_subjects)
        ? data.strength_subjects
        : [];

      const summaryLines = [
        `Name: ${data.name || 'Unknown'}`,
        `Average: ${typeof data.average === 'number' ? data.average : 'N/A'}%`,
        strengths.length
          ? `Strongest Subjects: ${strengths.join(', ')}`
          : 'Strongest Subjects: N/A',
        courses.length
          ? `Recommended Courses: ${courses.join(', ')}`
          : 'Recommended Courses: N/A',
      ];

      appendMessage(summaryLines.join('\n'), 'gemini');
    } catch (err) {
      hideTypingIndicator();
      appendMessage('Failed to upload result image. Check if Flask is running.', 'gemini');
      console.error('Result upload error:', err);
    } finally {
      resultImageInput.value = '';
    }
  });
}
