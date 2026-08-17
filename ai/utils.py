import unicodedata
import re


def normalize(text: str) -> str:
    """
    Normaliza o texto para facilitar comparaÃ§Ã£o.
    Remove acentos, converte para minÃºsculo, limpa espaÃ§os.
    """
    if not text:
        return ""

    # Remove acentos
    normalized = unicodedata.normalize("NFD", text)
    normalized = "".join(
        char for char in normalized
        if unicodedata.category(char) != "Mn"
    )

    # MinÃºsculo e limpa espaÃ§os
    normalized = normalized.lower().strip()

    # Remove pontuaÃ§Ã£o excessiva
    normalized = re.sub(r"[^\w\s]", "", normalized)

    # Remove espaÃ§os duplicados
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def contains_any(text: str, keywords: list[str]) -> bool:
    """Verifica se o texto contÃ©m alguma das palavras-chave."""
    normalized = normalize(text)
    return any(keyword in normalized for keyword in keywords)


def starts_with_any(text: str, prefixes: list[str]) -> bool:
    """Verifica se o texto comeÃ§a com algum dos prefixos."""
    normalized = normalize(text)
    return any(normalized.startswith(prefix) for prefix in prefixes)