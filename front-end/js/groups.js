// ─────────────────────────────────────────────────────────────
// Groups Management
// ─────────────────────────────────────────────────────────────

async function fetchGroups(render = true) {
    try {
        state.groups = await apiFetch('/groups');
        if (render) renderGroups();
    } catch (e) { console.error(e); }
}
window.fetchGroups = fetchGroups;

function renderGroups() {
    const container = document.getElementById('groups-list');
    if (!container) return;

    if (state.groups.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">Группы не найдены.</p>';
        return;
    }

    container.innerHTML = state.groups.map(g => `
        <div class="group-card glass">
            <div class="group-card-header" onclick="toggleGroupMembers('${g.id}')">
                <div>
                    <div class="group-card-title">${escapeHtml(g.name)}</div>
                    <div class="group-card-meta">${escapeHtml(g.description || 'Нет описания')} • Участников: ${g.member_count}</div>
                </div>
                <div class="group-card-actions">
                    <button class="btn btn-danger" onclick="event.stopPropagation(); deleteGroup('${g.id}')" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;">Удалить</button>
                </div>
            </div>
            <div class="group-members-panel" id="group-panel-${g.id}">
                <div class="spinner" style="width:20px; height:20px;"></div> Загрузка участников...
            </div>
        </div>
    `).join('');
}
window.renderGroups = renderGroups;

window.deleteGroup = async function (id) {
    if (!confirm('Удалить эту группу?')) return;
    try {
        await apiFetch(`/groups/${id}`, { method: 'DELETE' });
        showToast('Группа удалена');
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
                ${members.length === 0 ? '<div style="color:var(--text-muted); font-size:0.85rem;">Пока нет участников</div>' : ''}
                ${members.map(m => `
                    <div class="member-row">
                        <div class="member-info">
                            <span>${escapeHtml(m.username)}</span>
                            <span class="member-role">${m.role}</span>
                        </div>
                        <button class="btn btn-outline" style="border-color:var(--danger); color:var(--danger); padding:0.2rem 0.5rem; font-size:0.7rem;" 
                                onclick="removeMember('${groupId}', '${m.id}')">Исключить</button>
                    </div>
                `).join('')}
            </div>
            <div class="add-member-row">
                <div class="search-wrap" style="flex:1;">
                    <input type="text" class="input-control" id="search-add-${groupId}" placeholder="Добавить пользователя по логину..." 
                           oninput="debounceAddMemberSearch(this.value, '${groupId}')" style="width:100%; padding: 0.4rem 0.8rem;">
                    <div id="results-add-${groupId}" class="search-results-dropdown" style="display:none; bottom:100%; top:auto; margin-bottom:4px;"></div>
                </div>
            </div>
        `;
    } catch (e) {
        panel.innerHTML = '<div style="color:var(--danger)">Не удалось загрузить участников</div>';
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
            dropdown.innerHTML = '<div class="dropdown-item" style="color:var(--text-muted)">Пользователи не найдены</div>';
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
        showToast('Пользователь добавлен');
        toggleGroupMembers(groupId); // Refresh open panel
        toggleGroupMembers(groupId);
        fetchGroups(true); // update member counts
    } catch (e) { console.error(e); }
}

window.removeMember = async function (groupId, userId) {
    try {
        await apiFetch(`/groups/${groupId}/members/${userId}`, { method: 'DELETE' });
        showToast('Пользователь исключен');
        toggleGroupMembers(groupId); // Refresh open panel
        toggleGroupMembers(groupId);
        fetchGroups(true);
    } catch (e) { console.error(e); }
}

// Create Group logic
window.openCreateGroupModal = function() {
    const modal = document.getElementById('group-modal');
    modal.innerHTML = `
        <div class="doc-modal-panel upload-modal-panel" style="max-width: 400px;">
            <div class="dashboard-header" style="padding: 1.5rem; border-bottom: 1px solid var(--glass-border); margin-bottom: 0;">
                <h3 style="margin:0;">Создать группу</h3>
                <button class="btn btn-outline" onclick="document.getElementById('group-modal').style.display='none'" style="padding: 0.4rem 0.8rem;">✕</button>
            </div>
            <div class="upload-modal-body">
                <div class="form-group">
                    <label>Название группы</label>
                    <input type="text" id="new-group-name" class="input-control" placeholder="Например: Менеджеры" style="min-height: auto;">
                </div>
                <div class="form-group">
                    <label>Описание</label>
                    <textarea id="new-group-desc" placeholder="Краткое описание..."></textarea>
                </div>
            </div>
            <div class="upload-modal-footer">
                <button class="btn btn-outline" onclick="document.getElementById('group-modal').style.display='none'">Отмена</button>
                <button class="btn btn-primary" onclick="submitCreateGroup()">Создать</button>
            </div>
        </div>
    `;
    modal.style.display = 'flex';
}

window.submitCreateGroup = async function () {
    const name = document.getElementById('new-group-name').value.trim();
    const desc = document.getElementById('new-group-desc').value.trim();
    if (!name) return showToast('Название обязательно', 'error');

    try {
        await apiFetch('/groups', {
            method: 'POST',
            body: JSON.stringify({ name, description: desc })
        });
        showToast('Группа создана');
        document.getElementById('group-modal').style.display = 'none';
        fetchGroups();
    } catch (e) { console.error(e); }
}
