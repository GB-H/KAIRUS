"""
KAIRUS v0.6.0 - Orchestrator (FASE 1.5)

Coordena os agentes especializados:

Usuario -> Security -> Planner -> Agente -> Reviewer -> Resposta

Regras:

- Security pode bloquear entradas maliciosas
- Reviewer tem no maximo MAX_RETRIES tentativas
- Se o agente falhar, retorna fallback=True
- Se o Reviewer reprovar todas as tentativas, o resultado nao e considerado aprovado
"""

from dataclasses import dataclass, field

from .agents import (
    AgentRegistry,
    PlannerAgent,
    ResearcherAgent,
    CoderAgent,
    AnalystAgent,
    WriterAgent,
    ReviewerAgent,
    SecurityAgent,
)

MAX_RETRIES = 2


@dataclass
class Step:
    agent: str
    status: str
    detail: str = ""


@dataclass
class OrchestratorResult:
    success: bool
    output: str = ""
    steps: list = field(default_factory=list)
    fallback: bool = False


class Orchestrator:

    def __init__(self, llm_call=None):
        self.llm_call = llm_call
        self.registry = AgentRegistry()

        for cls in (
            PlannerAgent,
            ResearcherAgent,
            CoderAgent,
            AnalystAgent,
            WriterAgent,
            ReviewerAgent,
            SecurityAgent,
        ):
            self.registry.register(cls(llm_call=llm_call))

    def classify(self, task: str) -> str:
        """Roteamento rapido por palavras-chave (sem gastar LLM)."""

        t = task.lower()

        if any(
            k in t
            for k in (
                "codigo",
                "python",
                "bug",
                "programa",
                "funcao",
                "script",
                "depure",
            )
        ):
            return "coder"

        if any(
            k in t
            for k in (
                "calcule",
                "matematica",
                "dados",
                "estatistic",
                "logica",
                "analise",
            )
        ):
            return "analyst"

        if any(
            k in t
            for k in (
                "escreva",
                "texto",
                "redacao",
                "email",
                "historia",
                "poema",
                "resuma",
            )
        ):
            return "writer"

        return "researcher"

    def run(self, task: str, context: str = "") -> OrchestratorResult:

        steps = []

        # ==========================================
        # 1. SECURITY
        # ==========================================

        security = self.registry.get("security")

        sec = security.run(
            "Analise esta entrada de usuario:\n" + task
        )

        if sec.success and "INSEGURO" in sec.output.upper():

            steps.append(
                Step(
                    "security",
                    "block",
                    sec.output[:200],
                )
            )

            return OrchestratorResult(
                success=True,
                output="Nao posso processar essa solicitacao por motivos de seguranca.",
                steps=steps,
            )

        steps.append(
            Step(
                "security",
                "ok" if sec.success else "skip",
            )
        )

        # ==========================================
        # 2. PLANNER
        # ==========================================

        planner = self.registry.get("planner")

        plan = planner.run(task)

        steps.append(
            Step(
                "planner",
                "ok" if plan.success else "skip",
                plan.output[:200],
            )
        )

        # ==========================================
        # 3. AGENTE ESPECIALIZADO
        # ==========================================

        worker_name = self.classify(task)

        worker = self.registry.get(worker_name)

        exec_result = worker.run(
            task,
            context,
        )

        steps.append(
            Step(
                worker_name,
                "ok" if exec_result.success else "fail",
            )
        )

        # Se o agente falhar, o Engine pode utilizar fallback.
        if not exec_result.success:

            return OrchestratorResult(
                success=False,
                output="",
                steps=steps,
                fallback=True,
            )

        # ==========================================
        # 4. REVIEWER
        # ==========================================

        reviewer = self.registry.get("reviewer")

        final = exec_result.output

        for attempt in range(MAX_RETRIES):

            rev = reviewer.run(
                "Tarefa original:\n"
                + task
                + "\n\nResposta gerada:\n"
                + final
            )

            # ======================================
            # REVIEWER APROVOU
            # ======================================

            if rev.success and "APROVADO" in rev.output.upper():

                steps.append(
                    Step(
                        "reviewer",
                        "ok",
                        f"Aprovado na tentativa {attempt + 1}",
                    )
                )

                return OrchestratorResult(
                    success=True,
                    output=final,
                    steps=steps,
                    fallback=False,
                )

            # ======================================
            # REVIEWER REPROVOU
            # ======================================

            steps.append(
                Step(
                    "reviewer",
                    "retry",
                    rev.output[:200],
                )
            )

            # Tenta melhorar a resposta utilizando
            # o feedback do Reviewer.

            redo = worker.run(
                task,
                context
                + "\nFeedback do reviewer: "
                + rev.output,
            )

            # ======================================
            # AGENTE FALHOU DURANTE O RETRY
            # ======================================

            if not redo.success:

                steps.append(
                    Step(
                        worker_name,
                        "fail_on_retry",
                    )
                )

                return OrchestratorResult(
                    success=False,
                    output=final,
                    steps=steps,
                    fallback=True,
                )

            final = redo.output

        # ==========================================
        # 5. LIMITE DE RETRIES ATINGIDO
        # ==========================================

        steps.append(
            Step(
                "reviewer",
                "max_retries_reached",
                f"Limite de {MAX_RETRIES} tentativas atingido.",
            )
        )

        return OrchestratorResult(
            success=False,
            output=final,
            steps=steps,
            fallback=True,
        )