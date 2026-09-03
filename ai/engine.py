"""
KAIRUS AI Engine - Orquestrador principal.
Modelo hibrido: regras para intencoes conhecidas + LLM para o resto.
v0.6.0: modo multi-agente (Orchestrator) atras da flag ORCHESTRATOR_ENABLED.
FASE 2.3: eventos SSE "agents" com os steps do pipeline em tempo real.
"""

import os
import random

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
from ai.llm import (
    generate_llm_response,
    stream_llm_response,
    is_available,
    get_model_name,
)
from ai.personality import NAME, VERSION
from ai.orchestrator import Orchestrator


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


# =========================
# MODO MULTI-AGENTE (FASE 1)
# =========================

def _orchestrator_enabled() -> bool:
    """Flag de seguranca: modo multi-agente so liga se ativado explicitamente."""
    return os.getenv("ORCHESTRATOR_ENABLED", "off").strip().lower() == "on"


def _is_complex_task(task: str) -> bool:
    """Heuristica rapida: so aciona a equipe de agentes se valer a pena."""
    t = task.lower()
    keywords = (
        "planeje", "passo a passo", "analise", "escreva um texto",
        "resuma", "pesquise", "explique detalhadamente", "compare",
    )
    return len(task) > 140 or any(k in t for k in keywords)


def _llm_adapter(prompt: str, system: str, model=None) -> str:
    """Adapta a chamada dos agentes para o llm.py existente (com failover)."""
    return generate_llm_response(
        message=system + "\n\n" + prompt,
        history=[],
    ) or ""


def _run_orchestrator_safe(message: str):
    """Roda a equipe de agentes. Se QUALQUER coisa falhar, retorna (None, [])
    e o engine segue o fluxo normal. O KAIRUS nunca fica mudo.

    Retorna: (output, steps_detalhados)
    steps_detalhados: [{"agent": nome, "status": status}, ...]
    """
    try:
        orch = Orchestrator(llm_call=_llm_adapter)
        result = orch.run(message)
        if (
            result
            and result.success
            and not result.fallback
            and result.output.strip()
        ):
            steps = [
                {"agent": s.agent, "status": s.status}
                for s in result.steps
            ]
            return result.output, steps
    except Exception:
        pass
    return None, []


def generate_response(message: str, session_id: str = "default") -> dict:
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

    if intent == INTENT_TOOL_USE:
        tool_name = detect_tool(clean_message)
        if tool_name:
            tool_used = tool_name
            result = execute_tool(tool_name, clean_message)
            response_text = result if result else pick(UNKNOWN)

    elif intent in RULE_INTENTS:
        response_text = _handle_rule_intent(intent, clean_message, memory, is_repeat)

    elif intent == INTENT_UNKNOWN and is_available():
        orch_output = None
        if _orchestrator_enabled() and _is_complex_task(clean_message):
            orch_output, _steps = _run_orchestrator_safe(clean_message)

        if orch_output:
            response_text = orch_output
            used_llm = True
        else:
            llm_response = generate_llm_response(
                message=clean_message,
                history=memory.messages,
            )
            if llm_response:
                response_text = llm_response
                used_llm = True
            else:
                response_text = pick(UNKNOWN)

    else:
        response_text = pick(UNKNOWN)

    memory.add_message("user", clean_message, intent)
    memory.add_message("assistant", response_text, intent)

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


def stream_response(message: str, session_id: str = "default"):
    """Versao streaming do generate_response."""
    clean_message = message.strip()
    memory = get_memory(session_id)

    if not clean_message:
        text = "Voce nao enviou nenhuma mensagem."
        yield {"type": "meta", "intent": "empty", "llm": False, "tool": None, "agents": []}
        yield {"type": "token", "text": text}
        yield {
            "type": "done",
            "response": text,
            "intent": "empty",
            "model": f"{NAME}-core-{VERSION}",
            "llm": False,
            "tool": None,
            "agents": [],
        }
        return

    is_repeat = detect_repetition(clean_message, memory.messages)
    intent = classify(clean_message)
    memory.add_topic(intent)

    tool_used = None
    used_llm = False
    full_text = ""
    orchestrated = False
    orch_steps = []

    if intent == INTENT_TOOL_USE:
        tool_name = detect_tool(clean_message)
        if tool_name:
            tool_used = tool_name
            full_text = execute_tool(tool_name, clean_message) or pick(UNKNOWN)

    elif intent in RULE_INTENTS:
        full_text = _handle_rule_intent(intent, clean_message, memory, is_repeat)

    elif intent == INTENT_UNKNOWN and is_available():
        if _orchestrator_enabled() and _is_complex_task(clean_message):
            orch_output, orch_steps = _run_orchestrator_safe(clean_message)
            if orch_output:
                orchestrated = True
                full_text = orch_output
        used_llm = True

    else:
        full_text = pick(UNKNOWN)

    yield {
        "type": "meta",
        "intent": intent,
        "llm": used_llm,
        "tool": tool_used,
        "agents": orch_steps,
    }

    # FASE 2.3: envia os steps do pipeline para o frontend
    if orchestrated:
        yield {"type": "agents", "steps": orch_steps}

    if orchestrated:
        # resposta da equipe de agentes, enviada em pedacos (efeito de digitar)
        chunk = 4
        for i in range(0, len(full_text), chunk):
            yield {"type": "token", "text": full_text[i:i + chunk]}

    elif used_llm:
        streamed = False
        for token in stream_llm_response(clean_message, history=memory.messages):
            streamed = True
            full_text += token
            yield {"type": "token", "text": token}

        if not streamed:
            text = generate_llm_response(clean_message, history=memory.messages)
            if text:
                full_text = text
                yield {"type": "token", "text": text}
            else:
                used_llm = False
                full_text = pick(UNKNOWN)
                yield {"type": "token", "text": full_text}
    else:
        if not full_text:
            full_text = pick(UNKNOWN)
        yield {"type": "token", "text": full_text}

    memory.add_message("user", clean_message, intent)
    memory.add_message("assistant", full_text, intent)

    yield {
        "type": "done",
        "response": full_text,
        "intent": intent,
        "model": f"{NAME}-llm-{VERSION}" if used_llm else f"{NAME}-core-{VERSION}",
        "llm": used_llm,
        "tool": tool_used,
        "agents": orch_steps,
    }


def _handle_rule_intent(intent: str, message: str, memory, is_repeat: bool) -> str:
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