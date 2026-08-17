"""
KAIRUS AI Engine — Orquestrador principal.
Modelo hibrido: regras para intencoes conhecidas + LLM para o resto.
"""

from ai.intents import classify
from ai.intents import (
    INTENT_GREETING,
    INTENT_GOODBYE,
    INTENT_THANKS,
    INTENT_IDENTITY,
    INTENT_HELP,
    INTENT_STATUS,
    INTENT_CAPABILITIES,
    INTENT_LIMITATIONS,
    INTENT_COMPLIMENT,
    INTENT_INSULT,
    INTENT_JOKE,
    INTENT_UNKNOWN,
    INTENT_NAME_TELL,
    INTENT_NAME_ASK,
    INTENT_REPEAT,
    INTENT_CONTEXT,
    INTENT_COUNT,
    INTENT_TOOL_USE,
)
from ai.responses import (
    GREETINGS,
    GOODBYES,
    THANKS,
    IDENTITY,
    HELP,
    STATUS,
    CAPABILITIES_RESPONSE,
    LIMITATIONS_RESPONSE,
    COMPLIMENT,
    INSULT,
    JOKE,
    UNKNOWN,
    NAME_TELL,
    NAME_ASK_KNOWN,
    NAME_ASK_UNKNOWN,
    REPEAT_DETECTED,
    CONTEXT_SUMMARY,
    MESSAGE_COUNT,
    CONVERSATION_OPENING,
    pick,
)
from ai.memory import get_memory
from ai.context import (
    extract_name,
    detect_sentiment,
    detect_repetition,
    get_conversation_stage,
)
from ai.tools import detect_tool, execute_tool
from ai.llm import generate_llm_response, is_available, get_model_name
from ai.personality import NAME, VERSION
import random


# Intencoes que usam regras (rapido, gratis, previsivel)
RULE_INTENTS = {
    INTENT_GREETING,
    INTENT_GOODBYE,
    INTENT_THANKS,
    INTENT_IDENTITY,
    INTENT_HELP,
    INTENT_STATUS,
    INTENT_CAPABILITIES,
    INTENT_LIMITATIONS,
    INTENT_COMPLIMENT,
    INTENT_INSULT,
    INTENT_JOKE,
    INTENT_NAME_TELL,
    INTENT_NAME_ASK,
    INTENT_REPEAT,
    INTENT_CONTEXT,
    INTENT_COUNT,
    INTENT_TOOL_USE,
}


INTENT_RESPONSE_MAP = {
    INTENT_GREETING: GREETINGS,
    INTENT_GOODBYE: GOODBYES,
    INTENT_THANKS: THANKS,
    INTENT_IDENTITY: IDENTITY,
    INTENT_HELP: HELP,
    INTENT_STATUS: STATUS,
    INTENT_CAPABILITIES: CAPABILITIES_RESPONSE,
    INTENT_LIMITATIONS: LIMITATIONS_RESPONSE,
    INTENT_COMPLIMENT: COMPLIMENT,
    INTENT_INSULT: INSULT,
    INTENT_JOKE: JOKE,
    INTENT_UNKNOWN: UNKNOWN,
}


def generate_response(message: str, session_id: str = "default") -> dict:
    """
    Processa a mensagem e retorna a resposta do KAIRUS.
    Hibrido: regras para intencoes conhecidas, LLM para o resto.
    """
    clean_message = message.strip()
    memory = get_memory(session_id)

    if not clean_message:
        return {
            "response": "Voce nao enviou nenhuma mensagem.",
            "intent": "empty",
            "model": f"{NAME}-core-{VERSION}",
        }

    is_repeat = detect_repetition(clean_message, memory.messages)
    intent = classify(clean_message)
    sentiment = detect_sentiment(clean_message)
    memory.add_topic(intent)

    response_text = ""
    tool_used = None
    used_llm = False

    # =========================
    # CAMINHO 1: FERRAMENTAS
    # =========================

    if intent == INTENT_TOOL_USE:
        tool_name = detect_tool(clean_message)
        if tool_name:
            tool_used = tool_name
            result = execute_tool(tool_name, clean_message)
            response_text = result if result else pick(UNKNOWN)

    # =========================
    # CAMINHO 2: REGRAS (intencoes conhecidas)
    # =========================

    elif intent in RULE_INTENTS:
        response_text = _handle_rule_intent(intent, clean_message, memory, is_repeat)

    # =========================
    # CAMINHO 3: LLM (intencao desconhecida)
    # =========================

    elif intent == INTENT_UNKNOWN and is_available():
        llm_response = generate_llm_response(
            message=clean_message,
            history=memory.messages,
        )

        if llm_response:
            response_text = llm_response
            used_llm = True
        else:
            # Fallback se LLM falhar
            response_text = pick(UNKNOWN)

    # =========================
    # CAMINHO 4: FALLBACK (sem LLM)
    # =========================

    else:
        response_text = pick(UNKNOWN)

    # Registra na memoria
    memory.add_message("user", clean_message, intent)
    memory.add_message("assistant", response_text, intent)

    # Determinar modelo usado
    if used_llm:
        model_name = f"{NAME}-llm-{VERSION}"
    else:
        model_name = f"{NAME}-core-{VERSION}"

    result = {
        "response": response_text,
        "intent": intent,
        "model": model_name,
        "memory": {
            "message_count": memory.message_count,
            "user_name": memory.get_user_info("name"),
            "stage": get_conversation_stage(memory.message_count),
            "sentiment": sentiment,
        },
    }

    if tool_used:
        result["tool"] = tool_used

    if used_llm:
        result["llm"] = True

    return result


def _handle_rule_intent(intent: str, message: str, memory, is_repeat: bool) -> str:
    """Processa intencoes conhecidas com regras."""

    if intent == INTENT_NAME_TELL:
        name = extract_name(message)
        if name:
            memory.set_user_info("name", name)
            template = random.choice(NAME_TELL)
            return template.format(name=name)
        return pick(UNKNOWN)

    elif intent == INTENT_NAME_ASK:
        stored_name = memory.get_user_info("name")
        if stored_name:
            template = random.choice(NAME_ASK_KNOWN)
            return template.format(name=stored_name)
        return pick(NAME_ASK_UNKNOWN)

    elif is_repeat and intent != INTENT_NAME_TELL:
        return pick(REPEAT_DETECTED)

    elif intent == INTENT_CONTEXT:
        summary = memory.get_context_summary()
        template = random.choice(CONTEXT_SUMMARY)
        return template.format(summary=summary)

    elif intent == INTENT_COUNT:
        template = random.choice(MESSAGE_COUNT)
        return template.format(count=memory.message_count + 1)

    elif intent == INTENT_GREETING:
        stage = get_conversation_stage(memory.message_count)
        user_name = memory.get_user_info("name")

        if stage == "opening":
            return pick(CONVERSATION_OPENING)
        elif user_name:
            return f"Oi de novo, {user_name}! Como posso ajudar agora?"
        return pick(GREETINGS)

    else:
        response_list = INTENT_RESPONSE_MAP.get(intent, UNKNOWN)
        response_text = pick(response_list)

        user_name = memory.get_user_info("name")
        stage = get_conversation_stage(memory.message_count)

        if user_name and stage in ("mid", "deep") and intent not in (
            INTENT_NAME_TELL, INTENT_NAME_ASK
        ):
            if random.random() < 0.3:
                response_text = f"{user_name}, {response_text[0].lower()}{response_text[1:]}"

        return response_text