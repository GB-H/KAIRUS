"""
FASE 4 - Web search real via DuckDuckGo.
"""
import ai.tools as tools_mod
from ai.tools import detect_tool, execute_tool


def test_detect_web_search():
    assert detect_tool("pesquise sobre IA") == "web_search"
    assert detect_tool("pesquise sobre buraco negro") == "web_search"
    assert detect_tool("ultimas noticias sobre python") == "web_search"
    assert detect_tool("oi tudo bem") is None


def test_extract_query():
    from ai.tools import _extract_search_query

    assert _extract_search_query("pesquise sobre IA") == "IA"
    assert _extract_search_query("pesquise sobre buraco negro") == "buraco negro"
    assert _extract_search_query("pesquise as ultimas noticias") == "ultimas noticias"


def test_web_search_executa(monkeypatch):
    """Tool de busca executa e retorna resultados."""
    class FakeDDGS:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def text(self, query, max_results=4):
            return [
                {"title": "Teste 1", "body": "Corpo do teste 1", "href": "https://ex1.com"},
                {"title": "Teste 2", "body": "Corpo do teste 2", "href": "https://ex2.com"},
            ]

    monkeypatch.setitem(
        __import__("sys").modules,
        "duckduckgo_search",
        type("M", (), {"DDGS": FakeDDGS})(),
    )

    result = execute_tool("web_search", "pesquise sobre python")
    assert result is not None
    assert "python" in result.lower()
    assert "Teste 1" in result


def test_web_search_falha_sem_quebrar(monkeypatch):
    """Se a busca falhar, retorna None e o orchestrator continua."""
    class FakeDDGS:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def text(self, query, max_results=4):
            raise RuntimeError("falha de rede")

    monkeypatch.setitem(
        __import__("sys").modules,
        "duckduckgo_search",
        type("M", (), {"DDGS": FakeDDGS})(),
    )

    result = execute_tool("web_search", "pesquise sobre IA")
    assert result is None