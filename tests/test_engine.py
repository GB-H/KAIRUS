"""
Testes para ai/engine.py - motor de IA completo.
Sessoes unicas por execucao (RUN_ID) para nao depender do
historico acumulado no banco local.
"""

import uuid

import pytest
from ai.engine import generate_response
from ai.memory import clear_memory


RUN_ID = uuid.uuid4().hex[:8]


def sid(name: str) -> str:
    """Gera um session_id unico por execucao de pytest."""
    return f"{name}_{RUN_ID}"


@pytest.fixture(autouse=True)
def setup():
    """Limpa memoria antes de cada teste."""
    yield
    from ai.memory import _active_memories
    _active_memories.clear()


class TestBasicResponses:

    def test_greeting(self):
        result = generate_response("oi", sid("test_eng_1"))
        assert result["intent"] == "greeting"
        assert len(result["response"]) > 0

    def test_goodbye(self):
        result = generate_response("tchau", sid("test_eng_2"))
        assert result["intent"] == "goodbye"

    def test_thanks(self):
        result = generate_response("obrigado", sid("test_eng_3"))
        assert result["intent"] == "thanks"

    def test_identity(self):
        result = generate_response("quem e voce?", sid("test_eng_4"))
        assert result["intent"] == "identity"
        assert "KAIRUS" in result["response"]

    def test_help(self):
        result = generate_response("me ajude", sid("test_eng_5"))
        assert result["intent"] == "help"

    def test_status(self):
        result = generate_response("status", sid("test_eng_6"))
        assert result["intent"] == "status"

    def test_joke(self):
        result = generate_response("conta uma piada", sid("test_eng_7"))
        assert result["intent"] == "joke"

    def test_unknown(self):
        result = generate_response("qual a capital da Franca?", sid("test_eng_8"))
        assert result["intent"] == "unknown"

    def test_empty_message(self):
        result = generate_response("", sid("test_eng_9"))
        assert result["intent"] == "empty"


class TestMemoryIntegration:

    def test_name_remembered(self):
        session = sid("test_eng_mem_1")
        result1 = generate_response("meu nome e Gabriel", session)
        assert result1["intent"] == "name_tell"
        assert "Gabriel" in result1["response"]

        result2 = generate_response("qual meu nome?", session)
        assert result2["intent"] == "name_ask"
        assert "Gabriel" in result2["response"]

    def test_name_unknown_without_telling(self):
        session = sid("test_eng_mem_2")
        result = generate_response("qual meu nome?", session)
        assert result["intent"] == "name_ask"
        assert "Gabriel" not in result["response"]

    def test_repetition_detected(self):
        session = sid("test_eng_mem_3")
        generate_response("oi", session)
        result = generate_response("oi", session)
        assert "ja" in result["response"].lower() or "repetiu" in result["response"].lower() or "ouvi" in result["response"].lower()

    def test_message_count(self):
        session = sid("test_eng_mem_4")
        generate_response("oi", session)
        generate_response("tchau", session)
        result = generate_response("quantas mensagens?", session)
        assert result["intent"] == "count"

    def test_context_summary(self):
        session = sid("test_eng_mem_5")
        generate_response("meu nome e Test", session)
        result = generate_response("resumo", session)
        assert result["intent"] == "context"


class TestResponseFormat:

    def test_has_response(self):
        result = generate_response("oi", sid("test_eng_fmt_1"))
        assert "response" in result

    def test_has_intent(self):
        result = generate_response("oi", sid("test_eng_fmt_2"))
        assert "intent" in result

    def test_has_model(self):
        result = generate_response("oi", sid("test_eng_fmt_3"))
        assert "model" in result
        assert "KAIRUS" in result["model"]

    def test_has_memory(self):
        result = generate_response("oi", sid("test_eng_fmt_4"))
        assert "memory" in result
        assert "message_count" in result["memory"]