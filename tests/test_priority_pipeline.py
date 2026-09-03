"""
FASE 2.4 - Pipeline prioritario para tarefas complexas.
FASE 2.5: no fallback, o evento agents chega com steps vazios
(usado pelo frontend para limpar o indicador de loading).
"""
import ai.engine as engine


def _fake_steps():
    return [
        {"agent": "security", "status": "ok"},
        {"agent": "planner", "status": "ok"},
        {"agent": "writer", "status": "ok"},
        {"agent": "reviewer", "status": "ok"},
    ]


def test_tarefa_complexa_vai_pro_pipeline(monkeypatch):
    """Mesmo que classify retorne GREETING, tarefa complexa vai pro pipeline."""
    monkeypatch.setenv("ORCHESTRATOR_ENABLED", "on")
    monkeypatch.setattr(engine, "is_available", lambda: True)
    monkeypatch.setattr(
        engine, "classify", lambda msg: engine.INTENT_GREETING
    )
    monkeypatch.setattr(
        engine,
        "_run_orchestrator_safe",
        lambda msg: ("Resposta do pipeline.", _fake_steps()),
    )

    events = list(engine.stream_response(
        "escreva um texto detalhado sobre a historia da computacao",
        session_id="test_priority_1",
    ))

    agent_events = [e for e in events if e["type"] == "agents"]
    assert len(agent_events) == 1

    done = [e for e in events if e["type"] == "done"][0]
    assert done["response"] == "Resposta do pipeline."
    assert done["llm"] is True


def test_tarefa_curta_vai_pras_regras(monkeypatch):
    """Tarefa curta vai pras regras, nao pro pipeline."""
    monkeypatch.setenv("ORCHESTRATOR_ENABLED", "on")
    monkeypatch.setattr(engine, "is_available", lambda: True)
    monkeypatch.setattr(
        engine, "classify", lambda msg: engine.INTENT_GREETING
    )

    orchestrator_called = {"called": False}

    def fake_orchestrator(msg):
        orchestrator_called["called"] = True
        return ("Pipeline.", _fake_steps())

    monkeypatch.setattr(
        engine, "_run_orchestrator_safe", fake_orchestrator
    )

    events = list(engine.stream_response(
        "oi",
        session_id="test_priority_2",
    ))

    assert orchestrator_called["called"] is False

    agent_events = [e for e in events if e["type"] == "agents"]
    assert len(agent_events) == 0

    done = [e for e in events if e["type"] == "done"][0]
    assert done["llm"] is False


def test_pipeline_falha_cai_nas_regras(monkeypatch):
    """Se o pipeline falhar, cai nas regras ou LLM simples."""
    monkeypatch.setenv("ORCHESTRATOR_ENABLED", "on")
    monkeypatch.setattr(engine, "is_available", lambda: True)
    monkeypatch.setattr(
        engine, "classify", lambda msg: engine.INTENT_UNKNOWN
    )
    monkeypatch.setattr(
        engine,
        "_run_orchestrator_safe",
        lambda msg: (None, []),
    )
    monkeypatch.setattr(
        engine,
        "stream_llm_response",
        lambda *a, **k: iter(["Resposta LLM simples."]),
    )

    events = list(engine.stream_response(
        "escreva um texto detalhado sobre a historia da computacao",
        session_id="test_priority_3",
    ))

    # FASE 2.5: o evento agents pode chegar, mas SEM steps (limpa loading)
    agent_events = [e for e in events if e["type"] == "agents"]
    for e in agent_events:
        assert e["steps"] == []

    done = [e for e in events if e["type"] == "done"][0]
    assert "Resposta LLM simples" in done["response"]