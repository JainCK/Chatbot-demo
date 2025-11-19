from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END
from core.persona import get_system_prompt
from core.llm import generate_stream

class ChatState(TypedDict):
    messages: List[dict]
    persona: str
    session_id: str

def inject_persona(state: ChatState):
    """Injects the system prompt based on the persona."""
    system_prompt = get_system_prompt(state["persona"])
    # Check if system prompt is already the first message
    if not state["messages"] or state["messages"][0].get("role") != "system":
        state["messages"].insert(0, {"role": "system", "content": system_prompt})
    else:
        # Update existing system prompt if needed
        state["messages"][0]["content"] = system_prompt
    return state

def generate_response(state: ChatState):
    """
    This node is a placeholder in the graph. 
    The actual streaming happens in the API endpoint using the generator.
    However, for the graph structure, we define the flow.
    """
    # In a full LangGraph execution, we might invoke the LLM here.
    # For streaming via FastAPI, we might use the graph to prepare state 
    # and then stream the result of the last node.
    pass

# Define the graph
workflow = StateGraph(ChatState)

workflow.add_node("inject_persona", inject_persona)
# workflow.add_node("generate", generate_response) # Not strictly needed if we stream manually after state prep

workflow.set_entry_point("inject_persona")
workflow.add_edge("inject_persona", END)

app = workflow.compile()

def prepare_chat_state(message: str, session_id: str, persona: str, history: list = []) -> list:
    """
    Runs the graph to prepare the messages for the LLM.
    """
    initial_state = {
        "messages": history + [{"role": "user", "content": message}],
        "persona": persona,
        "session_id": session_id
    }
    
    result = app.invoke(initial_state)
    return result["messages"]
