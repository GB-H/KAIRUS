"""
FASE 2.2 - Testes de pipeline multi-agente.

Verifica colaboracao real entre agentes (Researcher -> Analyst -> Writer).
"""
from ai.orchestrator import Orchestrator


def pipeline_llm(captured=None):
    """LLM simulado que retorna saidas previsiveis por agente."""
    captured = captured if captured is not None else {}

    def llm(prompt, system, model=None):
        if "Security" in system:
            return "SEGURO"
        if "Planner" in system:
            captured.setdefault("planner_calls", 0)
            captured["planner_calls"] += 1
            return (
                "1. Pesquisar informacoes sobre o tema\n"
                "2. Analisar os dados coletados\n"
                "3. Escrever o relatorio final"
            )
        if "Reviewer" in system:
            return "APROVADO"
        if "Researcher" in system:
            captured.setdefault("researcher_called", True)
            return "Informacoes coletadas: X, Y, Z"
        if "Analyst" in system:
            captured.setdefault("analyst_called", True)
            return "Analise concluida: tendencia positiva"
        if "Writer" in system:
            captured.setdefault("writer_called", True)
            return "Relatorio final redigido com base nas etapas anteriores"
        if "Coder" in system:
            return "Codigo gerado"
        return "resposta generica"

    return llm, captured


def test_pipeline_tres_agentes():
    """Researcher -> Analyst -> Writer em cadeia."""
    llm, captured = pipeline_llm()
    orch = Orchestrator(llm_call=llm)

    result = orch.run(
        "Crie um relatorio completo sobre inteligencia artificial"
    )

    assert result.success is True
    assert "Relatorio final redigido" in result.output
    assert captured["researcher_called"] is True
    assert captured["analyst_called"] is True
    assert captured["writer_called"] is True

    worker_steps = [
        s for s in result.steps
        if s.agent in ("researcher", "analyst", "writer")
    ]
    assert len(worker_steps) == 3


def test_pipeline_cada_etapa_alimenta_a_proxima():
    """Cada agente recebe o output do anterior como contexto."""
    captured_contexts = []

    def llm(prompt, system, model=None):
        if "Security" in system:
            return "SEGURO"
        if "Planner" in system:
            # Etapa 1 sem keywords de analyst/coder -> Researcher
            # Etapa 2 com 'escreva' -> Writer
            return (
                "1. Pesquisar informacoes de vendas\n"
                "2. Escreva a conclusao"
            )
        if "Reviewer" in system:
            return "APROVADO"
        if "Researcher" in system:
            captured_contexts.append(("researcher", prompt))
            return "Dados coletados: A, B, C"
        if "Writer" in system:
            captured_contexts.append(("writer", prompt))
            return "Conclusao escrita"
        return "ok"

    orch = Orchestrator(llm_call=llm)
    orch.run("Analise e conclua sobre vendas")

    # Writer recebe o output do Researcher no contexto
    writer_ctx = next(c for name, c in captured_contexts if name == "writer")
    assert "Dados coletados: A, B, C" in writer_ctx


def test_planner_sem_linhas_numeradas_usa_agente_unico():
    """Plano invalido (sem linhas numeradas) -> fallback para agente unico."""
    def llm(prompt, system, model=None):
        if "Security" in system:
            return "SEGURO"
        if "Planner" in system:
            return "Plano criado"  # sem linhas numeradas
        if "Reviewer" in system:
            return "APROVADO"
        return "resposta do agente"

    orch = Orchestrator(llm_call=llm)
    result = orch.run("escreva um texto sobre o mar")

    assert result.success is True
    # Apenas 1 agente executado (writer)
    worker_steps = [
        s for s in result.steps
        if s.agent in ("researcher", "analyst", "writer", "coder")
    ]
    assert len(worker_steps) == 1
    assert worker_steps[0].agent == "writer"


def test_pipeline_quebra_se_agente_falha():
    """Se um agente falha no meio, pipeline interrompe com fallback."""
    def llm(prompt, system, model=None):
        if "Security" in system:
            return "SEGURO"
        if "Planner" in system:
            return "1. Pesquisar\n2. Analisar"
        if "Researcher" in system:
            raise RuntimeError("modelo caiu")
        return "ok"

    orch = Orchestrator(llm_call=llm)
    result = orch.run("pesquise e analise")

    # Security/planner ok, researcher falha, analyst nunca executou
    assert result.fallback is True
    assert result.success is False

    agents_executados = [
        s.agent for s in result.steps
        if s.agent in ("researcher", "analyst", "writer", "coder")
    ]
    assert "researcher" in agents_executados
    assert "analyst" not in agents_executados


def test_pipeline_com_tool():
    """Pipeline com tool no meio (Analyst usa calculator)."""
    def llm(prompt, system, model=None):
        if "Security" in system:
            return "SEGURO"
        if "Planner" in system:
            return "1. Analise quanto e 12 * 8\n2. Escreva conclusao"
        if "Reviewer" in system:
            return "APROVADO"
        if "Analyst" in system:
            # Deve receber o resultado da calculadora no prompt/contexto
            return f"Analise feita com base em: {prompt}"
        if "Writer" in system:
            return "Conclusao final"
        return "ok"

    orch = Orchestrator(llm_call=llm)
    result = orch.run("analise e escreva")

    assert result.success is True
    tool_steps = [
        s for s in result.steps if s.agent.startswith("tool:")
    ]
    assert any("calculator" in s.agent for s in tool_steps)


def test_pipeline_reviewer_rejeita_e_aprova_no_retry():
    """Reviewer rejeita na primeira, aprova no retry (com worker)."""
    attempt = {"n": 0}

    def llm(prompt, system, model=None):
        if "Security" in system:
            return "SEGURO"
        if "Planner" in system:
            return "Plano criado"  # agente unico
        if "Reviewer" in system:
            attempt["n"] += 1
            if attempt["n"] == 1:
                return "REPROVADO: falta detalhe"
            return "APROVADO"
        return "resposta melhorada"

    orch = Orchestrator(llm_call=llm)
    result = orch.run("escreva um texto sobre IA")

    assert result.success is True
    assert attempt["n"] == 2