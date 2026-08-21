// -------------------------------------------------------------
// Chat Functions
// -------------------------------------------------------------
function appendMessage(role, content) {
    const messagesContainer = document.getElementById('chat-messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    // Using innerHTML to allow basic formatting and sources
    contentDiv.innerHTML = content.replace(/\n/g, '<br>');

    msgDiv.appendChild(contentDiv);
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return contentDiv;
}

async function performChat(query) {
    appendMessage('user', query);

    const submitBtn = document.getElementById('chat-submit-btn');
    const inputField = document.getElementById('chat-input');

    submitBtn.disabled = true;
    inputField.disabled = true;

    // Add a placeholder message for the assistant
    const assistantMsgContent = appendMessage('assistant', '<div class="spinner"></div> Думаю...');

    try {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };

        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ query: query })
        });

        if (response.status === 401) {
            const refreshed = await refreshToken();
            if (!refreshed) {
                logout();
                throw new Error('Session expired');
            }
            // Retry once
            headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
            // For simplicity, we just throw here and let the user click again
            // but normally we would await fetch again.
        }

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        // Streaming logic
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        let fullText = "";
        let sourcesHtml = "";
        assistantMsgContent.innerHTML = ""; // clear spinner

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunkText = decoder.decode(value, { stream: true });
            const lines = chunkText.split('\n').filter(l => l.trim() !== '');

            for (const line of lines) {
                try {
                    const data = JSON.parse(line);

                    if (data.type === 'sources') {
                        if (data.sources && data.sources.length > 0) {
                            const sourceLinks = data.sources.map(s => {
                                const ext = (s.extension || '').replace('.', '').toLowerCase();
                                return `<span class="source-title source-link"
                                    data-doc-id="${s.document_id}"
                                    data-doc-title="${escapeHtml(s.document_title)}"
                                    data-doc-ext="${ext}"
                                    onclick="openDocModal(this.dataset.docId, this.dataset.docTitle, this.dataset.docExt)"
                                    title="Открыть документ">
                                    ${EXT_ICONS[ext] || ''} ${escapeHtml(s.document_title)}
                                </span>`;
                            }).join(' ');
                            sourcesHtml = `<div class="sources-box">
                                <strong>Источники:</strong><br>
                                ${sourceLinks}
                            </div>`;
                            assistantMsgContent.innerHTML = sourcesHtml + fullText;
                        }
                    } else if (data.type === 'content') {
                        fullText += escapeHtml(data.content);
                        assistantMsgContent.innerHTML = sourcesHtml + fullText.replace(/\n/g, '<br>');
                        document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
                    } else if (data.type === 'error') {
                        fullText += `<br><span style="color:var(--danger)">[Ошибка: ${escapeHtml(data.content)}]</span>`;
                        assistantMsgContent.innerHTML = sourcesHtml + fullText.replace(/\n/g, '<br>');
                    }
                } catch (e) {
                    console.error("Parse error chunk:", line, e);
                }
            }
        }

    } catch (e) {
        assistantMsgContent.innerHTML = `<span style="color:var(--danger)">Ошибка: ${e.message}</span>`;
    } finally {
        submitBtn.disabled = false;
        inputField.disabled = false;
        inputField.focus();
    }
}
window.performChat = performChat;
