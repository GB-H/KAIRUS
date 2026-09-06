"""
FASE 3.2 - Comandos de memoria de longo prazo.
"""
import ai.engine as engine
from backend.database.db import init_db, delete_longterm_memory
from ai.engine import generate_response


init_db()


USER_C = 900003
USER_D = 900004


def test_lembre_que_salva_fato():
    r = generate_response(
        "lembre que eu gosto de programar em python",
        session_id="mc_1",
        user_id=USER_C,
    )
    assert "Anotado" in r["response"]

    r2 = generate_response(
        "o que voce lembra de mim?",
        session_id="mc_1",
        user_id=USER_C,
    )
    assert "python" in r2["response"]

    delete_longterm_memory(USER_C, "facts")


def test_recall_sem_memorias():
    r = generate_response(
        "o que voce lembra de mim?",
        session_id="mc_2",
        user_id=USER_D,
    )
    assert "Ainda nao" in r["response"]


def test_sem_user_id_nao_quebra(monkeypatch):
    monkeypatch.setattr(engine, "is_available", lambda: False)
    r = generate_response(
        "lembre que eu gosto de cafe",
        session_id="mc_3",
    )
    assert r["response"]