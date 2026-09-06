"""
KAIRUS FASE 3 - Memoria de longo prazo (por usuario).
Persiste fatos que o usuario compartilhou, entre conversas.
"""

from backend.database.db import (
    set_longterm_memory,
    get_longterm_memory,
    delete_longterm_memory,
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