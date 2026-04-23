# agent/graph.py
# =============================================================================
# Assembles all nodes into the compiled LangGraph StateGraph.
#
# Flow:
#   START → planner → researcher → writer → executor → critic
#                                     ↑                   |
#                                     └──── retry ─────────┘
#                                                          |
#                                                     (success)
#                                                          ↓
#                                                     finalizer → END
# =============================================================================

from functools import partial

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    AgentState,
    node_critic,
    node_executor,
    node_finalizer,
    node_planner,
    node_researcher,
    node_writer,
    route_after_critic,
)
from sandbx.docker_runner import DockerSandbox


def build_graph(sandbox: DockerSandbox):
    """
    Build and compile the LangGraph StateGraph.

    node_executor needs the sandbox object (to run Docker commands).
    We use functools.partial to bind it without making sandbox a global.
    """
    executor_node = partial(node_executor, sandbox=sandbox)

    graph = StateGraph(AgentState)

    graph.add_node("planner",    node_planner)
    graph.add_node("researcher", node_researcher)
    graph.add_node("writer",     node_writer)
    graph.add_node("executor",   executor_node)
    graph.add_node("critic",     node_critic)
    graph.add_node("finalizer",  node_finalizer)

    graph.add_edge(START,        "planner")
    graph.add_edge("planner",    "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer",     "executor")
    graph.add_edge("executor",   "critic")

    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "node_writer"   : "writer",
            "node_finalizer": "finalizer",
        },
    )

    graph.add_edge("finalizer", END)

    return graph.compile()


def run_agent(user_request: str, workspace_path: str, sandbox: DockerSandbox) -> str:
    """
    Initialise state, build the graph, stream execution node by node.
    Returns the final_answer string.
    """
    graph = build_graph(sandbox)

    initial_state: AgentState = {
        "user_request": user_request,
        "workspace"   : workspace_path,
        "plan"        : "",
        "context"     : "",
        "code_action" : "",
        "last_result" : "",
        "status"      : "running",
        "retry_count" : 0,
        "messages"    : [HumanMessage(content=user_request)],
        "final_answer": "",
    }

    # stream() lets us see each node's output as it happens.
    # recursion_limit guards against infinite retry loops at the graph level.
    final_state = None
    for chunk in graph.stream(initial_state, {"recursion_limit": 60}):
        final_state = chunk

    if final_state:
        last_node_output = list(final_state.values())[-1]
        return last_node_output.get("final_answer", "Task completed.")

    return "No output produced."