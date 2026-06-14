// ─────────────────────────────────────────────────────────────
// Initialization and Global Event Listeners
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
window.switchTab = switchTab;

function render() {
    if (state.isAuthenticated) {
        views.auth.classList.remove('active');
        tabNav.style.display = 'flex';

        navActions.innerHTML = `
            <span class="badge" style="background: rgba(99, 102, 241, 0.2); color: #818cf8;">
                ${state.user.role.toUpperCase()}
            </span>
            <span>${state.user.username}</span>
            <button class="btn btn-outline" onclick="logout()">Выйти</button>
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
window.render = render;

// ─────────────────────────────────────────────────────────────
// Event Listeners Registration
// ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

    // Chat form submit
    document.getElementById('chat-form')?.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = document.getElementById('chat-input').value.trim();
        if (!query) return;
        document.getElementById('chat-input').value = '';
        performChat(query);
    });

    // Auth form toggle
    document.getElementById('auth-toggle')?.addEventListener('click', () => {
        state.isLoginMode = !state.isLoginMode;
        document.getElementById('auth-title').innerText = state.isLoginMode ? 'Вход' : 'Регистрация';
        document.getElementById('auth-submit').innerText = state.isLoginMode ? 'Войти' : 'Создать аккаунт';
        document.getElementById('auth-toggle').innerText = state.isLoginMode
            ? "Нет аккаунта? Зарегистрируйтесь"
            : 'Уже есть аккаунт? Войти';
    });

    // Auth form submit
    document.getElementById('auth-form')?.addEventListener('submit', async (e) => {
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
                showToast('Успешная регистрация!');
            }

            await checkAuth();
            showToast(`Добро пожаловать, ${state.user.username}!`);
        } catch (e) {
            showToast(e.message, 'error');
        } finally {
            btn.innerHTML = state.isLoginMode ? 'Войти' : 'Создать аккаунт';
            btn.disabled = false;
        }
    });

    // Tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Search form submit
    document.getElementById('search-form')?.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = document.getElementById('search-input').value.trim();
        if (!query) return;
        performSearch(query);
    });

    // Create Group button
    document.getElementById('create-group-btn')?.addEventListener('click', () => {
        if(typeof openCreateGroupModal === 'function') {
            openCreateGroupModal();
        }
    });

    // Esc to close modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (typeof closeDocModal === 'function') closeDocModal();
            if (document.getElementById('upload-modal') && document.getElementById('upload-modal').style.display !== 'none' && typeof closeUploadModal === 'function') closeUploadModal();
            if (document.getElementById('group-modal') && document.getElementById('group-modal').style.display !== 'none') {
                if (typeof closeDocAccessModal === 'function') closeDocAccessModal();
                else document.getElementById('group-modal').style.display = 'none';
            }
        }
    });

    // Start App
    checkAuth();
});
