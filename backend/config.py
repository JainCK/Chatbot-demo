import os
from dotenv import load_dotenv

load_dotenv()

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "google/gemma-2-9b-it")

if not HUGGINGFACE_API_KEY:
    print("Warning: HUGGINGFACE_API_KEY is not set.")
