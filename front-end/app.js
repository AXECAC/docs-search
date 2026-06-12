const API_URL = window.location.origin.startsWith('file') ? 'http://localhost:8000' : window.location.origin;

// State
let state = {
    isAuthenticated: false,
    isLoginMode: true,
    user: null,
    documents: [],
    activeTab: 'dashboard',
};

// DOM Elements
const views = {
    auth: document.getElementById('auth-view'),
    dashboard: document.getElementById('dashboard-view'),
    search: document.getElementById('search-view'),
    chat: document.getElementById('chat-view'),
};
const navActions = document.getElementById('nav-actions');
const tabNav = document.getElementById('tab-nav');

// ─────────────────────────────────────────────────────────────
// Utility: Toasts
// ─────────────────────────────────────────────────────────────
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerText = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ─────────────────────────────────────────────────────────────
// Utility: API Fetch with Token Interceptor
// ─────────────────────────────────────────────────────────────
async function apiFetch(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = { ...options.headers };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    try {
        let response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });

        if (response.status === 401 && token) {
            const refreshed = await refreshToken();
            if (refreshed) {
                headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
                response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
            } else {
                logout();
                throw new Error('Session expired. Please login again.');
            }
        }

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(err.detail || 'API Error');
        }

        return await response.json();
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

// ─────────────────────────────────────────────────────────────
// Auth Functions
// ─────────────────────────────────────────────────────────────
async function refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return false;
    try {
        const res = await fetch(`${API_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refresh }),
        });
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            return true;
        }
    } catch (e) {}
    return false;
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    state.isAuthenticated = false;
    state.user = null;
    state.activeTab = 'dashboard';
    render();
}

async function checkAuth() {
    if (localStorage.getItem('access_token')) {
        try {
            state.user = await apiFetch('/auth/me');
            state.isAuthenticated = true;
        } catch (e) {
            logout();
        }
    }
    render();
}

window.logout = logout;

// ─────────────────────────────────────────────────────────────
// Tab Navigation
// ─────────────────────────────────────────────────────────────
function switchTab(tabName) {
    state.activeTab = tabName;

    // Update button active states
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Show/hide views
    Object.entries(views).forEach(([name, el]) => {
        el.classList.toggle('active', name === tabName);
    });

    if (tabName === 'dashboard') {
        fetchDocuments();
    }
}

// ─────────────────────────────────────────────────────────────
// Document Functions
// ─────────────────────────────────────────────────────────────
async function fetchDocuments() {
    try {
        state.documents = await apiFetch('/documents');
        renderDocuments();
    } catch (e) { console.error(e); }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    showToast('Uploading...', 'success');
    try {
        await apiFetch('/documents/upload', {
            method: 'POST',
            body: formData,
        });
        showToast('File uploaded successfully!');
        fetchDocuments();
    } catch (e) {
        console.error(e);
    }
}

async function deleteDocument(id) {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
        await apiFetch(`/documents/${id}`, { method: 'DELETE' });
        showToast('Document deleted');
        fetchDocuments();
    } catch (e) { console.error(e); }
}

window.deleteDocument = deleteDocument;

// ─────────────────────────────────────────────────────────────
// Search Functions
// ─────────────────────────────────────────────────────────────

/**
 * Highlights query words in text by wrapping them in <mark> tags.
 */
function highlightText(text, query) {
    if (!query) return escapeHtml(text);
    const words = query.trim().split(/\s+/).filter(w => w.length >= 3);
    if (!words.length) return escapeHtml(text);

    let escaped = escapeHtml(text);
    words.forEach(word => {
        const re = new RegExp(`(${word})`, 'gi');
        escaped = escaped.replace(re, '<mark>$1</mark>');
    });
    return escaped;
}

function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function renderSearchResults(results, query) {
    const container = document.getElementById('search-results');
    const stateEl = document.getElementById('search-state');

    if (!results || results.length === 0) {
        stateEl.style.display = 'block';
        stateEl.innerText = '🔍 No results found. Try different keywords.';
        container.innerHTML = '';
        return;
    }

    stateEl.style.display = 'none';

    container.innerHTML = results.map((r, i) => {
        const ext = r.extension ? r.extension.toUpperCase() : '?';
        const scorePercent = Math.min(100, Math.round(r.score * 100));
        const keywords = (r.keywords || []).slice(0, 8);
        const snippet = r.text.length > 400 ? r.text.slice(0, 400) + '…' : r.text;

        return `
        <div class="result-card glass" style="animation-delay: ${i * 0.04}s">
            <div class="result-header">
                <div class="result-source">
                    <span class="badge">${ext}</span>
                    <span class="doc-name">${escapeHtml(r.document_title)}</span>
                </div>
                <div class="score-badge">
                    ⚡ ${scorePercent}% match
                </div>
            </div>
            <div class="result-text">${highlightText(snippet, query)}</div>
            ${keywords.length ? `
            <div class="result-keywords">
                ${keywords.map(kw => `<span class="kw-tag">${escapeHtml(kw)}</span>`).join('')}
            </div>` : ''}
        </div>`;
    }).join('');
}

async function performSearch(query) {
    const stateEl = document.getElementById('search-state');
    const container = document.getElementById('search-results');

    stateEl.style.display = 'block';
    stateEl.innerHTML = '<div style="display:inline-block" class="spinner"></div>&nbsp; Searching...';
    container.innerHTML = '';

    try {
        const results = await apiFetch('/documents/search', {
            method: 'POST',
            body: JSON.stringify({ query, top_k: 15 }),
        });
        renderSearchResults(results, query);
    } catch (e) {
        stateEl.style.display = 'none';
    }
}

// ─────────────────────────────────────────────────────────────
// Chat Functions
// ─────────────────────────────────────────────────────────────
function appendMessage(role, content) {
    const messagesContainer = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    // Using innerHTML to allow basic formatting and sources
    contentDiv.innerHTML = content.replace(/\n/g, '<br>');
    
    msgDiv.appendChild(contentDiv);
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return contentDiv;
}

async function performChat(query) {
    appendMessage('user', query);
    
    const submitBtn = document.getElementById('chat-submit-btn');
    const inputField = document.getElementById('chat-input');
    
    submitBtn.disabled = true;
    inputField.disabled = true;
    
    // Add a placeholder message for the assistant
    const assistantMsgContent = appendMessage('assistant', '<div class="spinner"></div> Думаю...');
    
    try {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };
        
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ query: query })
        });
        
        if (response.status === 401) {
            const refreshed = await refreshToken();
            if (!refreshed) {
                logout();
                throw new Error('Session expired');
            }
            // Retry once
            headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
            // For simplicity, we just throw here and let the user click again
            // but normally we would await fetch again.
        }

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        // Streaming logic
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        
        let fullText = "";
        let sourcesHtml = "";
        assistantMsgContent.innerHTML = ""; // clear spinner
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunkText = decoder.decode(value, { stream: true });
            const lines = chunkText.split('\n').filter(l => l.trim() !== '');
            
            for (const line of lines) {
                try {
                    const data = JSON.parse(line);
                    
                    if (data.type === 'sources') {
                        if (data.sources && data.sources.length > 0) {
                            sourcesHtml = `<div class="sources-box">
                                <strong>📚 Источники:</strong><br>
                                ${data.sources.map(s => `<span class="source-title">📄 ${escapeHtml(s.document_title)}</span>`).join(' ')}
                            </div>`;
                            assistantMsgContent.innerHTML = sourcesHtml + fullText;
                        }
                    } else if (data.type === 'content') {
                        fullText += escapeHtml(data.content);
                        assistantMsgContent.innerHTML = sourcesHtml + fullText.replace(/\n/g, '<br>');
                        document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
                    } else if (data.type === 'error') {
                        fullText += `<br><span style="color:var(--danger)">[Ошибка: ${escapeHtml(data.content)}]</span>`;
                        assistantMsgContent.innerHTML = sourcesHtml + fullText.replace(/\n/g, '<br>');
                    }
                } catch (e) {
                    console.error("Parse error chunk:", line, e);
                }
            }
        }
        
    } catch (e) {
        assistantMsgContent.innerHTML = `<span style="color:var(--danger)">Error: ${e.message}</span>`;
    } finally {
        submitBtn.disabled = false;
        inputField.disabled = false;
        inputField.focus();
    }
}

// ─────────────────────────────────────────────────────────────
// Event Listeners
// ─────────────────────────────────────────────────────────────

// Chat form submit
document.getElementById('chat-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const query = document.getElementById('chat-input').value.trim();
    if (!query) return;
    document.getElementById('chat-input').value = '';
    performChat(query);
});

// Auth form toggle
document.getElementById('auth-toggle').addEventListener('click', () => {
    state.isLoginMode = !state.isLoginMode;
    document.getElementById('auth-title').innerText = state.isLoginMode ? 'Login' : 'Register';
    document.getElementById('auth-submit').innerText = state.isLoginMode ? 'Login' : 'Create Account';
    document.getElementById('auth-toggle').innerText = state.isLoginMode
        ? "Don't have an account? Register"
        : 'Already have an account? Login';
});

// Auth form submit
document.getElementById('auth-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('auth-submit');
    btn.innerHTML = '<div class="spinner"></div>';
    btn.disabled = true;

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        if (state.isLoginMode) {
            const fd = new FormData();
            fd.append('username', username);
            fd.append('password', password);
            const data = await fetch(`${API_URL}/auth/login`, { method: 'POST', body: fd }).then(async r => {
                if (!r.ok) throw new Error((await r.json()).detail);
                return r.json();
            });
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
        } else {
            await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            }).then(async r => {
                if (!r.ok) throw new Error((await r.json()).detail);
            });
            showToast('Registered successfully. Please login.');
            state.isLoginMode = true;
            render();
            btn.innerHTML = 'Login';
            btn.disabled = false;
            return;
        }

        await checkAuth();
        showToast(`Welcome, ${state.user.username}!`);
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        btn.innerHTML = state.isLoginMode ? 'Login' : 'Create Account';
        btn.disabled = false;
    }
});

// Tab navigation
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

// Search form submit
document.getElementById('search-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;
    performSearch(query);
});

// Drag & Drop
const dropArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.add('drag-over'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.remove('drag-over'), false);
});

dropArea.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length) uploadFile(files[0]);
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) uploadFile(e.target.files[0]);
});

// ─────────────────────────────────────────────────────────────
// Render
// ─────────────────────────────────────────────────────────────
function formatBytes(bytes, decimals = 2) {
    if (!+bytes) return '0 Bytes';
    const k = 1024, dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

function renderDocuments() {
    const grid = document.getElementById('docs-grid');
    if (state.documents.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted);">No documents found.</p>';
        return;
    }

    grid.innerHTML = state.documents.map(doc => `
        <div class="doc-card glass">
            <div class="doc-header">
                <div class="doc-title">${escapeHtml(doc.title || 'Untitled')}</div>
                <span class="badge">${doc.extension ? doc.extension.toUpperCase() : 'UNKNOWN'}</span>
            </div>
            <div class="doc-meta">
                <span>Size: ${formatBytes(doc.size_bytes)}</span>
                <span>Date: ${new Date(doc.upload_date).toLocaleDateString()}</span>
            </div>
            <div style="margin-top: auto; display: flex; gap: 0.5rem; justify-content: flex-end;">
                ${(state.user.role === 'admin' || state.user.id === doc.uploader_id)
                    ? `<button class="btn btn-danger" onclick="deleteDocument('${doc.id}')">Delete</button>`
                    : ''}
            </div>
        </div>
    `).join('');
}

function render() {
    if (state.isAuthenticated) {
        views.auth.classList.remove('active');
        tabNav.style.display = 'flex';

        navActions.innerHTML = `
            <span class="badge" style="background: rgba(99, 102, 241, 0.2); color: #818cf8;">
                ${state.user.role.toUpperCase()}
            </span>
            <span>${state.user.username}</span>
            <button class="btn btn-outline" onclick="logout()">Logout</button>
        `;

        switchTab(state.activeTab);
    } else {
        Object.values(views).forEach(v => v.classList.remove('active'));
        views.auth.classList.add('active');
        tabNav.style.display = 'none';
        navActions.innerHTML = '';
    }
}

// Init
checkAuth();
