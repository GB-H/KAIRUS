"""
FASE 2.3 - Eventos SSE do pipeline multi-agente.
"""
import ai.engine as engine


def _fake_steps():
    return [
        {"agent": "security", "status": "ok"},
        {"agent": "planner", "status": "ok"},
        {"agent": "writer", "status": "ok"},
        {"agent": "reviewer", "status": "ok"},
    ]


def test_stream_emite_evento_agents(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_ENABLED", "on")
    monkeypatch.setattr(engine, "is_available", lambda: True)
    monkeypatch.setattr(
        engine, "classify", lambda msg: engine.INTENT_UNKNOWN
    )
    monkeypatch.setattr(
        engine,
        "_run_orchestrator_safe",
        lambda msg: ("Resposta do pipeline.", _fake_steps()),
    )

    events = list(engine.stream_response(
        "escreva um texto detalhado sobre a historia da computacao",
        session_id="test_pipe_1",
    ))

    agent_events = [e for e in events if e["type"] == "agents"]
    assert len(agent_events) == 1
    assert agent_events[0]["steps"][0]["agent"] == "security"

    done = [e for e in events if e["type"] == "done"][0]
    assert done["llm"] is True
    assert done["response"] == "Resposta do pipeline."


def test_stream_sem_flag_nao_emite_agents(monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_ENABLED", raising=False)
    monkeypatch.setattr(engine, "is_available", lambda: True)
    monkeypatch.setattr(
        engine, "classify", lambda msg: engine.INTENT_UNKNOWN
    )
    monkeypatch.setattr(
        engine,
        "stream_llm_response",
        lambda *a, **k: iter(["token"]),
    )

    events = list(engine.stream_response(
        "escreva um texto detalhado sobre a historia da computacao",
        session_id="test_pipe_2",
    ))

    agent_events = [e for e in events if e["type"] == "agents"]
    assert len(agent_events) == 0
