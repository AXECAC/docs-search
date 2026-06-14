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
// Utility: Formatting and HTML Escaping
// ─────────────────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function formatBytes(bytes, decimals = 2) {
    if (!+bytes) return '0 Байт';
    const k = 1024, dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Байт', 'КБ', 'МБ', 'ГБ', 'ТБ'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
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
                if (typeof logout === 'function') logout();
                throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
            }
        }

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(err.detail || 'Ошибка API');
        }

        return await response.json();
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}
