from ninja import Router
from pydantic import BaseModel
from crm_agent.agent.graph import build_graph
from crm_agent.agent.state import AgentState
import uuid


router = Router(tags=["agent"])
graph = build_graph()


class AgentQuery(BaseModel):
    """Agent query request with conversation tracking."""
    question: str
    thread_id: str | None = None

    class Config:
        schema_extra = {
            "example": {
                "question": "What amenities does Beachgate by Address have?",
                "thread_id": "optional-thread-id-for-conversation-continuity"
            }
        }


@router.post("/agent/query", summary="Query AI Agent", description="""
Query the intelligent agent router that automatically routes your question to the appropriate tool:

- **RAG Route**: Property-related questions (amenities, location, units, etc.)
- **T2SQL Route**: Analytics and database queries (counts, lists, statistics)
- **Clarify Route**: Ambiguous queries that need clarification

The agent maintains conversation history using thread_id for follow-up questions.

**Examples:**

*Property Question (RAG):*
```json
{
  "question": "What amenities does Beachgate have?"
}
```

*Analytics Question (T2SQL):*
```json
{
  "question": "How many Connected leads do we have?"
}
```

*Follow-up Question:*
```json
{
  "question": "Tell me more about the first one",
  "thread_id": "previous-thread-id"
}
```

**Response includes:**
- `route`: Which tool was used (rag/t2sql/clarify)
- `answer`: The generated answer
- `sources`: (RAG only) Source documents with metadata
- `sql`, `rows`, `columns`: (T2SQL only) Query and results
- `confidence`: Routing confidence score
- `thread_id`: Use this for follow-up questions
""")
def agent_query(request, payload: AgentQuery):
    # Generate thread_id if not provided (for conversation tracking)
    thread_id = payload.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Retrieve conversation history from checkpointer if thread_id is provided
    history = []
    if payload.thread_id:
        try:
            # Get previous state from checkpointer
            checkpoint = graph.checkpointer.get_tuple(config)
            if checkpoint and checkpoint.checkpoint:
                # Extract query history from previous states
                prev_state = checkpoint.checkpoint.get("channel_values", {})
                if prev_state and isinstance(prev_state, dict):
                    # Keep last 3 queries for context
                    if "history" in prev_state and prev_state["history"]:
                        history = prev_state["history"][-3:]
                    # Add previous query to history
                    if "query" in prev_state and prev_state["query"]:
                        history.append(prev_state["query"])
                        history = history[-3:]  # Keep only last 3
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not retrieve conversation history: {str(e)}")

    # Create state with current query and history
    state = AgentState(query=payload.question, history=history if history else None)

    # Invoke graph with config containing thread_id
    result = graph.invoke(state, config=config)

    # Add thread_id to response for client to use in follow-up queries
    response = result if isinstance(result, dict) else result.dict()
    response["thread_id"] = thread_id

    return response


