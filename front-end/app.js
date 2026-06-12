const API_URL = window.location.origin.startsWith('file') ? 'http://localhost:8000' : window.location.origin;

// State
let state = {
    isAuthenticated: false,
    isLoginMode: true,
    user: null,
    documents: []
};

// DOM Elements
const views = {
    auth: document.getElementById('auth-view'),
    dashboard: document.getElementById('dashboard-view')
};
const navActions = document.getElementById('nav-actions');

// --- Utility: Toasts ---
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

// --- Utility: API Fetch with Interceptor ---
async function apiFetch(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = { ...options.headers };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Do not set Content-Type if body is FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    try {
        let response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
        
        // Handle token expiration / 401
        if (response.status === 401 && token) {
            const refreshed = await refreshToken();
            if (refreshed) {
                headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
                response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
            } else {
                logout();
                throw new Error("Session expired. Please login again.");
            }
        }

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(err.detail || "API Error");
        }

        return await response.json();
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

// --- Auth Functions ---
async function refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return false;
    try {
        const res = await fetch(`${API_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refresh })
        });
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            return true;
        }
    } catch(e) {}
    return false;
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    state.isAuthenticated = false;
    state.user = null;
    render();
}

async function checkAuth() {
    if (localStorage.getItem('access_token')) {
        try {
            state.user = await apiFetch('/auth/me');
            state.isAuthenticated = true;
        } catch(e) {
            logout();
        }
    }
    render();
}

// Make globally accessible for onclick attributes
window.logout = logout;

// --- Document Functions ---
async function fetchDocuments() {
    try {
        state.documents = await apiFetch('/documents');
        renderDocuments();
    } catch(e) { console.error(e); }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    showToast('Uploading...', 'success');
    try {
        await apiFetch('/documents/upload', {
            method: 'POST',
            body: formData
        });
        showToast('File uploaded successfully!');
        fetchDocuments();
    } catch(e) {
        console.error(e);
    }
}

async function deleteDocument(id) {
    if(!confirm("Are you sure you want to delete this document?")) return;
    try {
        await apiFetch(`/documents/${id}`, { method: 'DELETE' });
        showToast('Document deleted');
        fetchDocuments();
    } catch(e) { console.error(e); }
}

// Make globally accessible for onclick attributes
window.deleteDocument = deleteDocument;

// --- Event Listeners ---
document.getElementById('auth-toggle').addEventListener('click', () => {
    state.isLoginMode = !state.isLoginMode;
    document.getElementById('auth-title').innerText = state.isLoginMode ? 'Login' : 'Register';
    document.getElementById('auth-submit').innerText = state.isLoginMode ? 'Login' : 'Create Account';
    document.getElementById('auth-toggle').innerText = state.isLoginMode ? "Don't have an account? Register" : "Already have an account? Login";
});

document.getElementById('auth-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('auth-submit');
    btn.innerHTML = '<div class="spinner"></div>';
    btn.disabled = true;

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        if (state.isLoginMode) {
            // Login uses OAuth2 Form
            const fd = new FormData();
            fd.append('username', username);
            fd.append('password', password);
            const data = await fetch(`${API_URL}/auth/login`, { method: 'POST', body: fd }).then(async r => {
                if(!r.ok) throw new Error((await r.json()).detail);
                return r.json();
            });
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
        } else {
            // Register
            await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            }).then(async r => {
                if(!r.ok) throw new Error((await r.json()).detail);
            });
            showToast("Registered successfully. Please login.");
            state.isLoginMode = true;
            render();
            btn.innerHTML = 'Login';
            btn.disabled = false;
            return;
        }
        
        await checkAuth();
        showToast(`Welcome, ${state.user.username}!`);
    } catch(e) {
        showToast(e.message, 'error');
    } finally {
        btn.innerHTML = state.isLoginMode ? 'Login' : 'Create Account';
        btn.disabled = false;
    }
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
    const dt = e.dataTransfer;
    const files = dt.files;
    if(files.length) uploadFile(files[0]);
});

fileInput.addEventListener('change', (e) => {
    if(e.target.files.length) uploadFile(e.target.files[0]);
});

// --- Render ---
function formatBytes(bytes, decimals = 2) {
    if (!+bytes) return '0 Bytes';
    const k = 1024, dm = decimals < 0 ? 0 : decimals, sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'], i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

function renderDocuments() {
    const grid = document.getElementById('docs-grid');
    if(state.documents.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted);">No documents found.</p>';
        return;
    }
    
    grid.innerHTML = state.documents.map(doc => `
        <div class="doc-card glass">
            <div class="doc-header">
                <div class="doc-title">${doc.title || 'Untitled'}</div>
                <span class="badge">${doc.extension ? doc.extension.toUpperCase() : 'UNKNOWN'}</span>
            </div>
            <div class="doc-meta">
                <span>Size: ${formatBytes(doc.size_bytes)}</span>
                <span>Date: ${new Date(doc.upload_date).toLocaleDateString()}</span>
            </div>
            <div style="margin-top: auto; display: flex; gap: 0.5rem; justify-content: flex-end;">
                ${(state.user.role === 'admin' || state.user.id === doc.uploader_id) ? 
                    `<button class="btn btn-danger" onclick="deleteDocument('${doc.id}')">Delete</button>` : ''}
            </div>
        </div>
    `).join('');
}

function render() {
    if (state.isAuthenticated) {
        views.auth.classList.remove('active');
        views.dashboard.classList.add('active');
        navActions.innerHTML = `
            <span class="badge" style="background: rgba(99, 102, 241, 0.2); color: #818cf8;">
                ${state.user.role.toUpperCase()}
            </span>
            <span>${state.user.username}</span>
            <button class="btn btn-outline" onclick="logout()">Logout</button>
        `;
        fetchDocuments();
    } else {
        views.dashboard.classList.remove('active');
        views.auth.classList.add('active');
        navActions.innerHTML = '';
    }
}

// Init
checkAuth();
