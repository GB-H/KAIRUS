"""
Analisador de contexto do KAIRUS.
Extrai informacoes das mensagens e entende o contexto da conversa.
"""

import re
from ai.utils import normalize


def extract_name(message: str) -> str | None:
    """
    Tenta extrair um nome da mensagem.
    Ex: 'meu nome e Gabriel' -> 'Gabriel'
    """
    patterns = [
        r"meu nome [eé]\s+(\w+)",
        r"eu sou\s+(\w+)",
        r"me chamo\s+(\w+)",
        r"pode me chamar de\s+(\w+)",
        r"meu nome eh\s+(\w+)",
    ]

    lower_msg = message.lower().strip()

    for pattern in patterns:
        match = re.search(pattern, lower_msg)
        if match:
            name = match.group(1).capitalize()
            skip_words = {
                "o", "a", "um", "uma", "de", "do", "da",
                "que", "nao", "sei", "direi", "falar",
            }
            if name.lower() not in skip_words:
                return name

    return None


def extract_question_about(message: str) -> str | None:
    """
    Detecta se o usuario esta perguntando sobre algo ja dito.
    Ex: 'qual meu nome?' -> 'name'
    """
    normalized = normalize(message)

    name_patterns = [
        "qual meu nome",
        "como eu me chamo",
        "voce sabe meu nome",
        "vc sabe meu nome",
        "lembra meu nome",
    ]

    for pattern in name_patterns:
        if pattern in normalized:
            return "name"

    return None


def detect_sentiment(message: str) -> str:
    """
    Detecta o sentimento geral da mensagem.
    Retorna: positive, negative, neutral
    """
    normalized = normalize(message)

    positive_words = [
        "legal", "massa", "incrivel", "otimo", "bom",
        "gostei", "parabens", "top", "show", "demais",
        "adorei", "perfeito", "excelente", "maravilhoso",
        "obrigado", "valeu", "thanks",
    ]

    negative_words = [
        "ruim", "horrivel", "lixo", "burro", "inutil",
        "odio", "pessimo", "chato", "irritante",
        "nao gostei", "nao serve",
    ]

    pos_count = sum(1 for w in positive_words if w in normalized)
    neg_count = sum(1 for w in negative_words if w in normalized)

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


def detect_repetition(current_message: str, history: list) -> bool:
    """
    Verifica se o usuario esta repetindo uma mensagem anterior.
    """
    normalized_current = normalize(current_message)

    for msg in history:
        if msg["role"] == "user":
            if normalize(msg["content"]) == normalized_current:
                return True

    return False


def get_conversation_stage(message_count: int) -> str:
    """
    Determina o estagio da conversa.
    """
    if message_count <= 1:
        return "opening"
    elif message_count <= 5:
        return "early"
    elif message_count <= 15:
        return "mid"
    else:
        return "deep"