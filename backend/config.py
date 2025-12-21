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
COUNCIL_MODELS = [
    "openai/gpt-4-turbo",
    "google/gemini-pro",
    "anthropic/claude-3-opus",
    "mistral/mistral-large",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "openai/gpt-4-turbo"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
