"""
Cliente LLM do KAIRUS.
Conecta ao OpenRouter (compativel com OpenAI).
"""

import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1"

DEFAULT_MODEL = "google/gemma-4-26b-a4b-it:free"

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
- NUNCA inclua seu processo de pensamento ou raciocinio interno na resposta
- Seja direto, honesto e conciso
- Maximo 3-4 frases por resposta, a menos que o usuario peca detalhes
- Se nao souber algo, diga honestamente
- Voce esta na versao 0.3.0
- Nao mencione OpenRouter, API externa, ou que usa modelos de terceiros
- Voce E o KAIRUS, ponto final"""


def clean_response(text: str) -> str:
    """Remove raciocinio interno e pensamento da resposta."""
    if not text:
        return ""

    patterns = [
        r'Okay,.*?(?=\n\n|\Z)',
        r'Wait,.*?(?=\n\n|\Z)',
        r'Let me.*?(?=\n\n|\Z)',
        r'I should.*?(?=\n\n|\Z)',
        r'I need to.*?(?=\n\n|\Z)',
        r'Check if.*?(?=\n\n|\Z)',
        r'So, response:.*?(?=\n\n|\Z)',
        r'Make sure.*?(?=\n\n|\Z)',
        r'Also,.*?remember.*?(?=\n\n|\Z)',
    ]

    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

    lines = text.strip().split('\n')
    portuguese_lines = []
    found_portuguese = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        pt_words = ['é', 'ê', 'ã', 'õ', 'ç', 'á', 'à', 'â', 'í', 'ó', 'ô', 'ú',
                     'voce', 'nao', 'que', 'como', 'para', 'com', 'uma', 'este',
                     'esta', 'sao', 'por', 'mais', 'muito', 'tambem', 'quando',
                     'onde', 'quem', 'qual', 'seu', 'sua', 'meu', 'minha']

        has_pt = any(w in line.lower() for w in pt_words)
        has_en_thinking = any(w in line.lower() for w in [
            'okay', 'wait', 'let me', 'i should', 'i need', 'check if',
            'make sure', 'so, response', 'the user', 'also,', 'but i',
        ])

        if has_pt and not has_en_thinking:
            found_portuguese = True
            portuguese_lines.append(line)
        elif found_portuguese and has_pt:
            portuguese_lines.append(line)

    if portuguese_lines:
        return '\n'.join(portuguese_lines).strip()

    return text.strip()


def generate_llm_response(
    message: str,
    history: list[dict] | None = None,
    model: str | None = None,
) -> str | None:
    client = get_client()

    if not client:
        return None

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if history:
            recent = history[-10:]
            for msg in recent:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.7,
            extra_body={
                "reasoning": {"enabled": False}
            },
        )

        raw_text = response.choices[0].message.content.strip()
        cleaned = clean_response(raw_text)

        return cleaned if cleaned else raw_text

    except Exception as e:
        print(f"[KAIRUS LLM] Erro: {e}")
        return None


def get_model_name() -> str:
    return DEFAULT_MODEL