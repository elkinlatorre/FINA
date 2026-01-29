from langchain_core.messages import AIMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph

from app.core.config import RISK_FINANCIAL_KEYWORDS, SENSITIVE_FINANCIAL_KEYWORDS
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
            self.saver = AsyncSqliteSaver.from_conn_string(settings.DB_PATH)
            checkpointer = await self.saver.__aenter__()

            workflow = StateGraph(AgentState)

            # Nodes
            workflow.add_node("agent", call_model)
            workflow.add_node("tools", tool_node)
            workflow.add_node("human_review_gate", self.gatekeeper_node)

            workflow.set_entry_point("agent")

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
                    "end": END
                }
            )

            workflow.add_edge("tools", "agent")
            workflow.add_edge("human_review_gate", END)

            # Only interrupt when the gatekeeper node is reached
            self.graph = workflow.compile(
                checkpointer=checkpointer,
                interrupt_before=["human_review_gate"]
            )
        return self.graph

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
        # Palabras de alto riesgo (disparan revisión inmediata)
        high_risk_words = RISK_FINANCIAL_KEYWORDS
        # Palabras de riesgo moderado (necesitan al menos 2 para disparar)
        moderate_risk_words = SENSITIVE_FINANCIAL_KEYWORDS  # Las que ya tenemos en config.py

        triggered_high = [word for word in high_risk_words if f" {word} " in f" {content_lower} "]
        triggered_moderate = [word for word in moderate_risk_words if f" {word} " in f" {content_lower} "]

        # Lógica de Umbral:
        # - Si hay una palabra de ALTO riesgo -> Review.
        # - Si hay 2 o más palabras de riesgo moderado -> Review.
        risk_score = (len(triggered_high) * settings.HIGH_RISK_MULTIPLIER) + len(triggered_moderate)

        if risk_score >= settings.RISK_SCORE_THRESHOLD:
            logger.info(
                f"🚨 BREAKPOINT TRIGGERED [Thread: {state.get('thread_id', 'N/A')}]\n"
                f"Reason: High risk score ({risk_score})\n"
                f"Keywords found: {triggered_high + triggered_moderate}"
            )
            return "review"

        # 3. Flujo Directo (Informacional)
        logger.info(f"✅ DIRECT RESPONSE: Risk score ({risk_score}) below threshold.")
        return "end"

    async def close(self):
        """Closes the DB connection on app shutdown."""
        if self.saver:
            await self.saver.__aexit__(None, None, None)


# Singleton Instance
graph_manager = FinancialGraphManager()