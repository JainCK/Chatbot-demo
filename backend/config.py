import os
from dotenv import load_dotenv

load_dotenv()

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

if not HUGGINGFACE_API_KEY:
    print("Warning: HUGGINGFACE_API_KEY is not set.")
