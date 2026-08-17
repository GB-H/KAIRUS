"""
Classificador de intencoes do KAIRUS.
Analisa a mensagem e retorna a intencao detectada.
"""

from ai.utils import normalize, contains_any, starts_with_any


# =========================
# DEFINICAO DE INTENCOES
# =========================

INTENT_GREETING = "greeting"
INTENT_GOODBYE = "goodbye"
INTENT_THANKS = "thanks"
INTENT_IDENTITY = "identity"
INTENT_HELP = "help"
INTENT_STATUS = "status"
INTENT_CAPABILITIES = "capabilities"
INTENT_LIMITATIONS = "limitations"
INTENT_COMPLIMENT = "compliment"
INTENT_INSULT = "insult"
INTENT_JOKE = "joke"
INTENT_UNKNOWN = "unknown"
INTENT_NAME_TELL = "name_tell"
INTENT_NAME_ASK = "name_ask"
INTENT_REPEAT = "repeat"
INTENT_CONTEXT = "context"
INTENT_COUNT = "count"
INTENT_TOOL_USE = "tool_use"


# =========================
# PALAVRAS-CHAVE POR INTENCAO
# =========================

KEYWORDS = {
    INTENT_GREETING: [
        "oi", "ola", "hey", "hello", "hi",
        "eae", "e ai", "fala", "salve",
        "bom dia", "boa tarde", "boa noite",
    ],
    INTENT_GOODBYE: [
        "tchau", "ate logo", "ate mais", "adeus",
        "bye", "flw", "falou", "vou indo",
        "ate breve", "nos vemos",
    ],
    INTENT_THANKS: [
        "obrigado", "obrigada", "valeu", "thanks",
        "agradeco", "grato", "grata", "tmj",
    ],
    INTENT_IDENTITY: [
        "quem e voce", "quem eh voce",
        "o que voce e",
        "seu nome", "como vc se chama",
        "voce e uma ia",
        "voce e um bot",
        "o que e kairus",
    ],
    INTENT_HELP: [
        "ajuda", "help", "me ajude", "pode ajudar",
        "preciso de ajuda", "socorro",
    ],
    INTENT_STATUS: [
        "status", "como vc esta",
        "ta funcionando",
        "ta online",
    ],
    INTENT_CAPABILITIES: [
        "o que vc sabe",
        "o que vc faz",
        "o que vc consegue",
        "suas habilidades", "suas funcoes",
        "pode fazer o que",
    ],
    INTENT_LIMITATIONS: [
        "o que vc nao sabe",
        "limitacoes",
        "o que vc nao consegue",
    ],
    INTENT_COMPLIMENT: [
        "legal", "massa", "incrivel",
        "muito bom", "parabens",
        "impressionante", "top", "show",
        "voce e bom",
        "voce e inteligente",
    ],
    INTENT_INSULT: [
        "burro", "idiota", "inutil",
        "lixo", "ruim", "horrivel",
        "nao serve",
    ],
    INTENT_JOKE: [
        "piada", "conta uma piada", "me faz rir",
        "algo engracado",
        "joke",
    ],
    INTENT_NAME_TELL: [
        "meu nome e", "meu nome eh", "eu sou o", "eu sou a",
        "me chamo", "pode me chamar",
    ],
    INTENT_NAME_ASK: [
        "qual meu nome", "como eu me chamo",
        "voce sabe meu nome", "vc sabe meu nome",
        "lembra meu nome", "qual e meu nome",
    ],
    INTENT_REPEAT: [
        "ja disse isso", "repeti", "de novo",
    ],
    INTENT_CONTEXT: [
        "sobre o que estamos falando", "resumo",
        "contexto", "do que estamos falando",
    ],
    INTENT_COUNT: [
        "quantas mensagens", "quantas vezes",
        "quantas perguntas",
    ],
}


# =========================
# CLASSIFICADOR
# =========================

def classify(message: str) -> str:
    """
    Classifica a intencao da mensagem do usuario.
    Retorna uma string representando a intencao.
    """
    normalized = normalize(message)

    if not normalized:
        return INTENT_UNKNOWN

    # Verificar se ativa alguma ferramenta
    from ai.tools import detect_tool
    tool_name = detect_tool(message)
    if tool_name:
        return INTENT_TOOL_USE

    # Verificacoes especiais que precisam de logica extra
    from ai.context import extract_name, extract_question_about

    if extract_name(message):
        return INTENT_NAME_TELL

    question_about = extract_question_about(message)
    if question_about == "name":
        return INTENT_NAME_ASK

    # Verifica cada intencao por palavras-chave
    for intent, keywords in KEYWORDS.items():
        if contains_any(message, keywords):
            return intent

    # Verifica padroes especificos
    if starts_with_any(message, ["oi", "ola", "hey", "eae"]):
        return INTENT_GREETING

    return INTENT_UNKNOWN