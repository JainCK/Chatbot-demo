import redis
import json
from config import REDIS_URL
from typing import List, Dict

# Initialize Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_chat_history(session_id: str, limit: int = 6) -> List[Dict]:
    """
    Retrieves chat history from Redis.
    """
    key = f"chat:{session_id}"
    # Get all messages
    messages = redis_client.lrange(key, 0, -1)
    parsed_messages = [json.loads(m) for m in messages]
    return parsed_messages

def add_message_to_history(session_id: str, role: str, content: str):
    """
    Adds a message to the Redis list with Pinned Window logic.
    Index 0 is ALWAYS the System Prompt.
    """
    key = f"chat:{session_id}"
    message = {"role": role, "content": content}
    
    # Append new message
    redis_client.rpush(key, json.dumps(message))
    
    # Check length and enforce pinned window
    # We want System Prompt (idx 0) + 6 turns (user/ai pairs) = 1 + 12 messages max? 
    # User request says "Limit: 6 Messages (Context Window)". 
    # "If len(history) > 7 (System + 6 turns)" -> This implies 7 messages total (1 system + 6 others).
    # Let's follow the "If len(history) > 7: Remove Index 1" rule.
    
    list_len = redis_client.llen(key)
    if list_len > 7:
        # Remove the element at index 1 (the oldest non-system message)
        # LREM is by value, so we need to read it first or use LPOP/LTRIM tricks.
        # Redis lists don't support "remove at index" natively easily without Lua or LSET/LREM.
        # Easier approach: Read all, modify list, rewrite? No, race conditions.
        # Better approach: LTRIM? No, LTRIM removes from ends.
        # We want to keep Index 0, remove Index 1. 
        # We can rotate? No.
        # We can use a Lua script or just read-modify-write for this prototype.
        # Or simpler: Since we are appending, we can just pop the second element?
        # Actually, `lpop` removes head (index 0). We want to keep index 0.
        # So we can: 
        # 1. Get index 0 (System)
        # 2. LPOP (removes System)
        # 3. LPOP (removes Oldest Message)
        # 4. LPUSH System back.
        
        # Let's do the safe way:
        system_prompt = redis_client.lindex(key, 0)
        # Remove first two elements (System + Oldest)
        redis_client.lpop(key) # Pop System
        redis_client.lpop(key) # Pop Oldest Message
        # Push System back
        redis_client.lpush(key, system_prompt)
        
    # Set expiry to 24 hours
    redis_client.expire(key, 86400)
