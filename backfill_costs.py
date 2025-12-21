import asyncio
import sys
import os
import logging

# Add current dir to path
sys.path.append(os.getcwd())

from backend import storage, pricing

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill")

async def calculate_stage_cost(results, stage_name):
    stage_cost = 0.0
    if isinstance(results, list):
        items = results
    else:
        items = [results] if results else []

    for item in items:
        model = item.get('model')
        usage = item.get('usage', {})
        if model and usage:
            pt = usage.get('prompt_tokens', 0)
            ct = usage.get('completion_tokens', 0)
            try:
                # pricing.calculate_cost is async
                cost = await pricing.calculate_cost(model, pt, ct)
                stage_cost += cost
            except Exception as e:
                logger.warning(f"Failed to calc cost for {model}: {e}")
    return stage_cost

async def main():
    print("Starting cost backfill...")
    
    # Warm up pricing cache
    await pricing.fetch_openrouter_models()
    
    conversations = storage.list_conversations()
    print(f"Found {len(conversations)} conversations.")
    
    updated_count = 0
    
    for meta in conversations:
        conv_id = meta['id']
        conversation = storage.get_conversation(conv_id)
        
        if not conversation:
            continue
            
        modified = False
        
        for msg in conversation.get('messages', []):
            if msg.get('role') == 'assistant':
                metadata = msg.get('metadata', {})
                
                # Check if cost is missing or 0
                current_cost = metadata.get('cost', 0.0)
                
                if current_cost == 0.0:
                    # Try to recalculate
                    print(f"Recalculating cost for msg in {conv_id}...")
                    
                    stage1 = msg.get('stage1', [])
                    stage2 = msg.get('stage2', [])
                    stage3 = msg.get('stage3', {})
                    
                    cost1 = await calculate_stage_cost(stage1, "1")
                    cost2 = await calculate_stage_cost(stage2, "2")
                    cost3 = await calculate_stage_cost(stage3, "3")
                    
                    total_new_cost = cost1 + cost2 + cost3
                    
                    if total_new_cost > 0:
                        print(f"  -> New cost: ${total_new_cost:.6f}")
                        metadata['cost'] = round(total_new_cost, 6)
                        msg['metadata'] = metadata
                        modified = True
        
        if modified:
            storage.save_conversation(conversation)
            updated_count += 1
            print(f"Saved update for {conv_id}")
            
    print(f"Done. Updated {updated_count} conversations.")

if __name__ == "__main__":
    asyncio.run(main())
