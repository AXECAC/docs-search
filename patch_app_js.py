import re

with open('front-end/app.js', 'r') as f:
    content = f.read()

# 1. Remove old drag/drop logic that directly calls uploadFile
content = re.sub(
    r"const dropArea = document.getElementById\('uploadArea'\);.*?fileInput\.addEventListener\('change', \(e\) => {.*?uploadFile\(e\.target\.files\[0\]\);\n}\);\n",
    "",
    content,
    flags=re.DOTALL
)

# 2. Remove old uploadFile function
content = re.sub(
    r"async function uploadFile\(file\) \{.*?\n\}\n",
    "",
    content,
    flags=re.DOTALL
)

# 3. Append new logic before // Init
new_logic = """
// ─────────────────────────────────────────────────────────────
// Upload Modal & Logic
// ─────────────────────────────────────────────────────────────

let pendingUploadFile = null;
let selectedUploadGroups = new Set();
let selectedUploadUsers = new Set();

const openUploadBtn = document.getElementById('open-upload-modal-btn');
if(openUploadBtn) {
    openUploadBtn.addEventListener('click', () => openUploadModal());
}

async function openUploadModal(file = null) {
    pendingUploadFile = file;
    selectedUploadGroups.clear();
    selectedUploadUsers.clear();

    const modal = document.getElementById('upload-modal');
    
    // Fetch users/groups for dropdowns
    if (state.user) {
        if (!state.groups.length) await fetchGroups(false); // don't render view, just fetch
    }

    modal.innerHTML = `
        <div class="doc-modal-panel upload-modal-panel">
            <div class="dashboard-header" style="padding: 1.5rem; border-bottom: 1px solid var(--glass-border); margin-bottom: 0;">
                <h3 style="margin:0;">Upload Document</h3>
                <button class="btn btn-outline" onclick="closeUploadModal()" style="padding: 0.4rem 0.8rem;">✕</button>
            </div>
            <div class="upload-modal-body">
                
                <!-- File Drop Zone -->
                <div class="file-drop-zone" id="modal-drop-zone" onclick="document.getElementById('modalFileInput').click()">
                    <span class="file-drop-icon">📄</span>
                    <h4 id="modal-drop-text">${file ? 'File selected' : 'Click or Drag & Drop file here'}</h4>
                    <div id="modal-file-name" class="file-selected-name">${file ? file.name : ''}</div>
                    <input type="file" id="modalFileInput" style="display: none;">
                </div>

                <!-- Title/Desc -->
                <div class="form-group">
                    <label>Title (optional)</label>
                    <input type="text" id="upload-title" class="input-control" placeholder="Document title...">
                </div>
                <div class="form-group">
                    <label>Description (optional)</label>
                    <textarea id="upload-desc" placeholder="Brief description..."></textarea>
                </div>

                <!-- Access Control -->
                <div class="form-group">
                    <label>Access Control</label>
                    <div class="access-toggle">
                        <button class="access-toggle-btn active" id="btn-access-all" onclick="toggleAccessType('all')">Public (All)</button>
                        <button class="access-toggle-btn" id="btn-access-restricted" onclick="toggleAccessType('restricted')">Restricted</button>
                    </div>

                    <div id="restricted-panel" class="access-panel">
                        <div style="font-size:0.8rem; color:var(--text-muted);">Select groups or specific users who can access this document.</div>
                        
                        <label style="font-size:0.75rem;">Groups</label>
                        <div class="tag-select-wrap" id="upload-group-list">
                            ${state.groups.map(g => `
                                <label class="tag-item">
                                    <span>
                                        <input type="checkbox" value="${g.id}" onchange="toggleUploadGroup('${g.id}', this.checked)">
                                        ${escapeHtml(g.name)}
                                    </span>
                                </label>
                            `).join('')}
                            ${state.groups.length === 0 ? '<div style="padding:0.5rem; font-size:0.8rem; color:var(--text-muted);">No groups available</div>' : ''}
                        </div>

                        <label style="font-size:0.75rem;">Specific Users (by username)</label>
                        <div class="search-wrap">
                            <input type="text" class="input-control" id="upload-user-search" placeholder="Type username..." oninput="debounceUserSearch(this.value, 'upload')" style="width:100%">
                            <div id="upload-user-results" class="search-results-dropdown" style="display:none;"></div>
                        </div>
                        <div class="user-chips" id="upload-selected-users"></div>
                    </div>
                </div>

            </div>
            <div class="upload-modal-footer">
                <button class="btn btn-outline" onclick="closeUploadModal()">Cancel</button>
                <button class="btn btn-primary" onclick="submitUpload()">Upload File</button>
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
            document.getElementById('modal-drop-text').textContent = 'File selected';
            document.getElementById('modal-file-name').textContent = pendingUploadFile.name;
        }
    });
    fileIn.addEventListener('change', (e) => {
        if (e.target.files.length) {
            pendingUploadFile = e.target.files[0];
            document.getElementById('modal-drop-text').textContent = 'File selected';
            document.getElementById('modal-file-name').textContent = pendingUploadFile.name;
        }
    });
}

function closeUploadModal() {
    document.getElementById('upload-modal').style.display = 'none';
    document.body.style.overflow = '';
    pendingUploadFile = null;
}

window.toggleAccessType = function(type) {
    const btnAll = document.getElementById('btn-access-all');
    const btnRestricted = document.getElementById('btn-access-restricted');
    const panel = document.getElementById('restricted-panel');

    if (type === 'all') {
        btnAll.classList.add('active');
        btnRestricted.classList.remove('active');
        panel.classList.remove('visible');
        selectedUploadGroups.clear();
        selectedUploadUsers.clear();
        // Uncheck all group boxes
        document.querySelectorAll('#upload-group-list input[type="checkbox"]').forEach(cb => cb.checked = false);
        renderUploadSelectedUsers();
    } else {
        btnRestricted.classList.add('active');
        btnAll.classList.remove('active');
        panel.classList.add('visible');
    }
}

window.toggleUploadGroup = function(groupId, isChecked) {
    if (isChecked) selectedUploadGroups.add(groupId);
    else selectedUploadGroups.delete(groupId);
}

// User Search
let userSearchTimeout = null;
window.debounceUserSearch = function(query, context) {
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
            dropdown.innerHTML = '<div class="dropdown-item" style="color:var(--text-muted)">No users found</div>';
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

window.selectUser = function(id, username, context) {
    document.getElementById(context === 'upload' ? 'upload-user-results' : 'group-user-results').style.display = 'none';
    document.getElementById(context === 'upload' ? 'upload-user-search' : 'group-user-search').value = '';
    
    if (context === 'upload') {
        selectedUploadUsers.add({id, username});
        renderUploadSelectedUsers();
    } else {
        selectedGroupUsers.add({id, username});
        renderGroupSelectedUsers();
    }
}

window.removeUploadUser = function(id) {
    for (let u of selectedUploadUsers) {
        if (u.id === id) { selectedUploadUsers.delete(u); break; }
    }
    renderUploadSelectedUsers();
}

function renderUploadSelectedUsers() {
    const container = document.getElementById('upload-selected-users');
    if(!container) return;
    container.innerHTML = Array.from(selectedUploadUsers).map(u => `
        <div class="chip">
            👤 ${escapeHtml(u.username)}
            <span class="chip-remove" onclick="removeUploadUser('${u.id}')">✕</span>
        </div>
    `).join('');
}

async function submitUpload() {
    if (!pendingUploadFile) {
        showToast('Please select a file first', 'error');
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

    showToast('Uploading...', 'success');
    closeUploadModal();

    try {
        await apiFetch('/documents/upload', {
            method: 'POST',
            body: formData,
        });
        showToast('File uploaded successfully!');
        if (state.activeTab === 'dashboard') fetchDocuments();
    } catch (e) {
        console.error(e);
    }
}


// ─────────────────────────────────────────────────────────────
// Groups Management
// ─────────────────────────────────────────────────────────────

async function fetchGroups(render = true) {
    try {
        state.groups = await apiFetch('/groups');
        if (render) renderGroups();
    } catch (e) { console.error(e); }
}

function renderGroups() {
    const container = document.getElementById('groups-list');
    if (!container) return;
    
    if (state.groups.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">No groups found.</p>';
        return;
    }

    container.innerHTML = state.groups.map(g => `
        <div class="group-card glass">
            <div class="group-card-header" onclick="toggleGroupMembers('${g.id}')">
                <div>
                    <div class="group-card-title">👥 ${escapeHtml(g.name)}</div>
                    <div class="group-card-meta">${escapeHtml(g.description || 'No description')} • ${g.member_count} members</div>
                </div>
                <div class="group-card-actions">
                    <button class="btn btn-danger" onclick="event.stopPropagation(); deleteGroup('${g.id}')" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;">Delete</button>
                </div>
            </div>
            <div class="group-members-panel" id="group-panel-${g.id}">
                <div class="spinner" style="width:20px; height:20px;"></div> Loading members...
            </div>
        </div>
    `).join('');
}

window.deleteGroup = async function(id) {
    if (!confirm('Delete this group?')) return;
    try {
        await apiFetch(`/groups/${id}`, { method: 'DELETE' });
        showToast('Group deleted');
        fetchGroups();
    } catch (e) { console.error(e); }
}

window.toggleGroupMembers = async function(groupId) {
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
                ${members.length === 0 ? '<div style="color:var(--text-muted); font-size:0.85rem;">No members yet</div>' : ''}
                ${members.map(m => `
                    <div class="member-row">
                        <div class="member-info">
                            <span>👤 ${escapeHtml(m.username)}</span>
                            <span class="member-role">${m.role}</span>
                        </div>
                        <button class="btn btn-outline" style="border-color:var(--danger); color:var(--danger); padding:0.2rem 0.5rem; font-size:0.7rem;" 
                                onclick="removeMember('${groupId}', '${m.id}')">Remove</button>
                    </div>
                `).join('')}
            </div>
            <div class="add-member-row">
                <div class="search-wrap" style="flex:1;">
                    <input type="text" class="input-control" id="search-add-${groupId}" placeholder="Add user by username..." 
                           oninput="debounceAddMemberSearch(this.value, '${groupId}')" style="width:100%; padding: 0.4rem 0.8rem;">
                    <div id="results-add-${groupId}" class="search-results-dropdown" style="display:none; bottom:100%; top:auto; margin-bottom:4px;"></div>
                </div>
            </div>
        `;
    } catch (e) {
        panel.innerHTML = '<div style="color:var(--danger)">Failed to load members</div>';
    }
}

let addMemberTimeout = null;
window.debounceAddMemberSearch = function(query, groupId) {
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
            dropdown.innerHTML = '<div class="dropdown-item" style="color:var(--text-muted)">No users found</div>';
        } else {
            dropdown.innerHTML = users.map(u => `
                <div class="dropdown-item" onclick="addMemberToGroup('${groupId}', '${u.id}')">
                    ${escapeHtml(u.username)} <span style="font-size:0.7rem; color:var(--text-muted)">(${u.role})</span>
                </div>
            `).join('');
        }
        dropdown.style.display = 'block';
    } catch(e) {}
}

window.addMemberToGroup = async function(groupId, userId) {
    try {
        await apiFetch(`/groups/${groupId}/members`, {
            method: 'POST',
            body: JSON.stringify({ user_ids: [userId] })
        });
        showToast('Member added');
        toggleGroupMembers(groupId); // Refresh open panel
        toggleGroupMembers(groupId);
        fetchGroups(true); // update member counts
    } catch (e) { console.error(e); }
}

window.removeMember = async function(groupId, userId) {
    try {
        await apiFetch(`/groups/${groupId}/members/${userId}`, { method: 'DELETE' });
        showToast('Member removed');
        toggleGroupMembers(groupId); // Refresh open panel
        toggleGroupMembers(groupId);
        fetchGroups(true);
    } catch (e) { console.error(e); }
}

// Create Group logic
document.getElementById('create-group-btn')?.addEventListener('click', () => {
    const modal = document.getElementById('group-modal');
    modal.innerHTML = `
        <div class="doc-modal-panel upload-modal-panel" style="max-width: 400px;">
            <div class="dashboard-header" style="padding: 1.5rem; border-bottom: 1px solid var(--glass-border); margin-bottom: 0;">
                <h3 style="margin:0;">Create Group</h3>
                <button class="btn btn-outline" onclick="document.getElementById('group-modal').style.display='none'" style="padding: 0.4rem 0.8rem;">✕</button>
            </div>
            <div class="upload-modal-body">
                <div class="form-group">
                    <label>Group Name</label>
                    <input type="text" id="new-group-name" class="input-control" placeholder="E.g. Managers" style="min-height: auto;">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="new-group-desc" placeholder="Brief description..."></textarea>
                </div>
            </div>
            <div class="upload-modal-footer">
                <button class="btn btn-outline" onclick="document.getElementById('group-modal').style.display='none'">Cancel</button>
                <button class="btn btn-primary" onclick="submitCreateGroup()">Create</button>
            </div>
        </div>
    `;
    modal.style.display = 'flex';
});

window.submitCreateGroup = async function() {
    const name = document.getElementById('new-group-name').value.trim();
    const desc = document.getElementById('new-group-desc').value.trim();
    if (!name) return showToast('Name is required', 'error');

    try {
        await apiFetch('/groups', {
            method: 'POST',
            body: JSON.stringify({ name, description: desc })
        });
        showToast('Group created');
        document.getElementById('group-modal').style.display = 'none';
        fetchGroups();
    } catch (e) { console.error(e); }
}

"""

new_content = content.replace("// Init\ncheckAuth();", new_logic + "\n// Init\ncheckAuth();")

with open('front-end/app.js', 'w') as f:
    f.write(new_content)

print("Patched app.js successfully.")
