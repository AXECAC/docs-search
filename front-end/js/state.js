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
