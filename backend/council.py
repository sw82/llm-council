"""3-stage LLM Council orchestration."""

from typing import List, Dict, Any, Tuple
from .openrouter import query_models_parallel, query_model
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL
from .pricing import calculate_cost, fetch_openrouter_models
import logging

logger = logging.getLogger("llm_council")


async def stage1_collect_responses(user_query: str, models: List[str] = None) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual responses from all council models.

    Args:
        user_query: The user's question
        models: Optional list of models to use. Defaults to COUNCIL_MODELS.

    Returns:
        List of dicts with 'model' and 'response' keys
    """
    target_models = models if models else COUNCIL_MODELS
    messages = [{"role": "user", "content": user_query}]

    # Query all models in parallel
    responses = await query_models_parallel(target_models, messages)

    # Format results
    stage1_results = []
    all_errors = []
    
    for model, response in responses.items():
        if response is not None:
            if response.get('error'):
                # Include error in results
                error_msg = response.get('error')
                all_errors.append(f"{model}: {error_msg}")
                stage1_results.append({
                    "model": model,
                    "response": f"❌ Error: {error_msg}",
                    "error": error_msg,
                    "usage": response.get('usage', {})
                })
            elif response.get('content'):
                # Successful response
                stage1_results.append({
                    "model": model,
                    "response": response.get('content', ''),
                    "usage": response.get('usage', {})
                })
    
    # If ALL models failed, add a helpful message
    if len(stage1_results) == 0 or all(r.get('error') for r in stage1_results):
        stage1_results.append({
            "model": "system",
            "response": f"""⚠️ All council models failed. Common causes:

1. **API Key Limit Exceeded**: Your OpenRouter key has reached its monthly limit
   → Solution: Add credits at https://openrouter.ai/settings/keys

2. **Invalid API Key**: Check your OPENROUTER_API_KEY environment variable
   → Solution: Verify the key in your .env file

3. **Model Not Available**: Some models may not be accessible
   → Solution: Try different models in settings

Errors received:
{chr(10).join(f'  • {e}' for e in all_errors[:5])}""",
            "error": "all_models_failed",
            "usage": {}
        })

    return stage1_results


async def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    models: List[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, str], Dict[str, Any]]:
    """
    Stage 2: Each model ranks the anonymized responses.

    Args:
        user_query: The original user query
        stage1_results: Results from Stage 1
        models: Optional list of models to use. Defaults to COUNCIL_MODELS.

    Returns:
        Tuple of (rankings list, label_to_model mapping, usage stats)
    """
    target_models = models if models else COUNCIL_MODELS
    # Create anonymized labels for responses (Response A, Response B, etc.)
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

    # Create mapping from label to model name
    label_to_model = {
        f"Response {label}": result['model']
        for label, result in zip(labels, stage1_results)
    }

    # Build the ranking prompt
    responses_text = "\n\n".join([
        f"Response {label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example of the correct format for your ENTIRE response:

Response A provides good detail on X but misses Y...
Response B is accurate but lacks depth on Z...
Response C offers the most comprehensive answer...

FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking:"""

    messages = [{"role": "user", "content": ranking_prompt}]

    # Get rankings from all council models in parallel
    responses = await query_models_parallel(target_models, messages)

    # Format results
    stage2_results = []
    total_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}

    for model, response in responses.items():
        if response is not None:
            full_text = response.get('content', '')
            parsed = parse_ranking_from_text(full_text)
            
            # Aggregate usage
            usage = response.get('usage', {})
            total_usage['prompt_tokens'] += usage.get('prompt_tokens', 0)
            total_usage['completion_tokens'] += usage.get('completion_tokens', 0)
            total_usage['total_tokens'] += usage.get('total_tokens', 0)

            stage2_results.append({
                "model": model,
                "ranking": full_text,
                "parsed_ranking": parsed,
                "usage": usage
            })

    return stage2_results, label_to_model, total_usage


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    chairman_model: str = None
) -> Dict[str, Any]:
    """
    Stage 3: Chairman synthesizes final response.

    Args:
        user_query: The original user query
        stage1_results: Individual model responses from Stage 1
        stage2_results: Rankings from Stage 2
        chairman_model: Optional chairman model override.

    Returns:
        Dict with 'model' and 'response' keys
    """
    target_model = chairman_model if chairman_model else CHAIRMAN_MODEL
    # Build comprehensive context for chairman
    stage1_text = "\n\n".join([
        f"Model: {result['model']}\nResponse: {result['response']}"
        for result in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"Model: {result['model']}\nRanking: {result['ranking']}"
        for result in stage2_results
    ])

    chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {user_query}

STAGE 1 - Individual Responses:
{stage1_text}

STAGE 2 - Peer Rankings:
{stage2_text}

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any patterns of agreement or disagreement

Provide a clear, well-reasoned final answer that represents the council's collective wisdom:"""

    messages = [{"role": "user", "content": chairman_prompt}]

    # Query the chairman model
    response = await query_model(target_model, messages)

    if response is None or response.get('error') or not response.get('content'):
        # Fallback if chairman fails
        error_detail = response.get('error', 'No response') if response else 'No response'
        logger.error(f"Chairman model {target_model} failed: {error_detail}")
        return {
            "model": target_model,
            "response": f"❌ Chairman Error: {error_detail}",
            "error": error_detail,
            "usage": response.get('usage', {}) if response else {}
        }

    return {
        "model": target_model,
        "response": response.get('content', ''),
        "usage": response.get('usage', {})
    }


def parse_ranking_from_text(ranking_text: str) -> List[str]:
    """
    Parse the FINAL RANKING section from the model's response.

    Args:
        ranking_text: The full text response from the model

    Returns:
        List of response labels in ranked order
    """
    import re

    # Look for "FINAL RANKING:" section
    if "FINAL RANKING:" in ranking_text:
        # Extract everything after "FINAL RANKING:"
        parts = ranking_text.split("FINAL RANKING:")
        if len(parts) >= 2:
            ranking_section = parts[1]
            # Try to extract numbered list format (e.g., "1. Response A")
            # This pattern looks for: number, period, optional space, "Response X"
            numbered_matches = re.findall(r'\d+\.\s*Response [A-Z]', ranking_section)
            if numbered_matches:
                # Extract just the "Response X" part
                return [re.search(r'Response [A-Z]', m).group() for m in numbered_matches]

            # Fallback: Extract all "Response X" patterns in order
            matches = re.findall(r'Response [A-Z]', ranking_section)
            return matches

    # Fallback: try to find any "Response X" patterns in order
    matches = re.findall(r'Response [A-Z]', ranking_text)
    return matches


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all models.

    Args:
        stage2_results: Rankings from each model
        label_to_model: Mapping from anonymous labels to model names

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_text = ranking['ranking']

        # Parse the ranking from the structured format
        parsed_ranking = parse_ranking_from_text(ranking_text)

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    # Calculate average position for each model
    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append({
                "model": model,
                "average_rank": round(avg_rank, 2),
                "rankings_count": len(positions)
            })

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x['average_rank'])

    return aggregate


async def generate_conversation_title(user_query: str) -> str:
    """
    Generate a short title for a conversation based on the first user message.

    Args:
        user_query: The first user message

    Returns:
        A short title (3-5 words)
    """
    title_prompt = f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Question: {user_query}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    # Use gemini-2.5-flash for title generation (fast and cheap)
    response = await query_model("google/gemini-2.5-flash", messages, timeout=30.0)

    if response is None:
        # Fallback to a generic title
        return "New Conversation"

    title = response.get('content', 'New Conversation').strip()

    # Clean up the title - remove quotes, limit length
    title = title.strip('"\'')

    # Truncate if too long
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def calculate_council_metadata(
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    stage3_result: Dict[str, Any],
    label_to_model: Dict[str, str],
    aggregate_rankings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate total usage and cost metadata for a council run.
    """
    total_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    total_cost = 0.0
    cost_breakdown = []
    
    # Stage 1 usage
    for res in stage1_results:
        u = res.get('usage', {})
        model = res.get('model', 'unknown')
        
        pt = u.get('prompt_tokens', 0)
        ct = u.get('completion_tokens', 0)
        
        total_usage['prompt_tokens'] += pt
        total_usage['completion_tokens'] += ct
        total_usage['total_tokens'] += u.get('total_tokens', 0)
        
        cost = await calculate_cost(model, pt, ct)
        total_cost += cost
        cost_breakdown.append({"stage": "1", "model": model, "cost": cost})

    # Stage 2 usage
    for res in stage2_results:
        u = res.get('usage', {})
        model = res.get('model', 'unknown')
        
        pt = u.get('prompt_tokens', 0)
        ct = u.get('completion_tokens', 0)
        
        total_usage['prompt_tokens'] += pt
        total_usage['completion_tokens'] += ct
        total_usage['total_tokens'] += u.get('total_tokens', 0)
        
        cost = await calculate_cost(model, pt, ct)
        total_cost += cost
        cost_breakdown.append({"stage": "2", "model": model, "cost": cost})

    # Stage 3 usage
    s3_usage = stage3_result.get('usage', {})
    s3_model = stage3_result.get('model', 'unknown')
    
    s3_pt = s3_usage.get('prompt_tokens', 0)
    s3_ct = s3_usage.get('completion_tokens', 0)
    
    total_usage['prompt_tokens'] += s3_pt
    total_usage['completion_tokens'] += s3_ct
    total_usage['total_tokens'] += s3_usage.get('total_tokens', 0)
    
    s3_cost = await calculate_cost(s3_model, s3_pt, s3_ct)
    total_cost += s3_cost
    cost_breakdown.append({"stage": "3", "model": s3_model, "cost": s3_cost})

    return {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings,
        "usage": total_usage,
        "cost": round(total_cost, 6),
        "cost_breakdown": cost_breakdown
    }


async def run_full_council(
    user_query: str, 
    council_models: List[str] = None,
    chairman_model: str = None
) -> Tuple[List, List, Dict, Dict]:
    """
    Run the complete 3-stage council process.

    Args:
        user_query: The user's question
        council_models: Optional list of council models
        chairman_model: Optional chairman model

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    # Stage 1: Collect individual responses
    stage1_results = await stage1_collect_responses(user_query, council_models)

    # If no models responded successfully, return error
    if not stage1_results:
        return [], [], {
            "model": "error",
            "response": "All models failed to respond. Please try again."
        }, {}

    # Stage 2: Collect rankings
    stage2_results, label_to_model, stage2_usage = await stage2_collect_rankings(
        user_query, stage1_results, council_models
    )

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Stage 3: Synthesize final answer
    stage3_result = await stage3_synthesize_final(
        user_query,
        stage1_results,
        stage2_results,
        chairman_model
    )

    # Calculate metadata using extracted logic
    metadata = await calculate_council_metadata(
        stage1_results,
        stage2_results,
        stage3_result,
        label_to_model,
        aggregate_rankings
    )

    return stage1_results, stage2_results, stage3_result, metadata
