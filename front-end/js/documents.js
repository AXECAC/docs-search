// -------------------------------------------------------------
// Document Functions
// -------------------------------------------------------------
const DOCS_PAGE_SIZE = 12;
let docsCurrentPage = 1;
let docsFilterQuery = '';

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
    if (!confirm('Вы уверены, что хотите удалить этот документ?')) return;
    try {
        await apiFetch(`/documents/${id}`, { method: 'DELETE' });
        showToast('Документ удален');
        fetchDocuments();
    } catch (e) { console.error(e); }
}

window.deleteDocument = deleteDocument;

function onDocsFilter(value) {
    docsFilterQuery = value.trim().toLowerCase();
    docsCurrentPage = 1;
    fetchDocuments();
}
window.onDocsFilter = onDocsFilter;

const INLINE_EXTS = new Set(['pdf', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg']);

const EXT_ICONS = {
    pdf: 'PDF', txt: 'TXT', png: 'IMG', jpg: 'IMG', jpeg: 'IMG', gif: 'IMG',
    webp: 'IMG', svg: 'IMG', docx: 'DOC', doc: 'DOC', xlsx: 'XLS', xls: 'XLS',
    pptx: 'PPT', ppt: 'PPT',
};

function renderDocuments() {
    const grid = document.getElementById('docs-grid');
    const paginationEl = document.getElementById('docs-pagination');

    if (!state.documents || state.documents.length === 0) {
        grid.innerHTML = `<p style="color: var(--text-muted);">${docsFilterQuery ? 'По вашему запросу документы не найдены.' : 'Документы не найдены.'}</p>`;
        if (paginationEl) paginationEl.innerHTML = '';
        return;
    }

    grid.innerHTML = state.documents.map(doc => {
        const extRaw = (doc.extension || '').replace('.', '').toLowerCase();
        const extLabel = extRaw ? extRaw.toUpperCase() : 'UNKNOWN';
        const docIcon = EXT_ICONS[extRaw] || '';
        const uploaderLabel = doc.uploader_username ? `Загрузил: ${escapeHtml(doc.uploader_username)}` : '';
        return `
        <div class="doc-card glass">
            <div class="doc-header">
                <div class="doc-title">${docIcon} ${escapeHtml(doc.title || 'Untitled')}</div>
                <span class="badge">${extLabel}</span>
            </div>
            <div class="doc-meta">
                <span>Размер: ${formatBytes(doc.size_bytes)}</span>
                <span>Дата: ${new Date(doc.upload_date).toLocaleDateString()}</span>
                ${uploaderLabel ? `<span>${uploaderLabel}</span>` : ''}
            </div>
            <div style="margin-top: auto; display: flex; gap: 0.5rem; justify-content: flex-end; flex-wrap: wrap;">
                <button class="btn btn-outline"
                    data-doc-id="${doc.id}"
                    data-doc-title="${escapeHtml(doc.title || 'Untitled')}"
                    data-doc-ext="${extRaw}"
                    onclick="openDocModal(this.dataset.docId, this.dataset.docTitle, this.dataset.docExt)">
                    Открыть
                </button>
                ${(state.user.role === 'admin' || state.user.id === doc.uploader_id) ? `
                    <button class="btn btn-outline" style="color: var(--primary);"
                        onclick="openDocAccessModal('${doc.id}', ${JSON.stringify(doc.available_to_groups || []).replace(/"/g, '&quot;')})">
                        Доступ
                    </button>
                    <button class="btn btn-danger" onclick="deleteDocument('${doc.id}')">Удалить</button>
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

window.goToDocsPage = function (page) {
    const { pages } = state.docsPagination || { pages: 1 };
    if (page < 1 || page > pages) return;
    docsCurrentPage = page;
    fetchDocuments();
    document.getElementById('docs-grid').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// -------------------------------------------------------------
// Document Preview Modal
// -------------------------------------------------------------
async function openDocModal(documentId, documentTitle, extension) {
    const modal = document.getElementById('doc-modal');
    const icon = document.getElementById('modal-icon');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    const downloadBtn = document.getElementById('modal-download-btn');

    const ext = (extension || '').replace('.', '').toLowerCase();

    // Показываем модалку сразу с лоадером
    icon.textContent = EXT_ICONS[ext] || '';
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
            ${docMeta.author ? `<span>Автор: <strong>${escapeHtml(docMeta.author)}</strong></span>` : ''}
            ${docMeta.uploader_username ? `<span>Загрузил: <strong>${escapeHtml(docMeta.uploader_username)}</strong></span>` : ''}
            ${docMeta.upload_date ? `<span>Дата: <strong>${new Date(docMeta.upload_date).toLocaleDateString('ru-RU')}</strong></span>` : ''}
            ${docMeta.size_bytes ? `<span>Размер: <strong>${formatBytes(docMeta.size_bytes)}</strong></span>` : ''}
            ${docMeta.description ? `<span style="grid-column:1/-1">${escapeHtml(docMeta.description)}</span>` : ''}
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
                    <div class="file-icon">${EXT_ICONS[ext] || 'DOC'}</div>
                    <h3>${escapeHtml(documentTitle || 'Document')}</h3>
                    ${metaHtml}
                    <p>Формат <strong>.${ext.toUpperCase()}</strong> нельзя отобразить прямо в браузере.
                    Нажмите кнопку ниже, чтобы скачать файл.</p>
                    <a href="${blobUrl}" download="${escapeHtml(documentTitle || 'document')}"
                       class="btn btn-primary" style="font-size: 1rem; padding: 0.75rem 2rem;">
                       Скачать файл
                    </a>
                </div>`;
        }

        // Сохраняем blobUrl для освобождения при закрытии
        modal.dataset.blobUrl = blobUrl;

    } catch (e) {
        body.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--danger)">
            Ошибка загрузки файла: ${escapeHtml(e.message)}
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

// -------------------------------------------------------------
// Upload Modal & Logic
// -------------------------------------------------------------
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
        if (!state.groups.length && typeof fetchGroups === 'function') await fetchGroups(false); // don't render view, just fetch
    }

    modal.innerHTML = `
        <div class="doc-modal-panel upload-modal-panel">
            <div class="dashboard-header" style="padding: 1.5rem; border-bottom: 1px solid var(--glass-border); margin-bottom: 0;">
                <h3 style="margin:0;">Загрузка документа</h3>
                <button class="btn btn-outline" onclick="closeUploadModal()" style="padding: 0.4rem 0.8rem;">✕</button>
            </div>
            <div class="upload-modal-body">
                
                <!-- File Drop Zone -->
                <div class="file-drop-zone" id="modal-drop-zone" onclick="document.getElementById('modalFileInput').click()">
                    <span class="file-drop-icon">DOC</span>
                    <h4 id="modal-drop-text">${file ? 'Файл выбран' : 'Нажмите или перетащите файл сюда'}</h4>
                    <div id="modal-file-name" class="file-selected-name">${file ? file.name : ''}</div>
                    <input type="file" id="modalFileInput" style="display: none;">
                </div>

                <!-- Title/Desc -->
                <div class="form-group">
                    <label>Название (опционально)</label>
                    <input type="text" id="upload-title" class="input-control" placeholder="Название документа...">
                </div>
                <div class="form-group">
                    <label>Описание (опционально)</label>
                    <textarea id="upload-desc" placeholder="Краткое описание..."></textarea>
                </div>

                <!-- Access Control -->
                <div class="form-group">
                    <label>Настройки доступа</label>
                    <div class="access-toggle">
                        <button class="access-toggle-btn active" id="btn-access-all" onclick="toggleAccessType('all')">Публичный</button>
                        <button class="access-toggle-btn" id="btn-access-restricted" onclick="toggleAccessType('restricted')">Ограниченный</button>
                    </div>

                    <div id="restricted-panel" class="access-panel">
                        <div style="font-size:0.8rem; color:var(--text-muted);">Выберите группы или пользователей, которым будет доступен этот документ.</div>
                        
                        <label style="font-size:0.75rem;">Группы</label>
                        <div class="tag-select-wrap" id="upload-group-list">
                            ${state.groups.map(g => `
                                <label class="tag-item">
                                    <span>
                                        <input type="checkbox" value="${g.id}" onchange="toggleUploadGroup('${g.id}', this.checked)">
                                        ${escapeHtml(g.name)}
                                    </span>
                                </label>
                            `).join('')}
                            ${state.groups.length === 0 ? '<div style="padding:0.5rem; font-size:0.8rem; color:var(--text-muted);">Нет доступных групп</div>' : ''}
                        </div>

                        ${state.user && state.user.role === 'admin' ? `
                        <label style="font-size:0.75rem; margin-top: 0.5rem;">Конкретные пользователи (по логину)</label>
                        <div class="search-wrap">
                            <input type="text" class="input-control" id="upload-user-search" placeholder="Введите логин..." oninput="debounceUserSearch(this.value, 'upload')" style="width:100%">
                            <div id="upload-user-results" class="search-results-dropdown" style="display:none;"></div>
                        </div>
                        <div class="user-chips" id="upload-selected-users"></div>
                        ` : ''}
                    </div>
                </div>

            </div>
            <div class="upload-modal-footer">
                <button class="btn btn-outline" onclick="closeUploadModal()">Отмена</button>
                <button class="btn btn-primary" onclick="submitUpload()">Загрузить</button>
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
            document.getElementById('modal-drop-text').textContent = 'Файл выбран';
            document.getElementById('modal-file-name').textContent = pendingUploadFile.name;
        }
    });
    fileIn.addEventListener('change', (e) => {
        if (e.target.files.length) {
            pendingUploadFile = e.target.files[0];
            document.getElementById('modal-drop-text').textContent = 'Файл выбран';
            document.getElementById('modal-file-name').textContent = pendingUploadFile.name;
        }
    });
}

function closeUploadModal() {
    document.getElementById('upload-modal').style.display = 'none';
    document.body.style.overflow = '';
    pendingUploadFile = null;
}
window.closeUploadModal = closeUploadModal;

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
            uploadBtn.title = 'Вы не состоите ни в одной группе - невозможно ограничить доступ';
        }
    }
}

window.toggleUploadGroup = function (groupId, isChecked) {
    if (isChecked) selectedUploadGroups.add(groupId);
    else selectedUploadGroups.delete(groupId);
}

// User Search for modal
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
            dropdown.innerHTML = '<div class="dropdown-item" style="color:var(--text-muted)">Пользователи не найдены</div>';
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
        if (typeof renderGroupSelectedUsers === 'function') renderGroupSelectedUsers();
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
            ${escapeHtml(u.username)}
            <span class="chip-remove" onclick="removeUploadUser('${u.id}')">✕</span>
        </div>
    `).join('');
}

async function submitUpload() {
    if (!pendingUploadFile) {
        showToast('Пожалуйста, сначала выберите файл', 'error');
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

    showToast('Загрузка...', 'success');
    closeUploadModal();

    try {
        await apiFetch('/documents/upload', {
            method: 'POST',
            body: formData,
        });
        showToast('Файл успешно загружен!');
        if (state.activeTab === 'dashboard') fetchDocuments();
    } catch (e) {
        console.error(e);
    }
}
window.submitUpload = submitUpload;
