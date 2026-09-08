"""
Sistema de ferramentas do KAIRUS.
FASE 4.2: web search multi-fonte com fallback
(ddgs/DuckDuckGo -> Hacker News -> Wikipedia).
"""

import re
import json
import urllib.request
import urllib.parse
from datetime import datetime


_tools: dict[str, dict] = {}


def register_tool(name: str, description: str, keywords: list[str]):
    def decorator(func):
        _tools[name] = {
            "func": func,
            "description": description,
            "keywords": keywords,
        }
        return func
    return decorator


def get_available_tools() -> list[dict]:
    return [
        {"name": name, "description": info["description"]}
        for name, info in _tools.items()
    ]


def detect_tool(message: str) -> str | None:
    lower_msg = message.lower().strip()
    for name, info in _tools.items():
        for keyword in info["keywords"]:
            if keyword in lower_msg:
                return name
    return None


def execute_tool(name: str, message: str) -> str | None:
    if name not in _tools:
        return None
    try:
        result = _tools[name]["func"](message)
        return result
    except Exception as e:
        return f"Erro ao executar ferramenta: {str(e)}"


# =========================
# HORA/DATA
# =========================

@register_tool(
    name="datetime",
    description="Mostra a data e hora atuais",
    keywords=[
        "que horas", "hora certa", "horario",
        "data de hoje", "que dia", "data atual",
        "hoje e", "hoje eh",
    ]
)
def tool_datetime(message: str) -> str:
    now = datetime.now()
    lower_msg = message.lower()

    if any(w in lower_msg for w in ["hora", "horario"]):
        return f"Agora sao {now.strftime('%H:%M')} do dia {now.strftime('%d/%m/%Y')}."

    if any(w in lower_msg for w in ["data", "dia", "hoje"]):
        dias = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
        dia_semana = dias[now.weekday()]
        if now.weekday() < 4:
            return f"Hoje e {dia_semana}-feira, {now.strftime('%d/%m/%Y')}."
        elif now.weekday() == 4:
            return f"Hoje e sexta-feira, {now.strftime('%d/%m/%Y')}."
        elif now.weekday() == 5:
            return f"Hoje e sabado, {now.strftime('%d/%m/%Y')}."
        else:
            return f"Hoje e domingo, {now.strftime('%d/%m/%Y')}."

    return f"Data e hora atuais: {now.strftime('%d/%m/%Y %H:%M')}."


# =========================
# CALCULADORA
# =========================

@register_tool(
    name="calculator",
    description="Faz calculos matematicos basicos",
    keywords=[
        "quanto e", "quanto eh", "calcula",
        "matematica", "soma", "subtrai",
        "multiplica", "divide", "raiz",
        "potencia",
    ]
)
def tool_calculator(message: str) -> str:
    cleaned = re.sub(r'[^\d\s\+\-\*\/\.\(\)\^]', ' ', message)
    cleaned = cleaned.strip()

    match = re.search(r'([\d][\d\s\+\-\*\/\.\(\)\^]*[\d])', cleaned)

    if not match:
        numbers = re.findall(r'[\d]+\.?[\d]*', message)
        operators = re.findall(r'[\+\-\*\/\^]', message)

        if len(numbers) >= 2 and len(operators) >= 1:
            expr = numbers[0] + operators[0] + numbers[1]
        else:
            return "Nao encontrei uma expressao matematica. Tente algo como 'quanto e 2 + 2'."
    else:
        expr = match.group(1).strip()

    expr = expr.replace("^", "**")

    if not re.match(r'^[\d\s\+\-\*\/\.\(\)]+$', expr.replace('**', '')):
        return "Expressao invalida. Use apenas numeros e operadores (+, -, *, /)."

    try:
        if len(expr) > 50:
            return "Expressao muito longa. Mantenha simples."

        result = eval(expr, {"__builtins__": {}}, {})

        if isinstance(result, float) and result == int(result):
            result = int(result)

        return f"O resultado e {result}."

    except ZeroDivisionError:
        return "Divisao por zero! Isso nao e possivel."
    except Exception:
        return "Nao consegui calcular isso. Tente uma expressao mais simples."


# =========================
# CONTADOR DE TEXTO
# =========================

@register_tool(
    name="text_counter",
    description="Conta caracteres, palavras ou linhas de um texto",
    keywords=[
        "conta caracteres", "conta palavras",
        "quantas palavras", "quantos caracteres",
        "tamanho do texto",
    ]
)
def tool_text_counter(message: str) -> str:
    lower_msg = message.lower()

    quoted = re.search(r'["\'](.+?)["\']', message)
    text = quoted.group(1) if quoted else message

    chars = len(text)
    words = len(text.split())
    lines = text.count('\n') + 1

    if "caracter" in lower_msg:
        return f"O texto tem {chars} caracteres."

    if "palavra" in lower_msg:
        return f"O texto tem {words} palavras."

    return f"Texto analisado: {chars} caracteres, {words} palavras, {lines} linha(s)."


# =========================
# LISTAR FERRAMENTAS
# =========================

@register_tool(
    name="list_tools",
    description="Lista todas as ferramentas disponiveis",
    keywords=[
        "quais ferramentas", "o que voce consegue fazer",
        "suas ferramentas", "lista de ferramentas",
        "quais funcoes",
    ]
)
def tool_list_tools(message: str) -> str:
    tools = get_available_tools()
    lines = ["Minhas ferramentas atuais:"]
    for t in tools:
        lines.append(f"  - {t['name']}: {t['description']}")
    return "\n".join(lines)


# =========================
# WEB SEARCH (FASE 4.2)
# =========================

@register_tool(
    name="web_search",
    description="Pesquisa na internet (DuckDuckGo, Hacker News, Wikipedia)",
    keywords=[
        "pesquise", "pesquisar", "procure", "buscar",
        "busca na internet", "web search", "google",
        "ultimas noticias", "novidades sobre",
        "informacoes sobre",
    ]
)
def tool_web_search(message: str) -> str:
    """Busca na internet com fallback entre 3 fontes gratuitas.

    DuckDuckGo (ddgs) -> Hacker News -> Wikipedia.
    Se todas falharem, retorna None (o fluxo continua sem a tool).
    """
    query = _extract_search_query(message)
    if not query:
        return None

    results = _search_duckduckgo(query)
    source = "DuckDuckGo"

    if not results:
        results = _search_hackernews(query)
        source = "Hacker News"

    if not results:
        results = _search_wikipedia(query)
        source = "Wikipedia"

    if not results:
        return None

    lines = [f"Resultados da pesquisa sobre '{query}' (fonte: {source}):"]
    for r in results:
        title = r.get("title", "Sem titulo")
        body = (r.get("body") or "").strip()
        href = r.get("href", "")
        lines.append(f"- {title}")
        if body:
            lines.append(f"  {body}")
        if href:
            lines.append(f"  ({href})")

    return "\n".join(lines)


def _search_duckduckgo(query: str):
    """Fonte 1: DuckDuckGo via pacote ddgs."""
    try:
        from ddgs import DDGS
    except ImportError:
        return None

    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=4)) or None
    except Exception:
        return None


def _search_hackernews(query: str):
    """Fonte 2: Hacker News via Algolia (funciona em qualquer IP)."""
    try:
        url = (
            "https://hn.algolia.com/api/v1/search?query="
            + urllib.parse.quote(query)
            + "&hitsPerPage=4"
        )
        req = urllib.request.Request(
            url, headers={"User-Agent": "KAIRUS/0.6"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        out = []
        for hit in data.get("hits", []):
            title = hit.get("title") or hit.get("story_title") or ""
            if not title:
                continue
            href = hit.get("url") or (
                "https://news.ycombinator.com/item?id="
                + str(hit.get("objectID"))
            )
            body = f"{hit.get('points', 0)} points | autor: {hit.get('author', '?')}"
            out.append({"title": title, "body": body, "href": href})
        return out or None
    except Exception:
        return None


def _search_wikipedia(query: str):
    """Fonte 3: Wikipedia pt (API oficial, sem key)."""
    try:
        url = (
            "https://pt.wikipedia.org/w/api.php"
            "?action=query&list=search&format=json&srslimit=3&srsearch="
            + urllib.parse.quote(query)
        )
        req = urllib.request.Request(
            url, headers={"User-Agent": "KAIRUS/0.6"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        out = []
        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
            href = "https://pt.wikipedia.org/wiki/" + urllib.parse.quote(
                title.replace(" ", "_")
            )
            out.append({"title": title, "body": snippet, "href": href})
        return out or None
    except Exception:
        return None


def _extract_search_query(message: str) -> str:
    """Extrai o termo de busca da mensagem."""
    m = message.lower().strip()

    prefixes = [
        "pesquise sobre", "pesquise as", "pesquise",
        "procure sobre", "procure",
        "buscar sobre", "buscar", "busca na internet sobre",
        "busca na internet", "web search sobre", "web search",
        "ultimas noticias sobre", "novidades sobre",
        "informacoes sobre",
    ]

    for p in prefixes:
        if m.startswith(p):
            term = message[len(p):].strip()
            if term:
                return term

    if len(message) < 80:
        return message.strip()

    return ""