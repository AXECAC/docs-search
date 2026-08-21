// -------------------------------------------------------------
// Search Functions
// -------------------------------------------------------------

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

function renderSearchResults(results, query) {
    const container = document.getElementById('search-results');
    const stateEl = document.getElementById('search-state');

    if (!results || results.length === 0) {
        stateEl.style.display = 'block';
        stateEl.innerText = 'Ничего не найдено. Попробуйте другие ключевые слова.';
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
        const docIcon = EXT_ICONS[extRaw] || '';

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
                    Совпадение: ${scorePercent}%
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
    stateEl.innerHTML = '<div style="display:inline-block" class="spinner"></div>&nbsp; Поиск...';
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
window.performSearch = performSearch;
