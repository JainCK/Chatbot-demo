from huggingface_hub import InferenceClient
from config import HUGGINGFACE_API_KEY
from typing import Generator

# Initialize the client
client = InferenceClient(token=HUGGINGFACE_API_KEY)
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"

def generate_stream(messages: list) -> Generator[str, None, None]:
    """
    Generates a streaming response from the LLM.
    """
    try:
        stream = client.chat_completion(
            model=MODEL_ID,
            messages=messages,
            max_tokens=500,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except Exception as e:
        yield f"Error: {str(e)}"
