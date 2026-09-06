"""
KAIRUS v0.6.0 - Orchestrator (FASE 1.5 + FASE 2)

Coordena os agentes especializados:

Usuario -> Security -> Planner -> [Agentes] -> Reviewer -> Resposta

Regras:

- Security por regras (sem LLM) - FASE 2.6
- Tools so executam se o agente tiver permissao (allowed_tools)
- Tool que falha nao trava o fluxo (segue sem ela)
- Planner com 2+ linhas numeradas -> pipeline multi-agente
- Plano limitado a MAX_PLAN_STEPS etapas (custo/latencia)
- Plano vazio/invalido -> agente unico (fallback)
- Agente falhar no meio do pipeline -> fallback=True
- Reviewer tem no maximo MAX_RETRIES tentativas
- Backoff entre calls configuravel via KAIRUS_LLM_DELAY (segundos)
"""

import re
import time
import os
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
MAX_PLAN_STEPS = 2
CALL_DELAY_SECONDS = float(os.getenv("KAIRUS_LLM_DELAY", "0"))


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

    def _parse_plan(self, plan_text: str) -> list:
        """Extrai tarefas de um plano em lista numerada."""
        if not plan_text:
            return []

        tasks = []
        for line in plan_text.split("\n"):
            line = line.strip()
            match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
            if match:
                tasks.append(match.group(1).strip())
        return tasks

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
                "escrever",
                "texto",
                "redacao",
                "email",
                "historia",
                "poema",
                "resuma",
                "relatorio",
            )
        ):
            return "writer"

        return "researcher"

    def _execute_tool_if_allowed(
        self, task: str, worker, steps: list
    ) -> str:
        """Executa tool se o agente tiver permissao."""
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
                steps.append(
                    Step(
                        "tool:" + tool_name,
                        "fail",
                    )
                )

        return tool_context

    def _run_security_by_rules(self, task: str) -> tuple:
        """FASE 2.6: Security por regras (sem LLM) para economizar calls.

        Retorna: (is_safe, reason)
        """
        t = task.lower()

        injection_keywords = [
            "ignore", "esqueca", "ignore todas", "esqueca todas",
            "regras anteriores", "instrucoes anteriores",
            "voce agora e", "aja como se", "finja que",
            "modo desenvolvedor", "developer mode",
        ]
        if any(kw in t for kw in injection_keywords):
            return False, "Possivel prompt injection detectado"

        sensitive_patterns = [
            "senha", "password", "credit card", "cartao de credito",
            "cpf", "rg", "documento", "endereco",
        ]
        if any(kw in t for kw in sensitive_patterns):
            return False, "Dados sensiveis na entrada"

        dangerous_keywords = [
            "delete", "apague", "remove", "destroy",
            "hack", "invadir", "bypass",
        ]
        if any(kw in t for kw in dangerous_keywords):
            return False, "Comando potencialmente perigoso"

        return True, ""

    def run(self, task: str, context: str = "") -> OrchestratorResult:

        steps = []

        # ==========================================
        # 1. SECURITY (por regras, sem LLM)
        # ==========================================

        is_safe, reason = self._run_security_by_rules(task)

        if not is_safe:
            steps.append(
                Step(
                    "security",
                    "block",
                    reason,
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
                "ok",
            )
        )

        # ==========================================
        # 2. PLANNER (com backoff)
        # ==========================================

        planner = self.registry.get("planner")

        if CALL_DELAY_SECONDS > 0:
            time.sleep(CALL_DELAY_SECONDS)

        plan = planner.run(task)

        steps.append(
            Step(
                "planner",
                "ok" if plan.success else "skip",
                plan.output[:200],
            )
        )

        # ==========================================
        # 3. DECIDE: PIPELINE OU AGENTE UNICO
        # ==========================================

        plan_tasks = (
            self._parse_plan(plan.output)
            if plan.success
            else []
        )

        # FASE 2.6: limita o plano (menos chamadas de IA)
        plan_tasks = plan_tasks[:MAX_PLAN_STEPS]

        if len(plan_tasks) >= 2:
            return self._run_pipeline(
                task, plan_tasks, steps, context
            )

        return self._run_single_agent(
            task, steps, context
        )

    def _run_single_agent(
        self, task: str, steps: list, context: str
    ) -> OrchestratorResult:
        """Fluxo de agente unico + tools (FASE 2.1)."""

        worker_name = self.classify(task)
        worker = self.registry.get(worker_name)

        tool_context = self._execute_tool_if_allowed(
            task, worker, steps
        )

        if CALL_DELAY_SECONDS > 0:
            time.sleep(CALL_DELAY_SECONDS)

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

        if not exec_result.success:
            return OrchestratorResult(
                success=False,
                output="",
                steps=steps,
                fallback=True,
            )

        return self._run_reviewer(
            task, exec_result.output, steps, context,
            worker, tool_context
        )

    def _run_pipeline(
        self,
        task: str,
        plan_tasks: list,
        steps: list,
        initial_context: str,
    ) -> OrchestratorResult:
        """Executa agentes em cadeia: cada um recebe o output do anterior."""

        context = initial_context
        output = ""

        for subtask in plan_tasks:
            worker_name = self.classify(subtask)
            worker = self.registry.get(worker_name)

            tool_context = self._execute_tool_if_allowed(
                subtask, worker, steps
            )

            if CALL_DELAY_SECONDS > 0:
                time.sleep(CALL_DELAY_SECONDS)

            agent_input = f"Tarefa geral: {task}\n\nEtapa: {subtask}"
            exec_result = worker.run(
                agent_input,
                context + tool_context,
            )

            steps.append(
                Step(
                    worker_name,
                    "ok" if exec_result.success else "fail",
                    subtask[:100],
                )
            )

            if not exec_result.success:
                return OrchestratorResult(
                    success=False,
                    output=output,
                    steps=steps,
                    fallback=True,
                )

            output = exec_result.output
            context = (
                context
                + tool_context
                + "\nEtapa anterior (" + worker_name + "): "
                + output
            )

        return self._run_reviewer(
            task, output, steps, context
        )

    def _run_reviewer(
        self,
        task: str,
        final: str,
        steps: list,
        context: str = "",
        worker=None,
        tool_context: str = "",
    ) -> OrchestratorResult:
        """Reviewer com maximo de MAX_RETRIES tentativas."""

        reviewer = self.registry.get("reviewer")

        for attempt in range(MAX_RETRIES):

            if CALL_DELAY_SECONDS > 0:
                time.sleep(CALL_DELAY_SECONDS)

            rev = reviewer.run(
                "Tarefa original:\n"
                + task
                + "\n\nResposta gerada:\n"
                + final
            )

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

            steps.append(
                Step(
                    "reviewer",
                    "retry",
                    rev.output[:200],
                )
            )

            if worker is None:
                break

            if CALL_DELAY_SECONDS > 0:
                time.sleep(CALL_DELAY_SECONDS)

            redo = worker.run(
                task,
                context
                + tool_context
                + "\nFeedback do reviewer: "
                + rev.output,
            )

            if not redo.success:
                agent_name = getattr(worker, "name", "worker")
                steps.append(
                    Step(
                        agent_name,
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
        # LIMITE DE RETRIES ATINGIDO
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