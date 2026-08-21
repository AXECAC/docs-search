// -------------------------------------------------------------
// Theme Management
// -------------------------------------------------------------

function initTheme() {
    const savedTheme = localStorage.getItem('app-theme');
    // Default to light theme if no saved theme
    const themeToApply = savedTheme || 'light';
    document.documentElement.setAttribute('data-theme', themeToApply);

    window.addEventListener('DOMContentLoaded', () => {
        const btn = document.getElementById('theme-toggle-btn');
        if (btn) {
            btn.innerHTML = themeToApply === 'dark' ? 'Светлая' : 'Темная';
        }
    });
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('app-theme', newTheme);

    // Update button text if it exists
    const btn = document.getElementById('theme-toggle-btn');
    if (btn) {
        btn.innerHTML = newTheme === 'dark' ? 'Светлая' : 'Темная';
    }
}

window.toggleTheme = toggleTheme;

// Initialize theme immediately to prevent flash
initTheme();
