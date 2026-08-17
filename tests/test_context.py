"""
Testes para ai/context.py — analise de contexto.
"""

from ai.context import (
    extract_name,
    extract_question_about,
    detect_sentiment,
    detect_repetition,
    get_conversation_stage,
)


class TestExtractName:

    def test_meu_nome_e(self):
        assert extract_name("meu nome e Gabriel") == "Gabriel"

    def test_meu_nome_eh(self):
        assert extract_name("meu nome eh Maria") == "Maria"

    def test_eu_sou(self):
        assert extract_name("eu sou Pedro") == "Pedro"

    def test_me_chamo(self):
        assert extract_name("me chamo Ana") == "Ana"

    def test_pode_me_chamar_de(self):
        assert extract_name("pode me chamar de Lucas") == "Lucas"

    def test_no_name(self):
        assert extract_name("oi tudo bem") is None

    def test_skip_common_words(self):
        assert extract_name("eu sou o melhor") is None

    def test_capitalizes(self):
        assert extract_name("meu nome e gabriel") == "Gabriel"


class TestExtractQuestionAbout:

    def test_qual_meu_nome(self):
        assert extract_question_about("qual meu nome?") == "name"

    def test_como_eu_me_chamo(self):
        assert extract_question_about("como eu me chamo?") == "name"

    def test_voce_sabe_meu_nome(self):
        assert extract_question_about("voce sabe meu nome?") == "name"

    def test_lembra_meu_nome(self):
        assert extract_question_about("lembra meu nome?") == "name"

    def test_no_question(self):
        assert extract_question_about("oi tudo bem") is None


class TestDetectSentiment:

    def test_positive(self):
        assert detect_sentiment("isso e incrivel") == "positive"

    def test_negative(self):
        assert detect_sentiment("isso e horrivel") == "negative"

    def test_neutral(self):
        assert detect_sentiment("oi") == "neutral"

    def test_mixed_positive_wins(self):
        assert detect_sentiment("horrivel mas legal e incrivel") == "positive"

    def test_mixed_neutral_on_tie(self):
        assert detect_sentiment("horrivel mas legal") == "neutral"


class TestDetectRepetition:

    def test_is_repeat(self):
        history = [{"role": "user", "content": "oi"}]
        assert detect_repetition("oi", history) is True

    def test_is_not_repeat(self):
        history = [{"role": "user", "content": "oi"}]
        assert detect_repetition("tchau", history) is False

    def test_empty_history(self):
        assert detect_repetition("oi", []) is False

    def test_ignores_assistant_messages(self):
        history = [{"role": "assistant", "content": "oi"}]
        assert detect_repetition("oi", history) is False


class TestConversationStage:

    def test_opening(self):
        assert get_conversation_stage(0) == "opening"
        assert get_conversation_stage(1) == "opening"

    def test_early(self):
        assert get_conversation_stage(3) == "early"
        assert get_conversation_stage(5) == "early"

    def test_mid(self):
        assert get_conversation_stage(10) == "mid"

    def test_deep(self):
        assert get_conversation_stage(20) == "deep"