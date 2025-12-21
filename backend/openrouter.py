"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            # Log raw response for debugging
            raw_text = response.text
            print(f"Raw response from {model}: {raw_text[:500]}")

            try:
                data = response.json()
                
                # Check if response has expected structure
                if 'choices' not in data or len(data['choices']) == 0:
                    return {
                        'content': None,
                        'error': 'Invalid response structure: no choices',
                        'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
                    }
                
                message = data['choices'][0].get('message', {})
                usage = data.get('usage', {})
                
                content = message.get('content')
                
                # Check if content is empty or None
                if not content or content.strip() == '':
                    # Check if there's an error message in the response
                    error_msg = message.get('error', 'Model returned empty response')
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get('message', 'Model returned empty response')
                    
                    return {
                        'content': None,
                        'error': error_msg,
                        'usage': {
                            'prompt_tokens': usage.get('prompt_tokens', 0),
                            'completion_tokens': usage.get('completion_tokens', 0),
                            'total_tokens': usage.get('total_tokens', 0)
                        }
                    }

                return {
                    'content': content,
                    'reasoning_details': message.get('reasoning_details'),
                    'usage': {
                        'prompt_tokens': usage.get('prompt_tokens', 0),
                        'completion_tokens': usage.get('completion_tokens', 0),
                        'total_tokens': usage.get('total_tokens', 0)
                    }
                }
            except (KeyError, IndexError, ValueError) as e:
                return {
                    'content': None,
                    'error': f'Failed to parse response: {str(e)}',
                    'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
                }

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}"
        try:
            error_body = e.response.json()
            if 'error' in error_body and 'message' in error_body['error']:
                error_msg = error_body['error']['message']
        except:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:100]}"
        
        print(f"HTTP error querying model {model}: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
        
        return {
            'content': None,
            'error': error_msg,
            'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
        }
    except Exception as e:
        error_msg = str(e)
        print(f"Error querying model {model}: {e}")
        return {
            'content': None,
            'error': error_msg,
            'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
        }


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
