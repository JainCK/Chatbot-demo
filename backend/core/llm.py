from huggingface_hub import AsyncInferenceClient
from config import HUGGINGFACE_API_KEY, HF_MODEL_ID
from typing import AsyncGenerator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the client
client = AsyncInferenceClient(token=HUGGINGFACE_API_KEY)
MODEL_ID = HF_MODEL_ID

async def generate_stream(messages: list) -> AsyncGenerator[str, None]:
    """
    Generates a streaming response from the LLM.
    """
    try:
        logger.info(f"Sending request to HF Inference API for model {MODEL_ID}")
        logger.debug(f"Messages: {messages}")
        
        stream = await client.chat_completion(
            model=MODEL_ID,
            messages=messages,
            max_tokens=500,
            stream=True
        )
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                # logger.debug(f"Yielding chunk: {content}")
                yield content
    except Exception as e:
        logger.error(f"Error in generate_stream: {str(e)}")
        yield f"Error: {str(e)}"
