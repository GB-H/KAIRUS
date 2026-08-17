"""
Testes para ai/utils.py — normalizacao de texto.
"""

from ai.utils import normalize, contains_any, starts_with_any


class TestNormalize:

    def test_lowercase(self):
        assert normalize("OI") == "oi"

    def test_remove_accents(self):
        assert normalize("olá") == "ola"
        assert normalize("você") == "voce"
        assert normalize("não") == "nao"

    def test_strip_spaces(self):
        assert normalize("  oi  ") == "oi"

    def test_remove_punctuation(self):
        assert normalize("olá!") == "ola"
        assert normalize("quem é você?") == "quem e voce"

    def test_multiple_spaces(self):
        assert normalize("oi   tudo   bem") == "oi tudo bem"

    def test_empty_string(self):
        assert normalize("") == ""

    def test_complex_sentence(self):
        result = normalize("Olá! Como você está hoje?")
        assert result == "ola como voce esta hoje"


class TestContainsAny:

    def test_contains_keyword(self):
        assert contains_any("oi tudo bem", ["oi", "ola"]) is True

    def test_does_not_contain(self):
        assert contains_any("tchau", ["oi", "ola"]) is False

    def test_case_insensitive(self):
        assert contains_any("OI TUDO BEM", ["oi"]) is True

    def test_accent_insensitive(self):
        assert contains_any("olá amigo", ["ola"]) is True

    def test_empty_keywords(self):
        assert contains_any("oi", []) is False


class TestStartsWithAny:

    def test_starts_with(self):
        assert starts_with_any("oi tudo bem", ["oi", "ola"]) is True

    def test_does_not_start_with(self):
        assert starts_with_any("tudo bem oi", ["oi"]) is False

    def test_case_insensitive(self):
        assert starts_with_any("OI amigo", ["oi"]) is True