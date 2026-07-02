from typing import AsyncGenerator
import asyncio

from app.agents.planner_agent import PlannerAgent
from app.agents.coder_agent import CoderAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.tester_agent import TesterAgent
from app.agents.documenter_agent import DocumenterAgent
from app.services.llm_client import get_llm_client
from app.services.session_manager import get_session_manager
from app.schemas.models import AgentMessage, AgentName, SessionStatus
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger("codecrew.orchestrator")


class Orchestrator:
    """
    The Orchestrator — coordinates all 5 agents in the pipeline.

    Pipeline:
    1. Planner → creates technical plan
    2. Coder → writes code from plan
    3. Reviewer → reviews code (may reject and loop back to Coder)
    4. Tester → writes tests for approved code
    5. Documenter → writes documentation

    The Coder-Reviewer loop is the key innovation:
    - If Reviewer rejects → Coder fixes → Reviewer reviews again
    - This continues until approved OR max iterations reached
    - Max iterations prevents infinite loops

    Design decision: Orchestrator is stateless — all state lives in
    the session. This means the orchestrator can be restarted without
    losing session data.
    """

    def __init__(self):
        settings = get_settings()
        llm = get_llm_client()
        self.session_manager = get_session_manager()
        self.max_iterations = settings.MAX_REVIEW_ITERATIONS

        # Initialize all agents with shared LLM client
        self.planner = PlannerAgent(llm)
        self.coder = CoderAgent(llm)
        self.reviewer = ReviewerAgent(llm)
        self.tester = TesterAgent(llm)
        self.documenter = DocumenterAgent(llm)

        logger.info("Orchestrator ready — all 5 agents initialized")

    async def run(self, session_id: str, context: dict) -> AsyncGenerator[dict, None]:
        """
        Run the complete agent pipeline and yield events for SSE streaming.

        Each yield is a dict that gets sent to the frontend in real-time.
        This lets users watch the agents work live.
        """
        sm = self.session_manager
        sm.update_status(session_id, SessionStatus.RUNNING)

        try:
            # ── Step 1: Planner ──────────────────────────────────────────
            yield self._event("agent_start", AgentName.PLANNER, "Analyzing requirements and creating technical plan...")

            planner_output = await asyncio.to_thread(
                self.planner.run, context
            )
            context["planner_output"] = planner_output
            sm.save_agent_output(session_id, "planner", planner_output)

            plan_summary = f"Created {len(planner_output['plan'])} step plan. Complexity: {planner_output['estimated_complexity']}"
            yield self._event("agent_done", AgentName.PLANNER, plan_summary, data=planner_output)
            self._log_message(session_id, AgentName.PLANNER, "output", plan_summary)

            # ── Step 2-3: Coder ↔ Reviewer Loop ─────────────────────────
            initial_score = 0
            final_score = 0

            for round_num in range(1, self.max_iterations + 1):
                context["current_round"] = round_num

                # Coder writes/fixes code
                if round_num == 1:
                    yield self._event("agent_start", AgentName.CODER, f"Writing code (Round {round_num})...")
                else:
                    yield self._event("agent_start", AgentName.CODER, f"Fixing issues from reviewer feedback (Round {round_num})...")

                coder_output = await asyncio.to_thread(
                    self.coder.run, context
                )
                context["coder_output"] = coder_output
                sm.save_agent_output(session_id, "coder", coder_output)

                files_written = len(coder_output["files"])
                yield self._event("agent_done", AgentName.CODER, f"Wrote {files_written} file(s)", data=coder_output)
                self._log_message(session_id, AgentName.CODER, "output", f"Round {round_num}: Wrote {files_written} files")

                # Reviewer reviews
                yield self._event("agent_start", AgentName.REVIEWER, f"Reviewing code quality (Round {round_num})...")

                reviewer_output = await asyncio.to_thread(
                    self.reviewer.run, context
                )
                context["reviewer_output"] = reviewer_output
                sm.save_agent_output(session_id, "reviewer", reviewer_output)

                score = reviewer_output["overall_quality_score"]
                approved = reviewer_output["approved"]
                issues_count = len(reviewer_output["issues"])

                if round_num == 1:
                    initial_score = score

                if approved:
                    final_score = score
                    yield self._event(
                        "agent_done", AgentName.REVIEWER,
                        f"✅ APPROVED — Quality score: {score}/100",
                        data=reviewer_output
                    )
                    self._log_message(session_id, AgentName.REVIEWER, "output", f"Approved with score {score}")
                    sm.update_scores(session_id, initial=initial_score, final=final_score, rounds=round_num)
                    break
                else:
                    yield self._event(
                        "agent_done", AgentName.REVIEWER,
                        f"❌ REJECTED — Score: {score}/100 — {issues_count} issues found. Sending back to Coder...",
                        data=reviewer_output
                    )
                    self._log_message(session_id, AgentName.REVIEWER, "rejection", f"Rejected round {round_num}: {issues_count} issues")

                    if round_num == self.max_iterations:
                        # Max iterations reached — use best code so far
                        final_score = score
                        logger.warning(f"Max iterations ({self.max_iterations}) reached for session {session_id}")
                        yield self._event("system", AgentName.REVIEWER, f"Max review rounds reached. Proceeding with best code (score: {score}/100).")
                        sm.update_scores(session_id, initial=initial_score, final=final_score, rounds=round_num)

            # ── Step 4: Tester ───────────────────────────────────────────
            yield self._event("agent_start", AgentName.TESTER, "Writing comprehensive unit tests...")

            tester_output = await asyncio.to_thread(
                self.tester.run, context
            )
            context["tester_output"] = tester_output
            sm.save_agent_output(session_id, "tester", tester_output)

            tests_count = len(tester_output["test_cases"])
            yield self._event("agent_done", AgentName.TESTER, f"Written {tests_count} test cases", data=tester_output)
            self._log_message(session_id, AgentName.TESTER, "output", f"Wrote {tests_count} test cases")

            # ── Step 5: Documenter ───────────────────────────────────────
            yield self._event("agent_start", AgentName.DOCUMENTER, "Writing documentation...")

            documenter_output = await asyncio.to_thread(
                self.documenter.run, context
            )
            context["documenter_output"] = documenter_output
            sm.save_agent_output(session_id, "documenter", documenter_output)

            yield self._event("agent_done", AgentName.DOCUMENTER, "Documentation complete", data=documenter_output)
            self._log_message(session_id, AgentName.DOCUMENTER, "output", "Documentation written")

            # ── Complete ─────────────────────────────────────────────────
            sm.update_status(session_id, SessionStatus.COMPLETED)
            yield self._event("completed", AgentName.DOCUMENTER, "All agents completed successfully!", data={
                "session_id": session_id,
                "initial_quality_score": initial_score,
                "final_quality_score": final_score,
                "total_review_rounds": context.get("current_round", 1),
            })

            logger.info(f"Session {session_id} completed — score improved {initial_score} → {final_score}")

        except Exception as e:
            logger.error(f"Session {session_id} failed: {e}")
            sm.update_status(session_id, SessionStatus.FAILED)
            yield self._event("error", AgentName.PLANNER, f"Pipeline failed: {str(e)}")

    def _event(self, event_type: str, agent: AgentName, message: str, data: dict = None) -> dict:
        """Create a structured SSE event."""
        return {
            "event_type": event_type,
            "agent": agent.value,
            "message": message,
            "data": data or {},
        }

    def _log_message(self, session_id: str, agent: AgentName, msg_type: str, content: str, round_num: int = 1):
        """Save agent message to session log."""
        msg = AgentMessage(
            agent=agent,
            message_type=msg_type,
            content=content,
            round_number=round_num,
        )
        self.session_manager.add_message(session_id, msg)
