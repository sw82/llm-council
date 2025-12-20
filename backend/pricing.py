"""Pricing logic for OpenRouter models."""

import httpx
import time
import logging

logger = logging.getLogger("llm_council")

# Cache pricing data to avoid spamming the API
_PRICING_CACHE = {
    "data": [],
    "timestamp": 0
}
_CACHE_TTL = 3600  # 1 hour


async def fetch_openrouter_models():
    """
    Fetch available models and their pricing from OpenRouter.
    Returns a list of model dicts.
    """
    global _PRICING_CACHE
    
    current_time = time.time()
    
    # Return cached data if valid
    if _PRICING_CACHE["data"] and (current_time - _PRICING_CACHE["timestamp"] < _CACHE_TTL):
        return _PRICING_CACHE["data"]
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://openrouter.ai/api/v1/models")
            response.raise_for_status()
            
            data = response.json().get("data", [])
            
            # Update cache
            _PRICING_CACHE = {
                "data": data,
                "timestamp": current_time
            }
            
            return data
            
    except Exception as e:
        logger.error(f"Failed to fetch OpenRouter models: {e}")
        # Return stale cache if available, otherwise empty list
        return _PRICING_CACHE["data"]


async def get_model_price(model_id: str):
    """
    Get pricing for a specific model.
    Returns tuple (prompt_price, completion_price) per 1M tokens.
    """
    models = await fetch_openrouter_models()
    
    for m in models:
        if m["id"] == model_id:
            pricing = m.get("pricing", {})
            # Pricing is often returned as strings, need to convert to float
            prompt = float(pricing.get("prompt", 0)) * 1_000_000
            completion = float(pricing.get("completion", 0)) * 1_000_000
            return prompt, completion
            
    return 0.0, 0.0


async def calculate_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate the cost of a request in USD.
    """
    prompt_price_per_1m, completion_price_per_1m = await get_model_price(model_id)
    
    cost = (prompt_tokens / 1_000_000 * prompt_price_per_1m) + \
           (completion_tokens / 1_000_000 * completion_price_per_1m)
           
    return round(cost, 6)
