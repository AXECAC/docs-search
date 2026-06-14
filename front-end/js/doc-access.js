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
                <h3 style="margin:0;">Доступ к документу</h3>
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
                    ${docAccessSelectedGroups.size === 0 ? 'Документ публичный' : `Доступ ограничен: ${docAccessSelectedGroups.size} гр.`}
                </div>
            </div>
            <div class="upload-modal-footer">
                <button class="btn btn-outline" onclick="closeDocAccessModal()">Отмена</button>
                <button class="btn btn-primary" onclick="submitDocAccess()">Сохранить</button>
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
            ? 'Документ публичный'
            : `Доступ ограничен: ${docAccessSelectedGroups.size} гр.`;
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
