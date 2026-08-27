import ai.orchestrator as orch_mod
from ai.orchestrator import Orchestrator


def approve_llm(prompt, system, model=None):
    if "Security" in system:
        return "SEGURO"
    if "Reviewer" in system:
        return "APROVADO"
    return "resposta do agente"


def test_tool_executada_com_permissao():
    orch = Orchestrator(llm_call=approve_llm)
    result = orch.run("analise quanto e 25 * 4 nos dados de vendas")

    tool_steps = [s for s in result.steps if s.agent.startswith("tool:")]
    assert len(tool_steps) == 1
    assert tool_steps[0].agent == "tool:calculator"
    assert tool_steps[0].status == "ok"
    assert "100" in tool_steps[0].detail


def test_tool_sem_permissao_nao_executa():
    orch = Orchestrator(llm_call=approve_llm)
    # writer nao tem permissao para calculator
    result = orch.run("escreva um texto sobre quanto e 2 + 2")

    tool_steps = [s for s in result.steps if s.agent.startswith("tool:")]
    assert len(tool_steps) == 0


def test_resultado_da_tool_chega_no_agente():
    captured = {}

    def llm(prompt, system, model=None):
        if "Analyst" in system:
            captured["prompt"] = prompt
        if "Security" in system:
            return "SEGURO"
        if "Reviewer" in system:
            return "APROVADO"
        return "resposta"

    orch = Orchestrator(llm_call=llm)
    orch.run("analise quanto e 10 + 5")

    assert "15" in captured.get("prompt", "")


def test_tool_com_erro_nao_trava(monkeypatch):
    monkeypatch.setattr(
        orch_mod, "execute_tool", lambda name, msg: None
    )
    orch = Orchestrator(llm_call=approve_llm)
    result = orch.run("analise quanto e 2 + 2")

    assert result.success is True
    tool_steps = [s for s in result.steps if s.agent.startswith("tool:")]
    assert tool_steps[0].status == "fail"


def test_sem_tool_detectada_segue_normal():
    orch = Orchestrator(llm_call=approve_llm)
    result = orch.run("escreva um poema sobre o mar")

    assert result.success is True
    tool_steps = [s for s in result.steps if s.agent.startswith("tool:")]
    assert len(tool_steps) == 0