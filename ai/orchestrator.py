"""
KAIRUS v0.6.0 - Orchestrator (FASE 1.5 + FASE 2)

Coordena os agentes especializados:

Usuario -> Security -> Planner -> Tools -> Agente -> Reviewer -> Resposta

Regras:

- Security pode bloquear entradas maliciosas
- Tools so executam se o agente tiver permissao (allowed_tools)
- Tool que falha nao trava o fluxo (segue sem ela)
- Reviewer tem no maximo MAX_RETRIES tentativas
- Se o Reviewer reprovar todas as tentativas, fallback=True
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
from .tools import detect_tool, execute_tool

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
        # 3. AGENTE + TOOLS (FASE 2)
        # ==========================================

        worker_name = self.classify(task)
        worker = self.registry.get(worker_name)

        # ---- 3.1 Tool execution com permissao ----
        tool_context = ""
        tool_name = detect_tool(task)

        if tool_name and tool_name in worker.allowed_tools:
            tool_output = execute_tool(tool_name, task)

            if tool_output:
                tool_context = (
                    "\nResultado da ferramenta "
                    + tool_name
                    + ": "
                    + tool_output
                )
                steps.append(
                    Step(
                        "tool:" + tool_name,
                        "ok",
                        tool_output[:200],
                    )
                )
            else:
                # Tool falhou: segue sem ela, sem travar o fluxo
                steps.append(
                    Step(
                        "tool:" + tool_name,
                        "fail",
                    )
                )

        # ---- 3.2 Agente executa com contexto da tool ----
        exec_result = worker.run(
            task,
            context + tool_context,
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

            redo = worker.run(
                task,
                context
                + tool_context
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

        steps.append(
            Step(
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