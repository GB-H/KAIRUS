from ai.agents import BaseAgent, AgentRegistry


class EchoAgent(BaseAgent):
    name = "echo"
    description = "Agente de teste que responde a tarefa."


def fake_llm(prompt, system, model=None):
    return f"RESPOSTA: {prompt}"


def failing_llm(prompt, system, model=None):
    raise RuntimeError("modelo caiu")


def test_agent_sucesso():
    agent = EchoAgent(llm_call=fake_llm)
    result = agent.run("teste")
    assert result.success is True
    assert "RESPOSTA" in result.output
    assert result.agent == "echo"


def test_agent_erro_de_llm():
    agent = EchoAgent(llm_call=failing_llm)
    result = agent.run("teste")
    assert result.success is False
    assert "modelo caiu" in result.error


def test_agent_tarefa_vazia():
    agent = EchoAgent(llm_call=fake_llm)
    result = agent.run("   ")
    assert result.success is False


def test_agent_sem_llm():
    agent = EchoAgent()
    result = agent.run("teste")
    assert result.success is False


def test_registry():
    registry = AgentRegistry()
    agent = EchoAgent(llm_call=fake_llm)
    registry.register(agent)

    assert registry.get("echo") is agent
    assert registry.get("inexistente") is None
    assert "echo" in registry.names()
    assert registry.describe()[0]["name"] == "echo"
