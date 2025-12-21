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
# Using only free models
COUNCIL_MODELS = [
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "nousresearch/hermes-3-llama-3.1-405b:free"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
