from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.graph.state import AgentState
from app.graph.nodes import call_model, tool_node

DB_PATH = "checkpoints.sqlite"

class FinancialGraphManager:
    def __init__(self):
        self.graph = None
        self.saver = None

    async def initialize(self):
        """Inicializa el saver y compila el grafo una sola vez."""
        if self.graph is None:
            # 1. Creamos el saver asíncrono
            self.saver = AsyncSqliteSaver.from_conn_string(DB_PATH)
            # Entramos al contexto manualmente para mantenerlo abierto
            checkpointer = await self.saver.__aenter__()

            # 2. Construcción del Workflow
            workflow = StateGraph(AgentState)
            workflow.add_node("agent", call_model)
            workflow.add_node("tools", tool_node)
            workflow.set_entry_point("agent")

            workflow.add_conditional_edges("agent", self.should_continue)
            workflow.add_edge("tools", "agent")

            # 3. Compilación con el checkpointer persistente
            # Nota: Usamos interrupt_after=["agent"] para capturar la respuesta del analista
            self.graph = workflow.compile(
                checkpointer=checkpointer,
                interrupt_after=["agent"]
            )
        return self.graph

    def should_continue(self, state):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    async def close(self):
        """Cierra la conexión a la DB al apagar la app."""
        if self.saver:
            await self.saver.__aexit__(None, None, None)

# Instanciamos el Manager (pero no el grafo todavía)
graph_manager = FinancialGraphManager()