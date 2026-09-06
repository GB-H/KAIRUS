"""
KAIRUS FASE 3 - Memoria de longo prazo (por usuario).
Persiste fatos que o usuario compartilhou, entre conversas.
FASE 3.2: comandos "lembre que..." e "o que voce lembra de mim?".
"""

from backend.database.db import (
    set_longterm_memory,
    get_longterm_memory,
    delete_longterm_memory,
)


REMEMBER_PREFIXES = (
    "lembre que", "lembra que", "guarde que", "anote que",
)

RECALL_TRIGGERS = (
    "o que voce lembra de mim",
    "o que voce lembra sobre mim",
    "o que voce sabe sobre mim",
)


def remember(user_id: int, key: str, value: str):
    """Salva um fato do usuario (idempotente)."""
    set_longterm_memory(user_id, key, str(value))


def recall(user_id: int) -> dict:
    """Recupera todos os fatos do usuario. Nunca lanca excecao."""
    try:
        return get_longterm_memory(user_id)
    except Exception:
        return {}


def forget(user_id: int, key: str):
    """Esquece um fato do usuario."""
    try:
        delete_longterm_memory(user_id, key)
    except Exception:
        pass


# =========================
# FATOS (lista)
# =========================

def get_facts(user_id: int) -> list:
    """Lista de fatos livres do usuario."""
    raw = recall(user_id).get("facts", "")
    return [f for f in raw.split("\n") if f]


def add_fact(user_id: int, fact: str):
    """Adiciona um fato livre (sem duplicar)."""
    facts = get_facts(user_id)
    if fact not in facts:
        facts.append(fact)
    remember(user_id, "facts", "\n".join(facts))


# =========================
# COMANDOS DE MEMORIA (FASE 3.2)
# =========================

def build_recall_text(user_id: int) -> str:
    """Monta a resposta de 'o que voce lembra de mim?'."""
    data = recall(user_id)
    parts = []

    if data.get("name"):
        parts.append(f"Seu nome e {data['name']}.")

    facts = get_facts(user_id)
    if facts:
        parts.append("Eu lembro que:")
        for f in facts:
            parts.append(f"- {f}")

    if not parts:
        return (
            "Ainda nao tenho memorias sobre voce. "
            "Me conte algo, por exemplo: "
            "'lembre que eu gosto de python'."
        )

    return "\n".join(parts)


def handle_memory_command(message: str, user_id) -> str | None:
    """Detecta e executa comandos de memoria.

    Retorna a resposta pronta, ou None se nao for comando de memoria.
    """
    if user_id is None:
        return None

    m = message.lower().strip()

    for prefix in REMEMBER_PREFIXES:
        if m.startswith(prefix):
            fact = message[len(prefix):].strip()
            if fact:
                try:
                    add_fact(user_id, fact)
                except Exception:
                    return "Nao consegui salvar isso na minha memoria agora."
                return f"Anotado! Vou lembrar que {fact}."
            return "O que voce quer que eu lembre?"

    if any(t in m for t in RECALL_TRIGGERS):
        return build_recall_text(user_id)

    return None