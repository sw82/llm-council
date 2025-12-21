"""Configuration for the LLM Council."""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, assume env vars are set
    pass

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
# Using free/cheaper models
COUNCIL_MODELS = [
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen-2-7b-instruct:free",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "google/gemini-flash-1.5"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
