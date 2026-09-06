"""
FASE 3.1 - Memoria de longo prazo por usuario.
"""
from backend.database.db import (
    init_db,
    set_longterm_memory,
    get_longterm_memory,
    delete_longterm_memory,
)
from ai.engine import generate_response
from ai.memory import get_memory, clear_memory


init_db()


USER_A = 900001
USER_B = 900002


def test_set_e_get_longterm():
    set_longterm_memory(USER_A, "name", "Gabriel")
    facts = get_longterm_memory(USER_A)
    assert facts.get("name") == "Gabriel"

    delete_longterm_memory(USER_A, "name")
    assert get_longterm_memory(USER_A).get("name") is None


def test_engine_persiste_nome_com_user_id():
    generate_response(
        "meu nome eh Gabriel",
        session_id="lt_conv_1",
        user_id=USER_A,
    )

    facts = get_longterm_memory(USER_A)
    assert facts.get("name") == "Gabriel"

    delete_longterm_memory(USER_A, "name")


def test_conversa_nova_lembra_nome():
    set_longterm_memory(USER_B, "name", "Ana")

    generate_response("oi", session_id="lt_conv_2", user_id=USER_B)

    memory = get_memory("lt_conv_2")
    assert memory.get_user_info("name") == "Ana"

    delete_longterm_memory(USER_B, "name")
    clear_memory("lt_conv_2")