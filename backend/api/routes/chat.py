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

    # Check Cache
    from core.cache_service import semantic_search, cache_response
    cached_response = await semantic_search(request.message)
    
    if cached_response:
        # Return cached response as a stream (simulated)
        async def stream_cached():
            yield cached_response
            # Add to history
            add_message_to_history(request.session_id, "assistant", cached_response)
            
        return StreamingResponse(
            stream_cached(),
            media_type="text/event-stream"
        )

    # Generate the stream and save assistant response (this is tricky with streaming)
    # For a simple prototype, we might need to aggregate the stream to save it, 
    # or use a callback. For now, we will stream and let the client handle display,
    # but to save to memory, we need to capture the full response.
    # A common pattern is to use a generator wrapper.
    
    async def stream_with_memory():
        full_response = ""
        async for chunk in generate_stream(messages):
            full_response += chunk
            yield chunk
        # Save assistant message after streaming is complete
        add_message_to_history(request.session_id, "assistant", full_response)
        # Save to cache
        await cache_response(request.message, full_response)

    return StreamingResponse(
        stream_with_memory(),
        media_type="text/event-stream"
    )
