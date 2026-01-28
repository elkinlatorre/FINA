from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes import call_model, tool_node


def should_continue(state):
    """
    Conditional edge: determines if the model wants to call a tool
    or if it has finished the reasoning process.
    """
    messages = state["messages"]
    last_message = messages[-1]

    # If there are tool calls in the message, we continue to the tools node
    if last_message.tool_calls:
        return "tools"

    # Otherwise, we stop and return the final answer to the user
    return END


def create_financial_graph():
    """
    Builds the ReAct graph for the financial agent.
    """
    # 1. Initialize the graph with our state definition
    workflow = StateGraph(AgentState)

    # 2. Define the nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    # 3. Set the entry point
    workflow.set_entry_point("agent")

    # 4. Define the edges
    # After the agent speaks, we decide if we continue or stop
    workflow.add_conditional_edges(
        "agent",
        should_continue,
    )

    # After tools execute, we always go back to the agent to analyze the observation
    workflow.add_edge("tools", "agent")

    # 5. Compile the graph
    return workflow.compile()


# Singleton instance of the graph
financial_advisor_graph = create_financial_graph()