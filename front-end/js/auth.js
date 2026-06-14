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
    
    if (typeof docsCurrentPage !== 'undefined') docsCurrentPage = 1;
    if (typeof docsFilterQuery !== 'undefined') docsFilterQuery = '';

    // Сброс UI-полей
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = '';

    const searchResults = document.getElementById('search-results');
    if (searchResults) searchResults.innerHTML = '';

    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.value = '';

    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) chatMessages.innerHTML = '';

    if (typeof render === 'function') render();
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
    if (typeof render === 'function') render();
}

window.logout = logout;
