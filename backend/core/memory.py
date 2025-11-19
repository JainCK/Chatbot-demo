import redis
import json
from config import REDIS_URL
from typing import List, Dict

# Initialize Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_chat_history(session_id: str, limit: int = 6) -> List[Dict]:
    """
    Retrieves chat history from Redis.
    Limits to the last `limit` turns (user + assistant pairs).
    """
    key = f"chat:{session_id}"
    # Get all messages
    messages = redis_client.lrange(key, 0, -1)
    parsed_messages = [json.loads(m) for m in messages]
    
    # Limit context window (e.g., last 6 messages)
    return parsed_messages[-limit:]

def add_message_to_history(session_id: str, role: str, content: str):
    """
    Adds a message to the Redis list.
    """
    key = f"chat:{session_id}"
    message = {"role": role, "content": content}
    redis_client.rpush(key, json.dumps(message))
    # Set expiry to 24 hours
    redis_client.expire(key, 86400)
