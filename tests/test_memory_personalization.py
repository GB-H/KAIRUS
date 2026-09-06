"""
FASE 3.4 - Memoria injetada no LLM e no pipeline.
"""
import ai.engine as engine
from backend.database.db import (
    init_db,
    set_longterm_memory,
    delete_longterm_memory,
)


init_db()


USER_E = 900005


def test_build_memory_context():
    set_longterm_memory(USER_E, "name", "Gabriel")
    set_longterm_memory(USER_E, "facts", "gosta de python")

    ctx = engine._build_memory_context(USER_E, None)

    assert "Nome do usuario: Gabriel" in ctx
    assert "gosta de python" in ctx

    delete_longterm_memory(USER_E, "name")
    delete_longterm_memory(USER_E, "facts")


def test_llm_recebe_memoria_no_prompt(monkeypatch):
    set_longterm_memory(USER_E, "name", "Gabriel")
    captured = {}

    monkeypatch.setattr(engine, "is_available", lambda: True)
    monkeypatch.setattr(
        engine, "classify", lambda m: engine.INTENT_UNKNOWN
    )

    def fake_llm(message, history):
        captured["message"] = message
        return "resposta ok"

    monkeypatch.setattr(engine, "generate_llm_response", fake_llm)

    engine.generate_response(
        "qual a melhor linguagem de programacao",
        session_id="mp_1",
        user_id=USER_E,
    )

    assert "Nome do usuario: Gabriel" in captured["message"]

    delete_longterm_memory(USER_E, "name")