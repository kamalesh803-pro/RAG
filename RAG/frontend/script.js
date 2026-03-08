// ================================================================
//  RAG Web Application — Client Logic
// ================================================================

const API = '';  // same-origin

// ── DOM refs ────────────────────────────────────────────────────
const fileInput       = document.getElementById('file-input');
const uploadZone      = document.getElementById('upload-zone');
const uploadBtn       = document.getElementById('upload-btn');
const fileList        = document.getElementById('file-list');
const notification    = document.getElementById('notification');
const chatMessages    = document.getElementById('chat-messages');
const questionInput   = document.getElementById('question-input');
const sendBtn         = document.getElementById('send-btn');
const clearBtn        = document.getElementById('clear-btn');
const welcomeScreen   = document.getElementById('welcome-screen');

let selectedFile = null;
let isProcessing = false;

// ── File selection ──────────────────────────────────────────────
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) selectFile(file);
});

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) selectFile(file);
});

function selectFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'txt'].includes(ext)) {
        showNotification('Please select a PDF or TXT file.', 'error');
        return;
    }
    selectedFile = file;
    uploadBtn.disabled = false;
    showNotification(`Selected: ${file.name}`, 'success');
}

// ── Upload ──────────────────────────────────────────────────────
uploadBtn.addEventListener('click', async () => {
    if (!selectedFile || isProcessing) return;
    await uploadFile(selectedFile);
});

async function uploadFile(file) {
    isProcessing = true;
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Processing…';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API}/upload`, {
            method: 'POST',
            body: formData,
        });

        const data = await res.json();

        if (res.ok && data.success) {
            addFileItem(file.name, data.details);
            showNotification(data.message, 'success');
            // hide welcome screen once a doc is uploaded
            if (welcomeScreen) welcomeScreen.style.display = 'none';
        } else {
            showNotification(data.detail || data.message || 'Upload failed', 'error');
        }
    } catch (err) {
        showNotification('Connection error — is the server running?', 'error');
    } finally {
        isProcessing = false;
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload & Index';
        selectedFile = null;
        fileInput.value = '';
    }
}

function addFileItem(name, details) {
    const div = document.createElement('div');
    div.className = 'file-item';
    const icon = name.endsWith('.pdf') ? '📄' : '📝';
    const chunks = details ? `${details.chunks} chunks` : '';
    div.innerHTML = `
        <span class="file-icon">${icon}</span>
        <span class="file-name">${name}</span>
        <span class="file-status">${chunks} ✓</span>
    `;
    fileList.appendChild(div);
}

// ── Ask Question ────────────────────────────────────────────────
sendBtn.addEventListener('click', () => sendQuestion());
questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
    }
});

async function sendQuestion() {
    const q = questionInput.value.trim();
    if (!q || isProcessing) return;

    // hide welcome
    if (welcomeScreen) welcomeScreen.style.display = 'none';

    appendMessage(q, 'user');
    questionInput.value = '';
    isProcessing = true;
    sendBtn.disabled = true;

    const typingEl = showTypingIndicator();

    try {
        const res = await fetch(`${API}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: q }),
        });

        const data = await res.json();
        removeTypingIndicator(typingEl);

        if (res.ok) {
            appendMessage(data.answer, 'ai', data.sources);
        } else {
            appendMessage(data.detail || 'Something went wrong.', 'ai');
        }
    } catch (err) {
        removeTypingIndicator(typingEl);
        appendMessage('Connection error — is the server running?', 'ai');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

// ── Chat helpers ────────────────────────────────────────────────
function appendMessage(text, role) {
    const wrapper = document.createElement('div');
    wrapper.className = `message ${role}`;

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = role === 'user' ? 'You' : 'AI Assistant';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;

    wrapper.appendChild(label);
    wrapper.appendChild(content);

    chatMessages.appendChild(wrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const el = document.createElement('div');
    el.className = 'typing-indicator';
    el.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(el);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return el;
}

function removeTypingIndicator(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
}

// ── Notifications ───────────────────────────────────────────────
function showNotification(msg, type) {
    notification.textContent = msg;
    notification.className = `notification ${type}`;
    clearTimeout(notification._timer);
    notification._timer = setTimeout(() => {
        notification.className = 'notification';
    }, 5000);
}

// ── Clear ───────────────────────────────────────────────────────
clearBtn.addEventListener('click', async () => {
    if (!confirm('Clear all indexed documents and chat history?')) return;
    try {
        await fetch(`${API}/clear`, { method: 'POST' });
        fileList.innerHTML = '';
        chatMessages.innerHTML = '';
        if (welcomeScreen) {
            welcomeScreen.style.display = '';
            chatMessages.appendChild(welcomeScreen);
        }
        showNotification('All data cleared.', 'success');
    } catch {
        showNotification('Failed to clear.', 'error');
    }
});
