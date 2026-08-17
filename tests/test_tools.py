"""
Testes para ai/tools.py — sistema de ferramentas.
"""

from ai.tools import (
    detect_tool,
    execute_tool,
    get_available_tools,
    tool_datetime,
    tool_calculator,
    tool_text_counter,
)


class TestToolDetection:

    def test_detect_time(self):
        assert detect_tool("que horas sao?") == "datetime"

    def test_detect_date(self):
        assert detect_tool("data de hoje?") == "datetime"

    def test_detect_calc(self):
        assert detect_tool("quanto e 2 + 2?") == "calculator"

    def test_detect_counter(self):
        assert detect_tool("quantas palavras tem aqui?") == "text_counter"

    def test_detect_list_tools(self):
        assert detect_tool("quais ferramentas voce tem?") == "list_tools"

    def test_no_tool(self):
        assert detect_tool("oi tudo bem") is None


class TestCalculator:

    def test_simple_addition(self):
        result = tool_calculator("quanto e 2 + 2")
        assert "4" in result

    def test_multiplication(self):
        result = tool_calculator("quanto e 3 * 5")
        assert "15" in result

    def test_division(self):
        result = tool_calculator("quanto e 10 / 2")
        assert "5" in result

    def test_division_by_zero(self):
        result = tool_calculator("quanto e 1 / 0")
        assert "zero" in result.lower() or "possivel" in result.lower()

    def test_invalid_expression(self):
        result = tool_calculator("calcula abc")
        assert "nao" in result.lower() or "invalida" in result.lower()


class TestDatetime:

    def test_returns_time(self):
        result = tool_datetime("que horas sao?")
        assert "Agora sao" in result or "hora" in result.lower()

    def test_returns_date(self):
        result = tool_datetime("data de hoje?")
        assert "Hoje" in result or "data" in result.lower()


class TestTextCounter:

    def test_count_words(self):
        result = tool_text_counter("quantas palavras tem 'ola mundo aqui'?")
        assert "3" in result

    def test_count_characters(self):
        result = tool_text_counter("conta caracteres de 'abc'")
        assert "caracter" in result.lower()


class TestAvailableTools:

    def test_has_tools(self):
        tools = get_available_tools()
        assert len(tools) >= 4

    def test_tool_names(self):
        tools = get_available_tools()
        names = [t["name"] for t in tools]
        assert "datetime" in names
        assert "calculator" in names
        assert "text_counter" in names
        assert "list_tools" in names