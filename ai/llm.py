"""
Cliente LLM do KAIRUS.
Conecta ao OpenRouter (compativel com OpenAI).
Failover automatico entre modelos gratuitos.
"""

import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1"

# Modelos com failover automatico (se um falhar, tenta o proximo)
MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "z-ai/glm-5.2:free",
    "poolside/laguna-s-2.1:free",
    "liquid/lfm-2.5-2.6b:free",
]

STREAM_SAFE_MODELS = MODELS

DEFAULT_MODEL = MODELS[0]

_client: OpenAI | None = None


def get_client() -> OpenAI | None:
    global _client

    if not API_KEY:
        return None

    if _client is None:
        _client = OpenAI(
            base_url=BASE_URL,
            api_key=API_KEY,
            default_headers={
                "HTTP-Referer": "https://kairus.local",
                "X-Title": "KAIRUS AI",
            }
        )

    return _client


def is_available() -> bool:
    return bool(API_KEY)


SYSTEM_PROMPT = """Voce e o KAIRUS, um sistema de inteligencia artificial construido do zero com Python e FastAPI por Gabriel.

REGRAS OBRIGATORIAS:
- Responda SEMPRE e APENAS em portugues brasileiro
- NUNCA responda em ingles
- Seja direto, honesto e conciso
- Maximo 3-4 frases por resposta, a menos que o usuario peca detalhes
- Se nao souber algo, diga honestamente
- Voce esta na versao 0.4.0
- Nao mencione OpenRouter, API externa, ou que usa modelos de terceiros
- Voce E o KAIRUS, ponto final

FORMATO DE RESPOSTA (OBRIGATORIO, SEMPRE):
- Se precisar raciocinar, coloque um raciocinio CURTO (maximo 2 frases) dentro de <thinking>...</thinking>
- Coloque APENAS a resposta final dentro de <answer>...</answer>
- O conteudo de <answer> deve ser curto, direto e sem markdown
- Sempre feche as tags antes de terminar"""


def _build_messages(message: str, history: list[dict] | None) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for msg in history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})
    return messages


EN_MARKERS = [
    'okay', 'wait', 'let me', 'i should', 'i need', 'check if',
    'make sure', 'so, response', 'the user', 'also,', 'but i',
    'user asks', 'language:', 'topic:', 'formulate', 'actually,',
    'i think', "i'll", 'means', 'misspelling', 'slang', 'donkey',
    'black holes', 'however', 'therefore', 'in portuguese',
    'first, i', 'sentence', 'draft',
]

PT_REASONING_MARKERS = [
    'primeiro,', 'preciso de ter', 'preciso ter', 'deixe-me', 'deixe me',
    'vou verificar', 'verifique se', 'aguarde,', 'o usuário disse',
    'o usuario disse', 'usuário:', 'usuario:', 'assistente:', 'utilizador:',
    'olhando para', 'então eles disseram', 'eu dava uma', 'traçar:',
    'contagem de sentenças', 'mantenho-o', 'atenho ao',
    'mas como pediram', 'evite mencionar', 'disseram "',
]

PT_WORDS = [
    'é', 'ê', 'ã', 'õ', 'ç', 'á', 'à', 'â', 'í', 'ó', 'ô', 'ú',
    'voce', 'você', 'nao', 'não', 'que', 'como', 'para', 'com',
    'uma', 'este', 'esta', 'sao', 'por', 'mais', 'muito', 'tambem',
    'quando', 'onde', 'quem', 'qual', 'seu', 'sua', 'meu', 'minha',
]


def clean_response(text: str) -> str:
    """Remove raciocinio interno (fallback quando nao ha tags)."""
    if not text:
        return ""

    lines = text.strip().split('\n')
    portuguese_lines = []
    found_portuguese = False

    for line in lines:
        s = line.strip()
        if not s:
            continue

        if s.startswith(('-', '*', '•')) or re.match(r'^\d+[\.\)]', s):
            continue

        lower = s.lower()

        if any(m in lower for m in EN_MARKERS):
            continue

        if any(m in lower for m in PT_REASONING_MARKERS):
            continue

        has_pt = any(w in lower for w in PT_WORDS)

        if has_pt:
            found_portuguese = True
            portuguese_lines.append(s)
        elif found_portuguese:
            portuguese_lines.append(s)

    if portuguese_lines:
        result = '\n'.join(portuguese_lines).strip()
        result = result.strip('"').strip('"').strip('"').strip()
        return result

    return text.strip()


def extract_final_answer(text: str) -> str:
    """Extrai a resposta final, removendo todo o raciocinio interno."""
    if not text:
        return ""

    # 1. Resposta dentro de <answer>...</answer>
    m = re.search(r"<answer>(.*?)(</answer>|$)", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        result = m.group(1).strip().strip('"').strip('"').strip('"').strip()
        if result and not result.startswith("<"):
            return result

    # 2. Tudo que vem depois de </thinking>
    m = re.search(r"</thinking>(.*)$", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        result = m.group(1).strip()
        # Remove tags soltas que sobrarem
        result = re.sub(r"</?thinking>", "", result, flags=re.IGNORECASE)
        result = re.sub(r"</?answer>", "", result, flags=re.IGNORECASE)
        result = result.strip().strip('"').strip('"').strip('"').strip()
        if result and not result.startswith("<"):
            return result

    # 3. Fallback: heuristica de limpeza
    return clean_response(text)


def _is_valid_answer(text: str) -> bool:
    """Verifica se a resposta extraida e utilizavel."""
    if not text:
        return False
    t = text.strip()
    if t.startswith("<"):
        return False
    if len(t) < 10:
        return False
    return True


def generate_llm_response(
    message: str,
    history: list[dict] | None = None,
    model: str | None = None,
) -> str | None:
    client = get_client()

    if not client:
        return None

    models_to_try = [model] if model else MODELS
    messages = _build_messages(message, history)

    last_attempt = None

    for m in models_to_try:
        try:
            response = client.chat.completions.create(
                model=m,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
            )

            raw_text = response.choices[0].message.content.strip()
            cleaned = extract_final_answer(raw_text)

            if _is_valid_answer(cleaned):
                return cleaned

            last_attempt = cleaned if cleaned else raw_text

        except Exception as e:
            print(f"[KAIRUS LLM] {m} falhou: {e}")
            continue

    return last_attempt


def stream_llm_response(
    message: str,
    history: list[dict] | None = None,
    model: str | None = None,
):
    """
    Gera a resposta com failover, extrai apenas a resposta final
    e entrega em pequenos pedacos (efeito de digitacao).
    """
    client = get_client()

    if not client:
        return

    models_to_try = [model] if model else STREAM_SAFE_MODELS
    messages = _build_messages(message, history)

    final_text = None

    for m in models_to_try:
        try:
            response = client.chat.completions.create(
                model=m,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
            )

            raw_text = response.choices[0].message.content.strip()
            cleaned = extract_final_answer(raw_text)

            if _is_valid_answer(cleaned):
                final_text = cleaned
                break

        except Exception as e:
            print(f"[KAIRUS LLM Stream] {m} falhou: {e}")
            continue

    if not final_text:
        return

    # Entrega em pedacos de ate 3 palavras (efeito de digitacao)
    parts = final_text.split(" ")
    buf = []

    for i, word in enumerate(parts):
        buf.append(word)
        if len(buf) >= 3:
            yield " ".join(buf) + (" " if i < len(parts) - 1 else "")
            buf = []

    if buf:
        yield " ".join(buf)


def get_model_name() -> str:
    return DEFAULT_MODEL