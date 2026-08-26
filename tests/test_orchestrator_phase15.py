from ai.orchestrator import Orchestrator, MAX_RETRIES


class FakeResult:
    def __init__(self, success=True, output=""):
        self.success = success
        self.output = output


class FakeAgent:
    def __init__(self, results):
        self.results = iter(results)

    def run(self, *args, **kwargs):
        return next(self.results)


class FakeRegistry:
    def __init__(self, agents):
        self.agents = agents

    def get(self, name):
        return self.agents[name]


def make_orchestrator(
    security_results,
    planner_results,
    worker_results,
    reviewer_results,
):
    orchestrator = Orchestrator()

    worker = FakeAgent(worker_results)

    orchestrator.registry = FakeRegistry(
        {
            "security": FakeAgent(security_results),
            "planner": FakeAgent(planner_results),
            "coder": worker,
            "analyst": worker,
            "writer": worker,
            "researcher": worker,
            "reviewer": FakeAgent(reviewer_results),
        }
    )

    return orchestrator


def test_reviewer_aprova_na_primeira_tentativa():
    orchestrator = make_orchestrator(
        security_results=[
            FakeResult(True, "SEGURO")
        ],
        planner_results=[
            FakeResult(True, "Plano criado")
        ],
        worker_results=[
            FakeResult(True, "Resposta correta")
        ],
        reviewer_results=[
            FakeResult(True, "APROVADO")
        ],
    )

    result = orchestrator.run("Escreva um texto")

    assert result.success is True
    assert result.fallback is False
    assert result.output == "Resposta correta"

    reviewer_steps = [
        step for step in result.steps
        if step.agent == "reviewer"
    ]

    assert len(reviewer_steps) == 1
    assert reviewer_steps[0].status == "ok"


def test_reviewer_reprova_e_depois_aprova():
    orchestrator = make_orchestrator(
        security_results=[
            FakeResult(True, "SEGURO")
        ],
        planner_results=[
            FakeResult(True, "Plano criado")
        ],
        worker_results=[
            FakeResult(True, "Primeira resposta"),
            FakeResult(True, "Resposta corrigida"),
        ],
        reviewer_results=[
            FakeResult(True, "REPROVADO: precisa melhorar"),
            FakeResult(True, "APROVADO"),
        ],
    )

    result = orchestrator.run("Escreva um texto")

    assert result.success is True
    assert result.fallback is False
    assert result.output == "Resposta corrigida"

    reviewer_steps = [
        step for step in result.steps
        if step.agent == "reviewer"
    ]

    assert len(reviewer_steps) == 2
    assert reviewer_steps[0].status == "retry"
    assert reviewer_steps[1].status == "ok"


def test_reviewer_atinge_limite_de_retries():
    orchestrator = make_orchestrator(
        security_results=[
            FakeResult(True, "SEGURO")
        ],
        planner_results=[
            FakeResult(True, "Plano criado")
        ],
        worker_results=[
            FakeResult(True, "Resposta inicial"),
            FakeResult(True, "Resposta corrigida 1"),
            FakeResult(True, "Resposta corrigida 2"),
        ],
        reviewer_results=[
            FakeResult(True, "REPROVADO"),
            FakeResult(True, "REPROVADO"),
        ],
    )

    result = orchestrator.run("Escreva um texto")

    assert result.success is False
    assert result.fallback is True
    assert result.output == "Resposta corrigida 2"

    reviewer_steps = [
        step for step in result.steps
        if step.agent == "reviewer"
    ]

    assert len(reviewer_steps) == MAX_RETRIES + 1

    assert reviewer_steps[0].status == "retry"
    assert reviewer_steps[1].status == "retry"
    assert reviewer_steps[-1].status == "max_retries_reached"


def test_worker_falha_ativa_fallback():
    orchestrator = make_orchestrator(
        security_results=[
            FakeResult(True, "SEGURO")
        ],
        planner_results=[
            FakeResult(True, "Plano criado")
        ],
        worker_results=[
            FakeResult(False, "")
        ],
        reviewer_results=[],
    )

    result = orchestrator.run("Escreva um texto")

    assert result.success is False
    assert result.fallback is True


def test_worker_falha_durante_retry_ativa_fallback():
    orchestrator = make_orchestrator(
        security_results=[
            FakeResult(True, "SEGURO")
        ],
        planner_results=[
            FakeResult(True, "Plano criado")
        ],
        worker_results=[
            FakeResult(True, "Resposta inicial"),
            FakeResult(False, ""),
        ],
        reviewer_results=[
            FakeResult(True, "REPROVADO"),
        ],
    )

    result = orchestrator.run("Escreva um texto")

    assert result.success is False
    assert result.fallback is True

    retry_failures = [
        step for step in result.steps
        if step.status == "fail_on_retry"
    ]

    assert len(retry_failures) == 1