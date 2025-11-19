import json
import numpy as np
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer
from fastapi.concurrency import run_in_threadpool
from config import REDIS_URL
import redis
import logging

logger = logging.getLogger(__name__)

# Initialize Redis
redis_client = redis.from_url(REDIS_URL, decode_responses=False) # Need bytes for vectors? No, redis-py handles it usually or we send bytes.
# Actually for RediSearch we usually use the 'redis' lib but with specific commands.
# The standard redis-py client supports modules now.

# Initialize Embedding Model
# Run this once at startup
model = SentenceTransformer('all-MiniLM-L6-v2')

INDEX_NAME = "response_cache"
VECTOR_DIM = 384

def create_index():
    """Creates the RediSearch index if it doesn't exist."""
    try:
        redis_client.ft(INDEX_NAME).info()
        logger.info("Index already exists.")
    except:
        logger.info("Creating index...")
        # Define schema
        from redis.commands.search.field import VectorField, TextField
        from redis.commands.search.index_definition import IndexDefinition, IndexType

        schema = (
            TextField("response"),
            VectorField("vector",
                "FLAT", {
                    "TYPE": "FLOAT32",
                    "DIM": VECTOR_DIM,
                    "DISTANCE_METRIC": "COSINE"
                }
            )
        )
        redis_client.ft(INDEX_NAME).create_index(
            schema,
            definition=IndexDefinition(prefix=["cache:"], index_type=IndexType.HASH)
        )

async def get_embedding(text: str) -> np.ndarray:
    """Generates embedding in a threadpool to avoid blocking."""
    return await run_in_threadpool(model.encode, text)

async def semantic_search(text: str, threshold: float = 0.90):
    """
    Searches for a similar query in the cache.
    """
    embedding = await get_embedding(text)
    embedding_bytes = embedding.astype(np.float32).tobytes()

    q = Query(f"*=>[KN 1 @vector $vec AS score]")\
        .sort_by("score")\
        .return_fields("response", "score")\
        .dialect(2)
    
    params = {"vec": embedding_bytes}
    
    try:
        results = redis_client.ft(INDEX_NAME).search(q, query_params=params)
        if results.total > 0:
            doc = results.docs[0]
            score = 1 - float(doc.score) # RediSearch returns distance (1 - cosine) usually? 
            # Wait, DISTANCE_METRIC: COSINE. 
            # If using KN (K-Nearest), the score returned is the distance.
            # Cosine distance = 1 - Cosine Similarity.
            # So Similarity = 1 - Distance.
            # If distance is small, similarity is high.
            # Threshold 0.90 similarity means Distance <= 0.10.
            
            distance = float(doc.score)
            similarity = 1 - distance
            
            logger.info(f"Cache search: Distance={distance}, Similarity={similarity}")
            
            if similarity >= threshold:
                return doc.response
    except Exception as e:
        logger.error(f"Cache search error: {e}")
        
    return None

async def cache_response(query: str, response: str):
    """Saves the query vector and response to Redis."""
    try:
        embedding = await get_embedding(query)
        embedding_bytes = embedding.astype(np.float32).tobytes()
        
        key = f"cache:{hash(query)}"
        redis_client.hset(key, mapping={
            "vector": embedding_bytes,
            "response": response
        })
        # Set expiry (e.g., 1 hour)
        redis_client.expire(key, 3600)
    except Exception as e:
        logger.error(f"Cache save error: {e}")
