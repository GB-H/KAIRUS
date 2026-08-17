"""
Gerenciador de memoria do KAIRUS.
Armazena e recupera informacoes da conversa atual.
Integrado com banco de dados para persistencia.
"""

from backend.database.db import (
    create_conversation,
    get_conversation,
    save_message,
    get_messages,
    get_message_count,
    save_user_info,
    get_user_info,
    update_message_count,
    update_conversation_title,
)


class ConversationMemory:
    """
    Memoria de curto prazo para uma conversa.
    Sincroniza com o banco de dados.
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.messages = []
        self.user_info = {}
        self.topics_discussed = []
        self.message_count = 0
        self._loaded = False

    def load_from_db(self):
        """Carrega dados do banco de dados."""
        if self._loaded:
            return

        conv = get_conversation(self.session_id)

        if conv:
            db_messages = get_messages(self.session_id)
            self.messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in db_messages
            ]
            self.user_info = get_user_info(self.session_id)
            self.message_count = len(self.messages)

        self._loaded = True

    def add_message(self, role: str, content: str, intent: str = "unknown"):
        """Adiciona uma mensagem ao historico e salva no DB."""
        self.load_from_db()

        self.messages.append({
            "role": role,
            "content": content,
        })
        self.message_count += 1

        # Salvar no banco
        save_message(self.session_id, role, content, intent)
        update_message_count(self.session_id, self.message_count)

        # Atualizar titulo com a primeira mensagem do usuario
        if role == "user" and self.message_count == 1:
            title = content[:40] + ("..." if len(content) > 40 else "")
            update_conversation_title(self.session_id, title)

    def get_recent_messages(self, count: int = 5) -> list:
        """Retorna as ultimas N mensagens."""
        self.load_from_db()
        return self.messages[-count:]

    def get_context_summary(self) -> str:
        """Retorna um resumo do contexto atual."""
        self.load_from_db()

        parts = []

        if self.user_info.get("name"):
            parts.append(f"Nome do usuario: {self.user_info['name']}")

        if self.topics_discussed:
            unique_topics = list(dict.fromkeys(self.topics_discussed))
            parts.append(f"Topicos discutidos: {', '.join(unique_topics)}")

        parts.append(f"Mensagens trocadas: {self.message_count}")

        return " | ".join(parts) if parts else "Conversa recem-iniciada."

    def set_user_info(self, key: str, value: str):
        """Armazena uma informacao sobre o usuario."""
        self.load_from_db()
        self.user_info[key] = value
        save_user_info(self.session_id, key, value)

    def get_user_info(self, key: str) -> str | None:
        """Recupera uma informacao sobre o usuario."""
        self.load_from_db()
        return self.user_info.get(key)

    def add_topic(self, topic: str):
        """Registra um topico discutido."""
        if topic not in self.topics_discussed:
            self.topics_discussed.append(topic)

    def has_discussed(self, topic: str) -> bool:
        """Verifica se um topico ja foi discutido."""
        return topic in self.topics_discussed

    def get_last_user_message(self) -> str | None:
        """Retorna a ultima mensagem do usuario."""
        self.load_from_db()
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg["content"]
        return None

    def clear(self):
        """Limpa a memoria local (nao apaga do DB)."""
        self.messages = []
        self.user_info = {}
        self.topics_discussed = []
        self.message_count = 0
        self._loaded = False


# =========================
# GERENCIADOR GLOBAL DE MEMORIAS
# =========================

_active_memories: dict[str, ConversationMemory] = {}


def get_memory(session_id: str = "default") -> ConversationMemory:
    """Retorna ou cria a memoria de uma sessao."""
    if session_id not in _active_memories:
        # Garantir que a conversa existe no DB
        create_conversation(session_id)
        _active_memories[session_id] = ConversationMemory(session_id)
    return _active_memories[session_id]


def clear_memory(session_id: str = "default"):
    """Limpa a memoria de uma sessao."""
    if session_id in _active_memories:
        _active_memories[session_id].clear()
        del _active_memories[session_id]


def get_active_sessions() -> list[str]:
    """Retorna IDs das sessoes ativas."""
    return list(_active_memories.keys())