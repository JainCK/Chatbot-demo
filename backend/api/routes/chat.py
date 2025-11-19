from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest
from core.orchestrator import prepare_chat_state
from core.llm import generate_stream

router = APIRouter()

@router.post("/message")
async def chat_message(request: ChatRequest):
    """
    Endpoint to handle chat messages.
    Returns a streaming response.
    """
    # Retrieve history from Redis
    from core.memory import get_chat_history, add_message_to_history
    history = get_chat_history(request.session_id)
    
    # Prepare the messages using the orchestrator (injects persona)
    messages = prepare_chat_state(
        message=request.message,
        session_id=request.session_id,
        persona=request.persona,
        history=history
    )
    
    # Add user message to history
    add_message_to_history(request.session_id, "user", request.message)

    # Generate the stream and save assistant response (this is tricky with streaming)
    # For a simple prototype, we might need to aggregate the stream to save it, 
    # or use a callback. For now, we will stream and let the client handle display,
    # but to save to memory, we need to capture the full response.
    # A common pattern is to use a generator wrapper.
    
    async def stream_with_memory():
        full_response = ""
        for chunk in generate_stream(messages):
            full_response += chunk
            yield chunk
        # Save assistant message after streaming is complete
        add_message_to_history(request.session_id, "assistant", full_response)

    return StreamingResponse(
        stream_with_memory(),
        media_type="text/event-stream"
    )
