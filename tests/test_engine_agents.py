import ai.engine as engine


def test_flag_off_por_padrao(monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_ENABLED", raising=False)
    assert engine._orchestrator_enabled() is False


def test_flag_on(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_ENABLED", "on")
    assert engine._orchestrator_enabled() is True


def test_is_complex_task():
    assert engine._is_complex_task("x" * 150) is True
    assert engine._is_complex_task("escreva um texto sobre inteligencia artificial") is True
    assert engine._is_complex_task("pesquise sobre buracos negros") is True
    assert engine._is_complex_task("oi") is False