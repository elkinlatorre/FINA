from langchain_core.messages import AIMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph

from app.core.logger import get_logger
from app.core.settings import settings
from app.graph.nodes import call_model, tool_node
from app.graph.state import AgentState

logger = get_logger("BUILDER_WORKFLOW")


class FinancialGraphManager:
    def __init__(self):
        self.graph = None
        self.saver = None

    async def initialize(self):
        """
        Initializes the saver and compiles the graph with autonomous
        investigation logic and a conditional human gatekeeper.
        """
        if self.graph is None:
            self.saver = AsyncSqliteSaver.from_conn_string(settings.CHECKPOINT_DB_PATH)
            checkpointer = await self.saver.__aenter__()

            from app.graph.guardrails import input_guardrail, output_guardrail
            
            workflow = StateGraph(AgentState)

            # Nodes
            workflow.add_node("guardrail_input", input_guardrail)
            workflow.add_node("agent", call_model)
            workflow.add_node("tools", tool_node)
            workflow.add_node("human_review_gate", self.gatekeeper_node)
            workflow.add_node("guardrail_output", output_guardrail)

            workflow.set_entry_point("guardrail_input")

            # Routing from Guardrail
            workflow.add_conditional_edges(
                "guardrail_input",
                self.check_safety,
                {
                    "continue": "agent",
                    "block": END
                }
            )

            # Updated Conditional Routing:
            # - 'tools': Agent keeps investigating.
            # - 'review': Final answer needs human sign-off.
            # - END: Safe informational answer goes directly to user.
            workflow.add_conditional_edges(
                "agent",
                self.should_continue,
                {
                    "tools": "tools",
                    "review": "human_review_gate",
                    "end": "guardrail_output"
                }
            )

            workflow.add_edge("tools", "agent")
            workflow.add_edge("human_review_gate", "guardrail_output")
            workflow.add_edge("guardrail_output", END)

            # Only interrupt when the gatekeeper node is reached
            self.graph = workflow.compile(
                checkpointer=checkpointer,
                interrupt_before=["human_review_gate"]
            )
        return self.graph

    def check_safety(self, state: AgentState):
        """
        Decision node for the input guardrail.
        """
        safety = state.get("safety_metadata", {})
        if safety.get("is_safe", True):
            return "continue"
        
        logger.warning(f"🛡️ GUARDRAIL BLOCK: {safety.get('reason')}")
        return "block"

    async def gatekeeper_node(self, state: AgentState):
        """
        Hold the state for human supervision only when sensitive data is detected.
        """
        return state

    def should_continue(self, state):
        """
        Analyzes the agent's intention. If it's a financial recommendation,
        it forces a human review. If it's just information, it ends the flow.
        """
        messages = state["messages"]
        last_message = messages[-1]

        # 1. Autonomous Investigation Layer
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"

        # 2. Risk Evaluation Layer
        # Check if any sensitive keyword exists in the agent's final response
        content_lower = last_message.content.lower()
        high_risk_words = settings.RISK_FINANCIAL_KEYWORDS
        moderate_risk_words = settings.SENSITIVE_FINANCIAL_KEYWORDS

        triggered_high = [word for word in high_risk_words if f" {word} " in f" {content_lower} "]
        triggered_moderate = [word for word in moderate_risk_words if f" {word} " in f" {content_lower} "]

        risk_score = (len(triggered_high) * settings.HIGH_RISK_MULTIPLIER) + len(triggered_moderate)

        if risk_score >= settings.RISK_SCORE_THRESHOLD:
            logger.info(
                f"🚨 BREAKPOINT TRIGGERED [Thread: {state.get('thread_id', 'N/A')}]\n"
                f"Reason: High risk score ({risk_score})\n"
                f"Keywords found: {triggered_high + triggered_moderate}"
            )
            return "review"

        logger.info(f"✅ DIRECT RESPONSE: Risk score ({risk_score}) below threshold.")
        return "end"

    async def close(self):
        """Closes the DB connection on app shutdown."""
        if self.saver:
            await self.saver.__aexit__(None, None, None)


# Singleton Instance
graph_manager = FinancialGraphManager()