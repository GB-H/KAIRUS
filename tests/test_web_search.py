"""
FASE 4.2 - Web search multi-fonte com fallback (ddgs).
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
    """Fonte 1 (ddgs/DuckDuckGo) funciona."""
    class FakeDDGS:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def text(self, query, max_results=4):
            return [
                {"title": "Teste 1", "body": "Corpo do teste 1", "href": "https://ex1.com"},
            ]

    monkeypatch.setitem(
        __import__("sys").modules,
        "ddgs",
        type("M", (), {"DDGS": FakeDDGS})(),
    )

    result = execute_tool("web_search", "pesquise sobre python")
    assert result is not None
    assert "Teste 1" in result


def test_fallback_hackernews(monkeypatch):
    """DuckDuckGo falha -> cai no Hacker News."""
    monkeypatch.setattr(tools_mod, "_search_duckduckgo", lambda q: None)
    monkeypatch.setattr(
        tools_mod,
        "_search_hackernews",
        lambda q: [{"title": "HN noticia", "body": "10 points", "href": "https://hn.com"}],
    )

    result = execute_tool("web_search", "pesquise sobre python")
    assert result is not None
    assert "HN noticia" in result
    assert "Hacker News" in result


def test_fallback_wikipedia(monkeypatch):
    """DDG e HN falham -> cai na Wikipedia."""
    monkeypatch.setattr(tools_mod, "_search_duckduckgo", lambda q: None)
    monkeypatch.setattr(tools_mod, "_search_hackernews", lambda q: None)
    monkeypatch.setattr(
        tools_mod,
        "_search_wikipedia",
        lambda q: [{"title": "Python", "body": "Linguagem de programacao", "href": "https://pt.wikipedia.org/wiki/Python"}],
    )

    result = execute_tool("web_search", "pesquise sobre python")
    assert result is not None
    assert "Wikipedia" in result


def test_todas_fontes_falham(monkeypatch):
    """Todas as fontes falham -> None (fluxo continua sem a tool)."""
    monkeypatch.setattr(tools_mod, "_search_duckduckgo", lambda q: None)
    monkeypatch.setattr(tools_mod, "_search_hackernews", lambda q: None)
    monkeypatch.setattr(tools_mod, "_search_wikipedia", lambda q: None)

    assert execute_tool("web_search", "pesquise sobre IA") is None