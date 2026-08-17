const API_URL = "http://127.0.0.1:8000";

const messages = document.getElementById("messages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const newChatButton = document.getElementById("newChat");
const conversationList = document.getElementById("conversationList");

let conversationHistory = [];
let isWaiting = false;
let sessionId = generateSessionId();


function generateSessionId() {
    return "session_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
}


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

        // Animacao de entrada
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

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = text;

    contentWrapper.appendChild(content);

    if (meta && meta.llm) {
        const badge = document.createElement("span");
        badge.className = "llm-badge";
        badge.textContent = "LLM";
        badge.title = "Resposta gerada por inteligencia artificial";
        contentWrapper.appendChild(badge);
    }

    if (meta && meta.tool) {
        const badge = document.createElement("span");
        badge.className = "tool-badge";
        badge.textContent = meta.tool;
        badge.title = "Ferramenta utilizada";
        contentWrapper.appendChild(badge);
    }

    message.appendChild(avatar);
    message.appendChild(contentWrapper);

    messages.appendChild(message);

    scrollToBottom();

    return message;
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

    try {

        const response = await fetch(`${API_URL}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: text,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error("Erro na API");
        }

        const data = await response.json();

        hideTyping();

        addMessage("assistant", data.response, {
            llm: data.llm || false,
            tool: data.tool || null,
        });

        conversationHistory.push({
            role: "assistant",
            content: data.response
        });

        updateMemoryInfo(data.memory);

        loadConversations();

    } catch (error) {

        console.error(error);

        hideTyping();

        addMessage(
            "assistant",
            "Nao consegui me conectar ao servidor KAIRUS."
        );

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
        let info = "KAIRUS v0.3.0";
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

        const response = await fetch(`${API_URL}/api/conversations`);
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
            method: "DELETE"
        });

        if (response.ok) {
            if (convId === sessionId) {
                sessionId = generateSessionId();
                conversationHistory = [];
                showWelcome();

                let versionEl = document.querySelector(".version");
                if (versionEl) {
                    versionEl.textContent = "KAIRUS v0.3.0";
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

        const response = await fetch(`${API_URL}/api/conversations/${convId}/messages`);
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
            let info = "KAIRUS v0.3.0 | " + data.messages.length + " msgs";
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

            <div class="welcome-logo">
                K
            </div>

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
        versionEl.textContent = "KAIRUS v0.3.0";
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
   INICIALIZACAO
========================= */

loadConversations();
messageInput.focus();