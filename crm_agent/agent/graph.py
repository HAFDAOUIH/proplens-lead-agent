import os
import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from crm_agent.agent.state import AgentState, Route
from crm_agent.agent.router import RouterLLM
from crm_agent.agent.vanna_client import VannaClient
from crm_agent.agent.sql_executor import SQLExecutor
from crm_agent.agent.tools_rag import RagTool


CHROMA_DIR = os.getenv("CHROMA_DIR", "/home/hafdaoui/Documents/Proplens/crm_agent/data/chroma")

router = RouterLLM()
rag_tool = RagTool(chroma_dir=CHROMA_DIR)
executor = SQLExecutor()


def node_route(state: AgentState) -> AgentState:
    # Pass conversation history to router for context-aware routing
    decision = router.classify(state.query, history=state.history)
    state.route = Route(decision.route)
    state.confidence = decision.confidence
    state.intent = decision.reasons
    return state


def node_t2sql(state: AgentState) -> AgentState:
    vc = VannaClient(chroma_dir=CHROMA_DIR)
    result = vc.ask(state.query)
    if result["error"]:
        state.error = result["error"]
        return state
    exec_res = executor.execute(result["sql"])
    if exec_res["error"]:
        state.error = exec_res["error"]
        state.sql = result["sql"]
        return state
    state.sql = result["sql"]
    state.rows = exec_res["rows"]
    state.columns = exec_res["columns"]
    return state


def node_rag(state: AgentState) -> AgentState:
    res = rag_tool.answer(state.query, k=4)
    state.answer = res["answer"]
    state.sources = res["sources"]
    return state


def node_clarify(state: AgentState) -> AgentState:
    """Handle low-confidence routing by asking for clarification."""
    # Detect if this is likely a follow-up question (short, vague queries)
    query_words = state.query.strip().split()
    is_short_query = len(query_words) <= 5
    is_vague = any(word.lower() in ["that", "this", "it", "more", "else", "one", "them"]
                   for word in query_words)

    base_message = (
        "I'm not quite sure how to best answer your question. "
        "Could you clarify if you're asking about:\n"
        "- Property information (amenities, features, floor plans)\n"
        "- Lead analytics (counts, statistics, status breakdowns)"
    )

    # Add context hint for likely follow-up questions
    if is_short_query and is_vague:
        hint = (
            "\n\n💡 Tip: If you're asking a follow-up question, please include more context "
            "or reference what you're asking about. For example:\n"
            "  • 'Tell me more about Beachgate amenities'\n"
            "  • 'What about DLF West Park pricing?'\n"
            "  • 'Show me connected leads instead'"
        )
        state.answer = base_message + hint
    else:
        state.answer = base_message

    return state


def choose_next(state: AgentState) -> str:
    """Route based on classification and confidence."""
    # If confidence is too low, ask for clarification
    if state.confidence and state.confidence < 0.6:
        return "clarify"

    if state.route == Route.rag:
        return "rag"
    if state.route == Route.t2sql:
        return "t2sql"
    if state.route == Route.clarify:
        return "clarify"

    # Default to RAG for unknown routes
    return "rag"


def build_graph(sqlite_path: str = "/home/hafdaoui/Documents/Proplens/crm_agent/data/graph.sqlite3"):
    sg = StateGraph(AgentState)
    sg.add_node("route", node_route)
    sg.add_node("t2sql", node_t2sql)
    sg.add_node("rag", node_rag)
    sg.add_node("clarify", node_clarify)
    sg.set_entry_point("route")
    sg.add_conditional_edges("route", choose_next, {"rag": "rag", "t2sql": "t2sql", "clarify": "clarify"})
    sg.add_edge("rag", END)
    sg.add_edge("t2sql", END)
    sg.add_edge("clarify", END)

    # Create SQLite connection for checkpointer (required for langgraph v1.0+)
    # check_same_thread=False allows usage across multiple requests
    conn = sqlite3.connect(sqlite_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    return sg.compile(checkpointer=checkpointer)


