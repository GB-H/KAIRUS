"""
Sistema de ferramentas do KAIRUS.
Permite que o KAIRUS execute acoes alem de apenas conversar.
Cada ferramenta e um plugin independente.
"""

import re
import math
from datetime import datetime


# =========================
# REGISTRO DE FERRAMENTAS
# =========================

_tools: dict[str, dict] = {}


def register_tool(name: str, description: str, keywords: list[str]):
    """Decorator para registrar uma ferramenta."""
    def decorator(func):
        _tools[name] = {
            "func": func,
            "description": description,
            "keywords": keywords,
        }
        return func
    return decorator


def get_available_tools() -> list[dict]:
    """Retorna lista de ferramentas disponiveis."""
    return [
        {"name": name, "description": info["description"]}
        for name, info in _tools.items()
    ]


def detect_tool(message: str) -> str | None:
    """Detecta se a mensagem ativa alguma ferramenta."""
    lower_msg = message.lower().strip()

    for name, info in _tools.items():
        for keyword in info["keywords"]:
            if keyword in lower_msg:
                return name

    return None


def execute_tool(name: str, message: str) -> str | None:
    """Executa uma ferramenta e retorna o resultado."""
    if name not in _tools:
        return None

    try:
        result = _tools[name]["func"](message)
        return result
    except Exception as e:
        return f"Erro ao executar ferramenta: {str(e)}"


# =========================
# FERRAMENTA: HORA/DATA
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
        return f"Hoje e {dia_semana}-feira, {now.strftime('%d/%m/%Y')}." if now.weekday() < 4 else f"Hoje e {dia_semana}, {now.strftime('%d/%m/%Y')}."

    return f"Data e hora atuais: {now.strftime('%d/%m/%Y %H:%M')}."


# =========================
# FERRAMENTA: CALCULADORA
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
    lower_msg = message.lower().strip()

    # Extrair expressao matematica
    # Remove texto antes do numero
    match = re.search(r'([\d\s\+\-\*\/\.\(\)\^]+)', lower_msg)

    if not match:
        return "Nao encontrei uma expressao matematica. Tente algo como 'quanto e 2 + 2'."

    expr = match.group(1).strip()

    # Substituir ^ por **
    expr = expr.replace("^", "**")

    # Seguranca: permitir apenas numeros e operadores
    if not re.match(r'^[\d\s\+\-\*\/\.\(\)\*]+$', expr):
        return "Expressao invalida. Use apenas numeros e operadores (+, -, *, /)."

    try:
        # Limitar tamanho da expressao
        if len(expr) > 50:
            return "Expressao muito longa. Mantenha simples."

        result = eval(expr, {"__builtins__": {}}, {})

        # Formatar resultado
        if isinstance(result, float) and result == int(result):
            result = int(result)

        return f"O resultado e {result}."

    except ZeroDivisionError:
        return "Divisao por zero! Isso nao e possivel."
    except Exception:
        return "Nao consegui calcular isso. Tente uma expressao mais simples."


# =========================
# FERRAMENTA: CONTADOR DE TEXTO
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

    # Extrair o texto entre aspas se existir
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
# FERRAMENTA: LISTAR FERRAMENTAS
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