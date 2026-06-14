const API_URL = window.location.origin.startsWith('file') ? 'http://localhost:8000' : window.location.origin;

// State
let state = {
    isAuthenticated: false,
    isLoginMode: true,
    user: null,
    documents: [],
    groups: [],
    users: [],
    activeTab: 'dashboard',
    docsPagination: { total: 0, page: 1, pages: 1, page_size: 12 },
};

// DOM Elements
const views = {
    auth: document.getElementById('auth-view'),
    dashboard: document.getElementById('dashboard-view'),
    search: document.getElementById('search-view'),
    chat: document.getElementById('chat-view'),
    groups: document.getElementById('groups-view'),
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
    } catch (e) { }
    return false;
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    state.isAuthenticated = false;
    state.user = null;
    state.activeTab = 'dashboard';
    state.documents = [];
    state.groups = [];
    state.docsPagination = { total: 0, page: 1, pages: 1, page_size: 12 };
    docsCurrentPage = 1;
    docsFilterQuery = '';

    // Сброс UI-полей
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = '';

    const searchResults = document.getElementById('search-results');
    if (searchResults) searchResults.innerHTML = '';

    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.value = '';

    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) chatMessages.innerHTML = '';

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
    } else if (tabName === 'groups' && state.user && state.user.role === 'admin') {
        fetchGroups();
    }
}

// ─────────────────────────────────────────────────────────────
// Document Functions
// ─────────────────────────────────────────────────────────────
async function fetchDocuments() {
    try {
        const params = new URLSearchParams({
            search: docsFilterQuery,
            page: docsCurrentPage,
            page_size: DOCS_PAGE_SIZE,
        });
        const data = await apiFetch(`/documents?${params}`);
        state.documents = data.items;
        state.docsPagination = { total: data.total, page: data.page, pages: data.pages, page_size: data.page_size };
        renderDocuments();
    } catch (e) { console.error(e); }
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
// Document Preview Modal
// ─────────────────────────────────────────────────────────────

const INLINE_EXTS = new Set(['pdf', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg']);

const EXT_ICONS = {
    pdf: '📕', txt: '📝', png: '🖼', jpg: '🖼', jpeg: '🖼', gif: '🖼',
    webp: '🖼', svg: '🖼', docx: '📘', doc: '📘', xlsx: '📗', xls: '📗',
    pptx: '📙', ppt: '📙',
};

async function openDocModal(documentId, documentTitle, extension) {
    const modal = document.getElementById('doc-modal');
    const icon = document.getElementById('modal-icon');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    const downloadBtn = document.getElementById('modal-download-btn');

    const ext = (extension || '').replace('.', '').toLowerCase();

    // Показываем модалку сразу с лоадером
    icon.textContent = EXT_ICONS[ext] || '📄';
    title.textContent = documentTitle || 'Document';
    body.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;gap:1rem;color:var(--text-muted)">
        <div class="spinner"></div> Загрузка...
    </div>`;
    downloadBtn.href = '#';
    downloadBtn.removeAttribute('download');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // Загружаем метаданные документа
    let docMeta = null;
    try {
        const token = localStorage.getItem('access_token');
        const metaRes = await fetch(`${API_URL}/documents/${documentId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (metaRes.ok) docMeta = await metaRes.json();
    } catch (_) { }

    const metaHtml = docMeta ? `
        <div class="doc-modal-meta">
            ${docMeta.author ? `<span>✍️ Автор: <strong>${escapeHtml(docMeta.author)}</strong></span>` : ''}
            ${docMeta.uploader_username ? `<span>👤 Загрузил: <strong>${escapeHtml(docMeta.uploader_username)}</strong></span>` : ''}
            ${docMeta.upload_date ? `<span>📅 Дата: <strong>${new Date(docMeta.upload_date).toLocaleDateString('ru-RU')}</strong></span>` : ''}
            ${docMeta.size_bytes ? `<span>📦 Размер: <strong>${formatBytes(docMeta.size_bytes)}</strong></span>` : ''}
            ${docMeta.description ? `<span style="grid-column:1/-1">📝 ${escapeHtml(docMeta.description)}</span>` : ''}
        </div>` : '';

    // Загружаем файл через fetch с авторизацией
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/documents/${documentId}/content`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);

        // Ссылка на скачивание
        downloadBtn.href = blobUrl;
        downloadBtn.download = documentTitle || `document.${ext}`;

        // Тело модалки
        if (INLINE_EXTS.has(ext)) {
            body.innerHTML = `
                ${metaHtml}
                <iframe src="${blobUrl}" title="${escapeHtml(documentTitle || 'Document')}" style="flex:1; border:none; width:100%; min-height:0;"></iframe>`;
        } else {
            body.innerHTML = `
                <div class="doc-download-prompt">
                    <div class="file-icon">${EXT_ICONS[ext] || '📄'}</div>
                    <h3>${escapeHtml(documentTitle || 'Document')}</h3>
                    ${metaHtml}
                    <p>Формат <strong>.${ext.toUpperCase()}</strong> нельзя отобразить прямо в браузере.
                    Нажмите кнопку ниже, чтобы скачать файл.</p>
                    <a href="${blobUrl}" download="${escapeHtml(documentTitle || 'document')}"
                       class="btn btn-primary" style="font-size: 1rem; padding: 0.75rem 2rem;">
                       ⬇ Скачать файл
                    </a>
                </div>`;
        }

        // Сохраняем blobUrl для освобождения при закрытии
        modal.dataset.blobUrl = blobUrl;

    } catch (e) {
        body.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--danger)">
            ❌ Ошибка загрузки файла: ${escapeHtml(e.message)}
        </div>`;
    }
}

function closeDocModal() {
    const modal = document.getElementById('doc-modal');
    // Освобождаем Blob URL чтобы не было утечки памяти
    if (modal.dataset.blobUrl) {
        URL.revokeObjectURL(modal.dataset.blobUrl);
        delete modal.dataset.blobUrl;
    }
    modal.style.display = 'none';
    document.getElementById('modal-body').innerHTML = '';
    document.body.style.overflow = '';
}
window.openDocModal = openDocModal;
window.closeDocModal = closeDocModal;

// Закрытие по Esc
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeDocModal();
        if (document.getElementById('upload-modal').style.display !== 'none') closeUploadModal();
        if (document.getElementById('group-modal').style.display !== 'none') {
            // Could be Create Group or Doc Access modal — both have close buttons
            if (typeof closeDocAccessModal === 'function') closeDocAccessModal();
        }
    }
});

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
        const extRaw = (r.extension || '').replace('.', '').toLowerCase();
        const extLabel = extRaw ? extRaw.toUpperCase() : '?';
        const scorePercent = Math.min(100, Math.round(r.score * 100));
        const keywords = (r.keywords || []).slice(0, 8);
        const snippet = r.text.length > 400 ? r.text.slice(0, 400) + '…' : r.text;
        const docIcon = EXT_ICONS[extRaw] || '📄';

        return `
        <div class="result-card glass" style="animation-delay: ${i * 0.04}s">
            <div class="result-header">
                <div class="result-source">
                    <span class="badge">${extLabel}</span>
                    <span class="doc-name source-link"
                          data-doc-id="${r.document_id}"
                          data-doc-title="${escapeHtml(r.document_title)}"
                          data-doc-ext="${extRaw}"
                          onclick="openDocModal(this.dataset.docId, this.dataset.docTitle, this.dataset.docExt)"
                          title="Открыть документ">
                        ${docIcon} ${escapeHtml(r.document_title)}
                    </span>
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
                            const sourceLinks = data.sources.map(s => {
                                const ext = (s.extension || '').replace('.', '').toLowerCase();
                                return `<span class="source-title source-link"
                                    data-doc-id="${s.document_id}"
                                    data-doc-title="${escapeHtml(s.document_title)}"
                                    data-doc-ext="${ext}"
                                    onclick="openDocModal(this.dataset.docId, this.dataset.docTitle, this.dataset.docExt)"
                                    title="Открыть документ">
                                    ${EXT_ICONS[ext] || '📄'} ${escapeHtml(s.document_title)}
                                </span>`;
                            }).join(' ');
                            sourcesHtml = `<div class="sources-box">
                                <strong>📚 Источники:</strong><br>
                                ${sourceLinks}
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

            // Auto login after registration
            const fd = new FormData();
            fd.append('username', username);
            fd.append('password', password);
            const data = await fetch(`${API_URL}/auth/login`, { method: 'POST', body: fd }).then(async r => {
                if (!r.ok) throw new Error((await r.json()).detail);
                return r.json();
            });
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            showToast('Registered successfully!');
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

const DOCS_PAGE_SIZE = 12;
let docsCurrentPage = 1;
let docsFilterQuery = '';

function onDocsFilter(value) {
    docsFilterQuery = value.trim().toLowerCase();
    docsCurrentPage = 1;
    fetchDocuments();
}
window.onDocsFilter = onDocsFilter;

function renderDocuments() {
    const grid = document.getElementById('docs-grid');
    const paginationEl = document.getElementById('docs-pagination');

    if (!state.documents || state.documents.length === 0) {
        grid.innerHTML = `<p style="color: var(--text-muted);">${docsFilterQuery ? 'No documents match your search.' : 'No documents found.'}</p>`;
        if (paginationEl) paginationEl.innerHTML = '';
        return;
    }

    grid.innerHTML = state.documents.map(doc => {
        const extRaw = (doc.extension || '').replace('.', '').toLowerCase();
        const extLabel = extRaw ? extRaw.toUpperCase() : 'UNKNOWN';
        const docIcon = EXT_ICONS[extRaw] || '📄';
        const uploaderLabel = doc.uploader_username ? `👤 ${escapeHtml(doc.uploader_username)}` : '';
        return `
        <div class="doc-card glass">
            <div class="doc-header">
                <div class="doc-title">${docIcon} ${escapeHtml(doc.title || 'Untitled')}</div>
                <span class="badge">${extLabel}</span>
            </div>
            <div class="doc-meta">
                <span>Size: ${formatBytes(doc.size_bytes)}</span>
                <span>Date: ${new Date(doc.upload_date).toLocaleDateString()}</span>
                ${uploaderLabel ? `<span>${uploaderLabel}</span>` : ''}
            </div>
            <div style="margin-top: auto; display: flex; gap: 0.5rem; justify-content: flex-end; flex-wrap: wrap;">
                <button class="btn btn-outline"
                    data-doc-id="${doc.id}"
                    data-doc-title="${escapeHtml(doc.title || 'Untitled')}"
                    data-doc-ext="${extRaw}"
                    onclick="openDocModal(this.dataset.docId, this.dataset.docTitle, this.dataset.docExt)">
                    👁 Open
                </button>
                ${(state.user.role === 'admin' || state.user.id === doc.uploader_id) ? `
                    <button class="btn btn-outline" style="color: var(--primary);"
                        onclick="openDocAccessModal('${doc.id}', ${JSON.stringify(doc.available_to_groups || []).replace(/"/g, '&quot;')})">
                        ⚙️ Access
                    </button>
                    <button class="btn btn-danger" onclick="deleteDocument('${doc.id}')">Delete</button>
                ` : ''}
            </div>
        </div>`;
    }).join('');

    // Пагинация по метаданным с сервера
    if (paginationEl) {
        const { page, pages } = state.docsPagination || { page: 1, pages: 1 };
        if (pages <= 1) {
            paginationEl.innerHTML = '';
        } else {
            const btns = [];
            for (let i = 1; i <= pages; i++) {
                btns.push(`<button class="pagination-btn ${i === page ? 'active' : ''}" onclick="goToDocsPage(${i})">${i}</button>`);
            }
            paginationEl.innerHTML = `
                <button class="pagination-btn" onclick="goToDocsPage(${page - 1})" ${page === 1 ? 'disabled' : ''}>‹</button>
                ${btns.join('')}
                <button class="pagination-btn" onclick="goToDocsPage(${page + 1})" ${page === pages ? 'disabled' : ''}>›</button>
            `;
        }
    }
}

window.goToDocsPage = function(page) {
    const { pages } = state.docsPagination || { pages: 1 };
    if (page < 1 || page > pages) return;
    docsCurrentPage = page;
    fetchDocuments();
    document.getElementById('docs-grid').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ─────────────────────────────────────────────────────────────
// Document Access (Groups) Modal
// ─────────────────────────────────────────────────────────────

let docAccessDocId = null;
let docAccessSelectedGroups = new Set();

window.openDocAccessModal = async function(docId, currentGroupsRaw) {
    docAccessDocId = docId;
    docAccessSelectedGroups = new Set(
        Array.isArray(currentGroupsRaw) ? currentGroupsRaw : []
    );

    // Получаем актуальные группы пользователя (уже в state.groups после fetchGroups)
    if (!state.groups.length) await fetchGroups(false);

    const modal = document.getElementById('group-modal');

    // Все группы, которые пользователь может назначить
    // Админ видит все (но пока используем только те, что в state.groups)
    const availableGroups = state.groups;

    modal.innerHTML = `
        <div class="doc-modal-panel upload-modal-panel" style="max-width: 460px;">
            <div class="dashboard-header" style="padding: 1.5rem; border-bottom: 1px solid var(--glass-border); margin-bottom: 0;">
                <h3 style="margin:0;">⚙️ Document Access</h3>
                <button class="btn btn-outline" onclick="closeDocAccessModal()" style="padding: 0.4rem 0.8rem;">✕</button>
            </div>
            <div class="upload-modal-body">
                <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom: 1rem;">
                    Выберите группы, которые имеют доступ к документу.<br>
                    Если не выбрать ни одной — документ станет <strong>публичным</strong>.
                </p>

                <label style="font-size:0.8rem; margin-bottom: 0.5rem; display:block;">Группы</label>
                ${availableGroups.length === 0 ? `
                    <div style="color:var(--text-muted); font-size:0.85rem; padding: 0.75rem; background: rgba(255,255,255,0.04); border-radius: 0.5rem;">
                        Вы не состоите ни в одной группе. Документ останется публичным.
                    </div>
                ` : `
                    <div class="tag-select-wrap" id="doc-access-group-list">
                        ${availableGroups.map(g => `
                            <label class="tag-item">
                                <span>
                                    <input type="checkbox" value="${g.id}"
                                        ${docAccessSelectedGroups.has(g.id) ? 'checked' : ''}
                                        onchange="toggleDocAccessGroup('${g.id}', this.checked)">
                                    ${escapeHtml(g.name)}
                                </span>
                            </label>
                        `).join('')}
                    </div>
                `}

                <div id="doc-access-status" style="margin-top: 1rem; font-size:0.8rem; color:var(--text-muted);">
                    ${docAccessSelectedGroups.size === 0 ? '🌐 Документ публичный' : `🔒 Доступ ограничен: ${docAccessSelectedGroups.size} гр.`}
                </div>
            </div>
            <div class="upload-modal-footer">
                <button class="btn btn-outline" onclick="closeDocAccessModal()">Cancel</button>
                <button class="btn btn-primary" onclick="submitDocAccess()">Save</button>
            </div>
        </div>
    `;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

window.toggleDocAccessGroup = function(groupId, isChecked) {
    if (isChecked) docAccessSelectedGroups.add(groupId);
    else docAccessSelectedGroups.delete(groupId);

    const statusEl = document.getElementById('doc-access-status');
    if (statusEl) {
        statusEl.textContent = docAccessSelectedGroups.size === 0
            ? '🌐 Документ публичный'
            : `🔒 Доступ ограничен: ${docAccessSelectedGroups.size} гр.`;
    }
}

window.closeDocAccessModal = function() {
    document.getElementById('group-modal').style.display = 'none';
    document.body.style.overflow = '';
    docAccessDocId = null;
    docAccessSelectedGroups.clear();
}

window.submitDocAccess = async function() {
    if (!docAccessDocId) return;
    try {
        await apiFetch(`/documents/${docAccessDocId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                available_to_groups: Array.from(docAccessSelectedGroups),
            }),
        });
        showToast('Доступ обновлён');
        closeDocAccessModal();
        fetchDocuments();
    } catch (e) {
        showToast('Ошибка при обновлении доступа', 'error');
        console.error(e);
    }
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

        // Toggle admin tabs
        document.querySelectorAll('.admin-only').forEach(el => {
            el.style.display = state.user.role === 'admin' ? 'inline-block' : 'none';
        });

        switchTab(state.activeTab);
    } else {
        Object.values(views).forEach(v => v.classList.remove('active'));
        views.auth.classList.add('active');
        tabNav.style.display = 'none';
        navActions.innerHTML = '';
    }
}


// ─────────────────────────────────────────────────────────────
// Upload Modal & Logic
// ─────────────────────────────────────────────────────────────

let pendingUploadFile = null;
let selectedUploadGroups = new Set();
let selectedUploadUsers = new Set();

const openUploadBtn = document.getElementById('open-upload-modal-btn');
if (openUploadBtn) {
    openUploadBtn.addEventListener('click', () => openUploadModal());
}

async function openUploadModal(file = null) {
    pendingUploadFile = file;
    selectedUploadGroups.clear();
    selectedUploadUsers.clear();

    const modal = document.getElementById('upload-modal');

    // Fetch users/groups for dropdowns
    if (state.user) {
        if (!state.groups.length) await fetchGroups(false); // don't render view, just fetch
    }

    modal.innerHTML = `
        <div class="doc-modal-panel upload-modal-panel">
            <div class="dashboard-header" style="padding: 1.5rem; border-bottom: 1px solid var(--glass-border); margin-bottom: 0;">
                <h3 style="margin:0;">Upload Document</h3>
                <button class="btn btn-outline" onclick="closeUploadModal()" style="padding: 0.4rem 0.8rem;">✕</button>
            </div>
            <div class="upload-modal-body">
                
                <!-- File Drop Zone -->
                <div class="file-drop-zone" id="modal-drop-zone" onclick="document.getElementById('modalFileInput').click()">
                    <span class="file-drop-icon">📄</span>
                    <h4 id="modal-drop-text">${file ? 'File selected' : 'Click or Drag & Drop file here'}</h4>
                    <div id="modal-file-name" class="file-selected-name">${file ? file.name : ''}</div>
                    <input type="file" id="modalFileInput" style="display: none;">
                </div>

                <!-- Title/Desc -->
                <div class="form-group">
                    <label>Title (optional)</label>
                    <input type="text" id="upload-title" class="input-control" placeholder="Document title...">
                </div>
                <div class="form-group">
                    <label>Description (optional)</label>
                    <textarea id="upload-desc" placeholder="Brief description..."></textarea>
                </div>

                <!-- Access Control -->
                <div class="form-group">
                    <label>Access Control</label>
                    <div class="access-toggle">
                        <button class="access-toggle-btn active" id="btn-access-all" onclick="toggleAccessType('all')">Public (All)</button>
                        <button class="access-toggle-btn" id="btn-access-restricted" onclick="toggleAccessType('restricted')">Restricted</button>
                    </div>

                    <div id="restricted-panel" class="access-panel">
                        <div style="font-size:0.8rem; color:var(--text-muted);">Select groups or specific users who can access this document.</div>
                        
                        <label style="font-size:0.75rem;">Groups</label>
                        <div class="tag-select-wrap" id="upload-group-list">
                            ${state.groups.map(g => `
                                <label class="tag-item">
                                    <span>
                                        <input type="checkbox" value="${g.id}" onchange="toggleUploadGroup('${g.id}', this.checked)">
                                        ${escapeHtml(g.name)}
                                    </span>
                                </label>
                            `).join('')}
                            ${state.groups.length === 0 ? '<div style="padding:0.5rem; font-size:0.8rem; color:var(--text-muted);">No groups available</div>' : ''}
                        </div>

                        ${state.user && state.user.role === 'admin' ? `
                        <label style="font-size:0.75rem; margin-top: 0.5rem;">Specific Users (by username)</label>
                        <div class="search-wrap">
                            <input type="text" class="input-control" id="upload-user-search" placeholder="Type username..." oninput="debounceUserSearch(this.value, 'upload')" style="width:100%">
                            <div id="upload-user-results" class="search-results-dropdown" style="display:none;"></div>
                        </div>
                        <div class="user-chips" id="upload-selected-users"></div>
                        ` : ''}
                    </div>
                </div>

            </div>
            <div class="upload-modal-footer">
                <button class="btn btn-outline" onclick="closeUploadModal()">Cancel</button>
                <button class="btn btn-primary" onclick="submitUpload()">Upload File</button>
            </div>
        </div>
    `;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // File input handlers
    const dropZone = document.getElementById('modal-drop-zone');
    const fileIn = document.getElementById('modalFileInput');

    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            pendingUploadFile = e.dataTransfer.files[0];
            document.getElementById('modal-drop-text').textContent = 'File selected';
            document.getElementById('modal-file-name').textContent = pendingUploadFile.name;
        }
    });
    fileIn.addEventListener('change', (e) => {
        if (e.target.files.length) {
            pendingUploadFile = e.target.files[0];
            document.getElementById('modal-drop-text').textContent = 'File selected';
            document.getElementById('modal-file-name').textContent = pendingUploadFile.name;
        }
    });
}

function closeUploadModal() {
    document.getElementById('upload-modal').style.display = 'none';
    document.body.style.overflow = '';
    pendingUploadFile = null;
}

window.toggleAccessType = function (type) {
    const btnAll = document.getElementById('btn-access-all');
    const btnRestricted = document.getElementById('btn-access-restricted');
    const panel = document.getElementById('restricted-panel');
    const uploadBtn = document.querySelector('.upload-modal-footer .btn-primary');

    const userHasNoGroups = state.user && state.user.role !== 'admin' && state.groups.length === 0;

    if (type === 'all') {
        btnAll.classList.add('active');
        btnRestricted.classList.remove('active');
        panel.classList.remove('visible');
        selectedUploadGroups.clear();
        selectedUploadUsers.clear();
        document.querySelectorAll('#upload-group-list input[type="checkbox"]').forEach(cb => cb.checked = false);
        renderUploadSelectedUsers();
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.title = '';
        }
    } else {
        btnRestricted.classList.add('active');
        btnAll.classList.remove('active');
        panel.classList.add('visible');
        if (uploadBtn && userHasNoGroups) {
            uploadBtn.disabled = true;
            uploadBtn.title = 'Вы не состоите ни в одной группе — невозможно ограничить доступ';
        }
    }
}

window.toggleUploadGroup = function (groupId, isChecked) {
    if (isChecked) selectedUploadGroups.add(groupId);
    else selectedUploadGroups.delete(groupId);
}

// User Search
let userSearchTimeout = null;
window.debounceUserSearch = function (query, context) {
    clearTimeout(userSearchTimeout);
    userSearchTimeout = setTimeout(() => searchUsersApi(query, context), 300);
}

async function searchUsersApi(query, context) {
    const dropdown = document.getElementById(context === 'upload' ? 'upload-user-results' : 'group-user-results');
    if (!query || query.length < 2) {
        dropdown.style.display = 'none';
        return;
    }

    try {
        const users = await apiFetch(`/auth/users?q=${encodeURIComponent(query)}`);
        if (users.length === 0) {
            dropdown.innerHTML = '<div class="dropdown-item" style="color:var(--text-muted)">No users found</div>';
        } else {
            dropdown.innerHTML = users.map(u => `
                <div class="dropdown-item" onclick="selectUser('${u.id}', '${escapeHtml(u.username)}', '${context}')">
                    ${escapeHtml(u.username)} <span style="font-size:0.7rem; color:var(--text-muted)">(${u.role})</span>
                </div>
            `).join('');
        }
        dropdown.style.display = 'block';
    } catch (e) {
        console.error("User search failed", e);
    }
}

window.selectUser = function (id, username, context) {
    document.getElementById(context === 'upload' ? 'upload-user-results' : 'group-user-results').style.display = 'none';
    document.getElementById(context === 'upload' ? 'upload-user-search' : 'group-user-search').value = '';

    if (context === 'upload') {
        selectedUploadUsers.add({ id, username });
        renderUploadSelectedUsers();
    } else {
        selectedGroupUsers.add({ id, username });
        renderGroupSelectedUsers();
    }
}

window.removeUploadUser = function (id) {
    for (let u of selectedUploadUsers) {
        if (u.id === id) { selectedUploadUsers.delete(u); break; }
    }
    renderUploadSelectedUsers();
}

function renderUploadSelectedUsers() {
    const container = document.getElementById('upload-selected-users');
    if (!container) return;
    container.innerHTML = Array.from(selectedUploadUsers).map(u => `
        <div class="chip">
            👤 ${escapeHtml(u.username)}
            <span class="chip-remove" onclick="removeUploadUser('${u.id}')">✕</span>
        </div>
    `).join('');
}

async function submitUpload() {
    if (!pendingUploadFile) {
        showToast('Please select a file first', 'error');
        return;
    }

    const title = document.getElementById('upload-title').value.trim();
    const desc = document.getElementById('upload-desc').value.trim();

    const formData = new FormData();
    formData.append('file', pendingUploadFile);
    if (title) formData.append('title', title);
    if (desc) formData.append('description', desc);

    const isRestricted = document.getElementById('btn-access-restricted').classList.contains('active');
    if (isRestricted) {
        if (selectedUploadUsers.size > 0) {
            formData.append('is_available_to', Array.from(selectedUploadUsers).map(u => u.id).join(','));
        }
        if (selectedUploadGroups.size > 0) {
            formData.append('available_to_groups', Array.from(selectedUploadGroups).join(','));
        }
    }

    showToast('Uploading...', 'success');
    closeUploadModal();

    try {
        await apiFetch('/documents/upload', {
            method: 'POST',
            body: formData,
        });
        showToast('File uploaded successfully!');
        if (state.activeTab === 'dashboard') fetchDocuments();
    } catch (e) {
        console.error(e);
    }
}


// ─────────────────────────────────────────────────────────────
// Groups Management
// ─────────────────────────────────────────────────────────────

async function fetchGroups(render = true) {
    try {
        state.groups = await apiFetch('/groups');
        if (render) renderGroups();
    } catch (e) { console.error(e); }
}

function renderGroups() {
    const container = document.getElementById('groups-list');
    if (!container) return;

    if (state.groups.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">No groups found.</p>';
        return;
    }

    container.innerHTML = state.groups.map(g => `
        <div class="group-card glass">
            <div class="group-card-header" onclick="toggleGroupMembers('${g.id}')">
                <div>
                    <div class="group-card-title">👥 ${escapeHtml(g.name)}</div>
                    <div class="group-card-meta">${escapeHtml(g.description || 'No description')} • ${g.member_count} members</div>
                </div>
                <div class="group-card-actions">
                    <button class="btn btn-danger" onclick="event.stopPropagation(); deleteGroup('${g.id}')" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;">Delete</button>
                </div>
            </div>
            <div class="group-members-panel" id="group-panel-${g.id}">
                <div class="spinner" style="width:20px; height:20px;"></div> Loading members...
            </div>
        </div>
    `).join('');
}

window.deleteGroup = async function (id) {
    if (!confirm('Delete this group?')) return;
    try {
        await apiFetch(`/groups/${id}`, { method: 'DELETE' });
        showToast('Group deleted');
        fetchGroups();
    } catch (e) { console.error(e); }
}

window.toggleGroupMembers = async function (groupId) {
    const panel = document.getElementById(`group-panel-${groupId}`);
    if (panel.classList.contains('open')) {
        panel.classList.remove('open');
        return;
    }

    // Close others
    document.querySelectorAll('.group-members-panel').forEach(p => p.classList.remove('open'));
    panel.classList.add('open');

    try {
        const members = await apiFetch(`/groups/${groupId}/members`);
        panel.innerHTML = `
            <div class="member-list">
                ${members.length === 0 ? '<div style="color:var(--text-muted); font-size:0.85rem;">No members yet</div>' : ''}
                ${members.map(m => `
                    <div class="member-row">
                        <div class="member-info">
                            <span>👤 ${escapeHtml(m.username)}</span>
                            <span class="member-role">${m.role}</span>
                        </div>
                        <button class="btn btn-outline" style="border-color:var(--danger); color:var(--danger); padding:0.2rem 0.5rem; font-size:0.7rem;" 
                                onclick="removeMember('${groupId}', '${m.id}')">Remove</button>
                    </div>
                `).join('')}
            </div>
            <div class="add-member-row">
                <div class="search-wrap" style="flex:1;">
                    <input type="text" class="input-control" id="search-add-${groupId}" placeholder="Add user by username..." 
                           oninput="debounceAddMemberSearch(this.value, '${groupId}')" style="width:100%; padding: 0.4rem 0.8rem;">
                    <div id="results-add-${groupId}" class="search-results-dropdown" style="display:none; bottom:100%; top:auto; margin-bottom:4px;"></div>
                </div>
            </div>
        `;
    } catch (e) {
        panel.innerHTML = '<div style="color:var(--danger)">Failed to load members</div>';
    }
}

let addMemberTimeout = null;
window.debounceAddMemberSearch = function (query, groupId) {
    clearTimeout(addMemberTimeout);
    addMemberTimeout = setTimeout(() => searchAddMemberApi(query, groupId), 300);
}

async function searchAddMemberApi(query, groupId) {
    const dropdown = document.getElementById(`results-add-${groupId}`);
    if (!query || query.length < 2) {
        dropdown.style.display = 'none';
        return;
    }
    try {
        const users = await apiFetch(`/auth/users?q=${encodeURIComponent(query)}`);
        if (users.length === 0) {
            dropdown.innerHTML = '<div class="dropdown-item" style="color:var(--text-muted)">No users found</div>';
        } else {
            dropdown.innerHTML = users.map(u => `
                <div class="dropdown-item" onclick="addMemberToGroup('${groupId}', '${u.id}')">
                    ${escapeHtml(u.username)} <span style="font-size:0.7rem; color:var(--text-muted)">(${u.role})</span>
                </div>
            `).join('');
        }
        dropdown.style.display = 'block';
    } catch (e) { }
}

window.addMemberToGroup = async function (groupId, userId) {
    try {
        await apiFetch(`/groups/${groupId}/members`, {
            method: 'POST',
            body: JSON.stringify({ user_ids: [userId] })
        });
        showToast('Member added');
        toggleGroupMembers(groupId); // Refresh open panel
        toggleGroupMembers(groupId);
        fetchGroups(true); // update member counts
    } catch (e) { console.error(e); }
}

window.removeMember = async function (groupId, userId) {
    try {
        await apiFetch(`/groups/${groupId}/members/${userId}`, { method: 'DELETE' });
        showToast('Member removed');
        toggleGroupMembers(groupId); // Refresh open panel
        toggleGroupMembers(groupId);
        fetchGroups(true);
    } catch (e) { console.error(e); }
}

// Create Group logic
document.getElementById('create-group-btn')?.addEventListener('click', () => {
    const modal = document.getElementById('group-modal');
    modal.innerHTML = `
        <div class="doc-modal-panel upload-modal-panel" style="max-width: 400px;">
            <div class="dashboard-header" style="padding: 1.5rem; border-bottom: 1px solid var(--glass-border); margin-bottom: 0;">
                <h3 style="margin:0;">Create Group</h3>
                <button class="btn btn-outline" onclick="document.getElementById('group-modal').style.display='none'" style="padding: 0.4rem 0.8rem;">✕</button>
            </div>
            <div class="upload-modal-body">
                <div class="form-group">
                    <label>Group Name</label>
                    <input type="text" id="new-group-name" class="input-control" placeholder="E.g. Managers" style="min-height: auto;">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="new-group-desc" placeholder="Brief description..."></textarea>
                </div>
            </div>
            <div class="upload-modal-footer">
                <button class="btn btn-outline" onclick="document.getElementById('group-modal').style.display='none'">Cancel</button>
                <button class="btn btn-primary" onclick="submitCreateGroup()">Create</button>
            </div>
        </div>
    `;
    modal.style.display = 'flex';
});

window.submitCreateGroup = async function () {
    const name = document.getElementById('new-group-name').value.trim();
    const desc = document.getElementById('new-group-desc').value.trim();
    if (!name) return showToast('Name is required', 'error');

    try {
        await apiFetch('/groups', {
            method: 'POST',
            body: JSON.stringify({ name, description: desc })
        });
        showToast('Group created');
        document.getElementById('group-modal').style.display = 'none';
        fetchGroups();
    } catch (e) { console.error(e); }
}


// Init
checkAuth();
