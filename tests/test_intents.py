"""
Testes para ai/intents.py — classificador de intencoes.
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
    INTENT_CONTEXT,
    INTENT_COUNT,
)


class TestGreeting:

    def test_oi(self):
        assert classify("oi") == INTENT_GREETING

    def test_ola(self):
        assert classify("ola") == INTENT_GREETING

    def test_bom_dia(self):
        assert classify("bom dia") == INTENT_GREETING

    def test_boa_noite(self):
        assert classify("boa noite") == INTENT_GREETING

    def test_eae(self):
        assert classify("eae") == INTENT_GREETING


class TestGoodbye:

    def test_tchau(self):
        assert classify("tchau") == INTENT_GOODBYE

    def test_ate_logo(self):
        assert classify("ate logo") == INTENT_GOODBYE

    def test_bye(self):
        assert classify("bye") == INTENT_GOODBYE


class TestThanks:

    def test_obrigado(self):
        assert classify("obrigado") == INTENT_THANKS

    def test_valeu(self):
        assert classify("valeu") == INTENT_THANKS


class TestIdentity:

    def test_quem_e_voce(self):
        assert classify("quem e voce?") == INTENT_IDENTITY

    def test_o_que_e_kairus(self):
        assert classify("o que e kairus?") == INTENT_IDENTITY


class TestHelp:

    def test_ajuda(self):
        assert classify("ajuda") == INTENT_HELP

    def test_me_ajude(self):
        assert classify("me ajude") == INTENT_HELP


class TestStatus:

    def test_status(self):
        assert classify("status") == INTENT_STATUS


class TestCapabilities:

    def test_o_que_vc_sabe(self):
        assert classify("o que vc sabe?") == INTENT_CAPABILITIES


class TestCompliment:

    def test_legal(self):
        assert classify("legal") == INTENT_COMPLIMENT

    def test_incrivel(self):
        assert classify("incrivel") == INTENT_COMPLIMENT


class TestInsult:

    def test_burro(self):
        assert classify("burro") == INTENT_INSULT


class TestJoke:

    def test_piada(self):
        assert classify("conta uma piada") == INTENT_JOKE


class TestNameTell:

    def test_meu_nome_e(self):
        assert classify("meu nome e Gabriel") == INTENT_NAME_TELL

    def test_me_chamo(self):
        assert classify("me chamo Ana") == INTENT_NAME_TELL


class TestNameAsk:

    def test_qual_meu_nome(self):
        assert classify("qual meu nome?") == INTENT_NAME_ASK

    def test_lembra_meu_nome(self):
        assert classify("lembra meu nome?") == INTENT_NAME_ASK


class TestContext:

    def test_resumo(self):
        assert classify("resumo") == INTENT_CONTEXT

    def test_contexto(self):
        assert classify("contexto") == INTENT_CONTEXT


class TestCount:

    def test_quantas_mensagens(self):
        assert classify("quantas mensagens trocamos?") == INTENT_COUNT


class TestUnknown:

    def test_random_question(self):
        assert classify("qual a capital da Franca?") == INTENT_UNKNOWN

    def test_empty(self):
        assert classify("") == INTENT_UNKNOWN

    def test_gibberish(self):
        assert classify("asdfghjkl") == INTENT_UNKNOWN