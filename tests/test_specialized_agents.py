from ai.agents import (
    PlannerAgent,
    ResearcherAgent,
    CoderAgent,
    AnalystAgent,
    WriterAgent,
    ReviewerAgent,
    SecurityAgent,
)

def fake_llm(prompt, system, model=None):
    return "OK"

def test_agentes_instanciam():
    agentes = [
        PlannerAgent,
        ResearcherAgent,
        CoderAgent,
        AnalystAgent,
        WriterAgent,
        ReviewerAgent,
        SecurityAgent,
    ]
    for Agente in agentes:
        agente = Agente(llm_call=fake_llm)
        assert agente.name
        assert agente.description
        assert "KAIRUS" in agente.system_prompt()
        result = agente.run("tarefa de teste")
        assert result.success is True
        assert result.agent == agente.name
