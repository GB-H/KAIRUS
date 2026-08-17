"""
Sistema de ferramentas do KAIRUS.
"""

import re
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
    # Extrair todos os numeros e operadores da mensagem
    # Remove tudo que nao e numero, operador, ponto, parenteses, espaco
    cleaned = re.sub(r'[^\d\s\+\-\*\/\.\(\)\^]', ' ', message)
    cleaned = cleaned.strip()

    # Encontrar a expressao matematica (sequencia de numeros e operadores)
    match = re.search(r'([\d][\d\s\+\-\*\/\.\(\)\^]*[\d])', cleaned)

    if not match:
        # Tentar pegar qualquer numero
        numbers = re.findall(r'[\d]+\.?[\d]*', message)
        operators = re.findall(r'[\+\-\*\/\^]', message)

        if len(numbers) >= 2 and len(operators) >= 1:
            expr = numbers[0] + operators[0] + numbers[1]
        else:
            return "Nao encontrei uma expressao matematica. Tente algo como 'quanto e 2 + 2'."
    else:
        expr = match.group(1).strip()

    expr = expr.replace("^", "**")

    # Seguranca
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