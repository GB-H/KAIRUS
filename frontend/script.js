const API_URL = "";

const messages = document.getElementById("messages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const newChatButton = document.getElementById("newChat");
const conversationList = document.getElementById("conversationList");
const logoutBtn = document.getElementById("logoutBtn");

let conversationHistory = [];
let isWaiting = false;
let sessionId = generateSessionId();


// =========================
// VERIFICAR AUTENTICACAO
// =========================

function getAuthToken() {
    return localStorage.getItem("kairus_token");
}

if (!getAuthToken()) {
    window.location.href = "/login.html";
}

function generateSessionId() {
    return "session_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
}


// =========================
// LOGOUT
// =========================

logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("kairus_token");
    localStorage.removeItem("kairus_user_id");
    localStorage.removeItem("kairus_username");
    window.location.href = "/login.html";
});


/* =========================
   MODAL DE CONFIRMACAO
========================= */

function showConfirmModal(title, message) {
    return new Promise((resolve) => {
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";

        const modal = document.createElement("div");
        modal.className = "modal";

        modal.innerHTML = `
            <div class="modal-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
            </div>
            <div class="modal-title">${title}</div>
            <div class="modal-message">${message}</div>
            <div class="modal-actions">
                <button class="modal-btn modal-cancel">Cancelar</button>
                <button class="modal-btn modal-confirm">Excluir</button>
            </div>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        requestAnimationFrame(() => {
            overlay.classList.add("active");
            modal.classList.add("active");
        });

        const closeModal = (result) => {
            overlay.classList.remove("active");
            modal.classList.remove("active");
            setTimeout(() => overlay.remove(), 200);
            resolve(result);
        };

        modal.querySelector(".modal-cancel").addEventListener("click", () => closeModal(false));
        modal.querySelector(".modal-confirm").addEventListener("click", () => closeModal(true));
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) closeModal(false);
        });
    });
}


/* =========================
   ADICIONAR MENSAGEM
========================= */

function addMessage(role, text, meta) {

    const welcome = document.querySelector(".welcome");

    if (welcome) {
        welcome.remove();
    }

    const message = document.createElement("div");

    message.className = `message ${
        role === "user" ? "user-message" : "ai-message"
    }`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "EU" : "K";

    const contentWrapper = document.createElement("div");
    contentWrapper.className = "message-content-wrapper";

    if (meta && (meta.llm || meta.tool)) {
        const badgesDiv = document.createElement("div");
        badgesDiv.className = "message-badges";
        if (meta.llm) {
            const badge = document.createElement("span");
            badge.className = "llm-badge";
            badge.textContent = "LLM";
            badge.title = "Resposta gerada por inteligencia artificial";
            badgesDiv.appendChild(badge);
        }
        if (meta.tool) {
            const badge = document.createElement("span");
            badge.className = "tool-badge";
            badge.textContent = meta.tool;
            badge.title = "Ferramenta utilizada";
            badgesDiv.appendChild(badge);
        }
        contentWrapper.appendChild(badgesDiv);
    }

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = text;

    contentWrapper.appendChild(content);

    message.appendChild(avatar);
    message.appendChild(contentWrapper);

    messages.appendChild(message);

    scrollToBottom();

    return message;
}


/* =========================
   MENSAGEM DE STREAMING
========================= */

function createStreamingMessage() {
    const welcome = document.querySelector(".welcome");
    if (welcome) welcome.remove();

    const message = document.createElement("div");
    message.className = "message ai-message";

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = "K";

    const contentWrapper = document.createElement("div");
    contentWrapper.className = "message-content-wrapper";

    const badgesDiv = document.createElement("div");
    badgesDiv.className = "message-badges";
    badgesDiv.style.display = "none";
    contentWrapper.appendChild(badgesDiv);

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = "";
    contentWrapper.appendChild(content);

    const cursor = document.createElement("span");
    cursor.className = "stream-cursor";
    content.appendChild(cursor);

    message.appendChild(avatar);
    message.appendChild(contentWrapper);
    messages.appendChild(message);

    scrollToBottom();

    return {
        message,
        content,
        contentWrapper,
        badgesDiv,

        appendToken(token) {
            const existingCursor = content.querySelector(".stream-cursor");
            if (existingCursor) existingCursor.remove();
            content.insertAdjacentText("beforeend", token);
            content.appendChild(cursor);
            scrollToBottom();
        },

        finish() {
            const existingCursor = content.querySelector(".stream-cursor");
            if (existingCursor) existingCursor.remove();
        },

        setBadges(meta) {
            if (meta.llm) {
                const badge = document.createElement("span");
                badge.className = "llm-badge";
                badge.textContent = "LLM";
                badge.title = "Resposta gerada por inteligencia artificial";
                badgesDiv.appendChild(badge);
                badgesDiv.style.display = "block";
            }
            if (meta.tool) {
                const badge = document.createElement("span");
                badge.className = "tool-badge";
                badge.textContent = meta.tool;
                badge.title = "Ferramenta utilizada";
                badgesDiv.appendChild(badge);
                badgesDiv.style.display = "block";
            }
        }
    };
}


/* =========================
   INDICADOR DE DIGITACAO
========================= */

function showTyping() {

    const message = document.createElement("div");
    message.className = "message ai-message typing-message";
    message.id = "typingIndicator";

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = "K";

    const content = document.createElement("div");
    content.className = "message-content";

    const dots = document.createElement("div");
    dots.className = "typing-indicator";
    dots.innerHTML = "<span></span><span></span><span></span>";

    content.appendChild(dots);

    message.appendChild(avatar);
    message.appendChild(content);

    messages.appendChild(message);

    scrollToBottom();
}

function hideTyping() {
    const typing = document.getElementById("typingIndicator");
    if (typing) {
        typing.remove();
    }
}


function scrollToBottom() {
    messages.scrollTo({
        top: messages.scrollHeight,
        behavior: "smooth"
    });
}


/* =========================
   FASE 2.3/2.5 - PIPELINE VISUAL DE AGENTES
========================= */

function clearPipelineLoading() {
    const loading = document.getElementById("pipelineLoading");
    if (loading) loading.remove();
}

function renderPipelineStart() {
    clearPipelineLoading();

    const bar = document.createElement("div");
    bar.className = "agent-pipeline";
    bar.id = "pipelineLoading";

    const chip = document.createElement("span");
    chip.className = "agent-chip status-retry";
    chip.textContent = "🧠 ativando equipe de agentes…";
    bar.appendChild(chip);

    messages.appendChild(bar);
    scrollToBottom();
}

function renderAgentSteps(steps) {
    clearPipelineLoading();

    if (!steps || steps.length === 0) return;

    const bar = document.createElement("div");
    bar.className = "agent-pipeline";

    const icons = {
        ok: "✓",
        retry: "⟳",
        fail: "✗",
        block: "🛡",
        skip: "○",
    };

    steps.forEach((s) => {
        const chip = document.createElement("span");
        chip.className = "agent-chip status-" + (s.status || "ok");
        chip.textContent =
            s.agent + " " + (icons[s.status] || "✓");
        bar.appendChild(chip);
    });

    messages.appendChild(bar);
    scrollToBottom();
}


/* =========================
   ENVIAR MENSAGEM
========================= */

chatForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const text = messageInput.value.trim();

    if (!text || isWaiting) {
        return;
    }

    isWaiting = true;
    sendButton.disabled = true;

    addMessage("user", text);

    conversationHistory.push({
        role: "user",
        content: text
    });

    messageInput.value = "";
    messageInput.style.height = "auto";

    showTyping();

    let fullResponse = "";
    let meta = { llm: false, tool: null };
    let streamingMsg = null;

    try {

        const response = await fetch(`${API_URL}/api/chat/stream`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({
                message: text,
                session_id: sessionId
            })
        });

        if (response.status === 401) {
            localStorage.removeItem("kairus_token");
            window.location.href = "/login.html";
            return;
        }

        if (!response.ok) {
            throw new Error("Erro na API");
        }

        hideTyping();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;

                const payload = line.substring(6).trim();
                if (payload === "[DONE]") continue;

                try {
                    const event = JSON.parse(payload);

                    if (event.type === "meta") {
                        meta = event;
                        streamingMsg = createStreamingMessage();
                    } else if (event.type === "pipeline_start") {
                        renderPipelineStart();
                    } else if (event.type === "agents") {
                        renderAgentSteps(event.steps);
                    } else if (event.type === "token") {
                        if (!streamingMsg) {
                            streamingMsg = createStreamingMessage();
                            if (meta.llm || meta.tool) {
                                streamingMsg.setBadges(meta);
                            }
                        }
                        streamingMsg.appendToken(event.text);
                        fullResponse += event.text;
                    } else if (event.type === "done") {
                        clearPipelineLoading();
                        if (streamingMsg && (event.llm || event.tool)) {
                            streamingMsg.setBadges(event);
                        }
                        if (streamingMsg) streamingMsg.finish();
                        fullResponse = event.response || fullResponse;
                    }
                } catch (e) {
                    // JSON invalido
                }
            }
        }

        conversationHistory.push({
            role: "assistant",
            content: fullResponse
        });

        await loadConversations();

        const memResp = await fetch(`${API_URL}/api/chat/memory?session_id=${sessionId}`, {
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });
        if (memResp.ok) {
            const memData = await memResp.json();
            updateMemoryInfo({
                message_count: memData.message_count,
                user_name: memData.user_info?.name
            });
        }

    } catch (error) {

        console.error(error);

        hideTyping();
        clearPipelineLoading();

        if (!streamingMsg) {
            addMessage(
                "assistant",
                "Nao consegui me conectar ao servidor KAIRUS."
            );
        } else {
            streamingMsg.finish();
        }

    } finally {

        isWaiting = false;
        sendButton.disabled = !messageInput.value.trim();
        messageInput.focus();

    }

});


/* =========================
   INFO DE MEMORIA
========================= */

function updateMemoryInfo(memoryData) {
    if (!memoryData) return;

    let versionEl = document.querySelector(".version");
    if (versionEl) {
        let info = "KAIRUS v0.4.0";
        if (memoryData.message_count) {
            info += " | " + memoryData.message_count + " msgs";
        }
        if (memoryData.user_name) {
            info += " | " + memoryData.user_name;
        }
        versionEl.textContent = info;
    }
}


/* =========================
   LISTA DE CONVERSAS
========================= */

async function loadConversations() {

    try {

        const response = await fetch(`${API_URL}/api/conversations`, {
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });

        if (response.status === 401) {
            localStorage.removeItem("kairus_token");
            window.location.href = "/login.html";
            return;
        }

        const data = await response.json();

        conversationList.innerHTML = "";

        data.conversations.forEach(conv => {

            const item = document.createElement("div");
            item.className = "conversation-item";

            const title = document.createElement("div");
            title.className = "conversation";

            if (conv.id === sessionId) {
                title.classList.add("active");
            }

            title.textContent = conv.title || "Nova conversa";

            title.addEventListener("click", () => {
                loadConversation(conv.id);
            });

            const deleteBtn = document.createElement("button");
            deleteBtn.className = "delete-conversation";
            deleteBtn.title = "Excluir conversa";
            deleteBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>`;

            deleteBtn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const confirmed = await showConfirmModal(
                    "Excluir conversa",
                    `Tem certeza que deseja excluir "${conv.title}"? Esta acao nao pode ser desfeita.`
                );
                if (confirmed) {
                    deleteConversation(conv.id);
                }
            });

            item.appendChild(title);
            item.appendChild(deleteBtn);

            conversationList.appendChild(item);

        });

    } catch (e) {
        console.error("Erro ao carregar conversas:", e);
    }

}


/* =========================
   EXCLUIR CONVERSA
========================= */

async function deleteConversation(convId) {

    try {

        const response = await fetch(`${API_URL}/api/conversations/${convId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });

        if (response.ok) {
            if (convId === sessionId) {
                sessionId = generateSessionId();
                conversationHistory = [];
                showWelcome();

                let versionEl = document.querySelector(".version");
                if (versionEl) {
                    versionEl.textContent = "KAIRUS v0.4.0";
                }
            }

            loadConversations();
        }

    } catch (e) {
        console.error("Erro ao excluir conversa:", e);
    }

}


/* =========================
   CARREGAR CONVERSA
========================= */

async function loadConversation(convId) {

    try {

        const response = await fetch(`${API_URL}/api/conversations/${convId}/messages`, {
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });
        const data = await response.json();

        sessionId = convId;
        conversationHistory = [];

        messages.innerHTML = "";

        if (data.messages.length === 0) {
            showWelcome();
            return;
        }

        data.messages.forEach(msg => {
            addMessage(msg.role, msg.content);
            conversationHistory.push({
                role: msg.role,
                content: msg.content
            });
        });

        let versionEl = document.querySelector(".version");
        if (versionEl) {
            let info = "KAIRUS v0.4.0 | " + data.messages.length + " msgs";
            versionEl.textContent = info;
        }

        loadConversations();

        messageInput.focus();

    } catch (e) {
        console.error("Erro ao carregar conversa:", e);
    }

}


/* =========================
   TELA DE BOAS-VINDAS
========================= */

function showWelcome() {
    messages.innerHTML = `
        <div class="welcome" id="welcomeScreen">

            <img src="logo.png" alt="KAIRUS" class="welcome-logo-img">

            <h1>
                Como posso ajudar?
            </h1>

            <p>
                Converse com o KAIRUS.
            </p>

            <div class="suggestions" id="suggestions">
                <button class="suggestion" data-message="Quem e voce?">
                    Quem e voce?
                </button>
                <button class="suggestion" data-message="O que voce sabe fazer?">
                    O que voce sabe fazer?
                </button>
                <button class="suggestion" data-message="Conta uma piada">
                    Conta uma piada
                </button>
                <button class="suggestion" data-message="Me explique buracos negros">
                    Me explique buracos negros
                </button>
            </div>

        </div>
    `;

    initSuggestions();
}


/* =========================
   ALTURA DO TEXTAREA
========================= */

messageInput.addEventListener("input", () => {

    messageInput.style.height = "auto";

    messageInput.style.height =
        `${Math.min(messageInput.scrollHeight, 180)}px`;

    sendButton.disabled = !messageInput.value.trim() || isWaiting;

});


/* =========================
   ENTER PARA ENVIAR
========================= */

messageInput.addEventListener("keydown", (event) => {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();

        chatForm.requestSubmit();

    }

});


/* =========================
   NOVA CONVERSA
========================= */

newChatButton.addEventListener("click", async () => {

    sessionId = generateSessionId();
    conversationHistory = [];
    isWaiting = false;

    showWelcome();

    let versionEl = document.querySelector(".version");
    if (versionEl) {
        versionEl.textContent = "KAIRUS v0.4.0";
    }

    sendButton.disabled = true;
    messageInput.focus();

    loadConversations();

});


/* =========================
   SUGESTOES RAPIDAS
========================= */

function initSuggestions() {

    const suggestions = document.querySelectorAll(".suggestion");

    suggestions.forEach(button => {

        button.addEventListener("click", () => {

            const message = button.getAttribute("data-message");

            if (message && !isWaiting) {
                messageInput.value = message;
                chatForm.requestSubmit();
            }

        });

    });

}

initSuggestions();


/* =========================
   VERIFICAR STATUS DO SERVIDOR
========================= */

async function checkServerStatus() {

    const statusDot = document.querySelector(".status-dot");
    const statusText = document.querySelector(".status-text");

    try {

        const response = await fetch(`${API_URL}/api/health`);

        if (response.ok) {
            statusDot.classList.remove("offline");
            statusText.textContent = "Sistema online";
        } else {
            throw new Error();
        }

    } catch {

        statusDot.classList.add("offline");
        statusText.textContent = "Sistema offline";

    }

}

checkServerStatus();
setInterval(checkServerStatus, 30000);


/* =========================
   SIDEBAR COLAPSAVEL
========================= */

const appEl = document.getElementById("app");
const sidebarToggle = document.getElementById("sidebarToggle");

sidebarToggle.addEventListener("click", () => {
    appEl.classList.toggle("collapsed");
    localStorage.setItem(
        "kairus_sidebar",
        appEl.classList.contains("collapsed") ? "collapsed" : "open"
    );
});

if (localStorage.getItem("kairus_sidebar") === "collapsed") {
    appEl.classList.add("collapsed");
}


/* =========================
   INICIALIZACAO
========================= */

loadConversations();
messageInput.focus();
/* =========================
   MOBILE - MENU HAMBURGUER
========================= */

const menuToggle = document.getElementById("menuToggle");
const sidebarOverlay = document.getElementById("sidebarOverlay");

menuToggle.addEventListener("click", () => {
    appEl.classList.toggle("sidebar-open");
});

sidebarOverlay.addEventListener("click", () => {
    appEl.classList.remove("sidebar-open");
});

conversationList.addEventListener("click", (e) => {
    if (e.target.closest(".conversation")) {
        appEl.classList.remove("sidebar-open");
    }
});

newChatButton.addEventListener("click", () => {
    appEl.classList.remove("sidebar-open");
});