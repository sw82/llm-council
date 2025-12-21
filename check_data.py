import sys
import os
import json

# Add current dir to path
sys.path.append(os.getcwd())

try:
    from backend import storage, config
    print(f"Data Dir: {config.DATA_DIR}")
    print(f"Abs Data Dir: {os.path.abspath(config.DATA_DIR)}")
    print(f"Exists: {os.path.exists(config.DATA_DIR)}")
    
    if os.path.exists(config.DATA_DIR):
        files = os.listdir(config.DATA_DIR)
        print(f"Files: {len(files)}")
        
        conversations = storage.list_conversations()
        print(f"Conversations found: {len(conversations)}")
        
        for conv in conversations[:3]:
            print(f"ID: {conv['id']}, Cost: {conv.get('total_cost')}")
            
            # Inspect raw file for metadata
            with open(storage.get_conversation_path(conv['id']), 'r') as f:
                data = json.load(f)
                msgs = data.get("messages", [])
                print(f"  Msg count: {len(msgs)}")
                for i, msg in enumerate(msgs):
                    if msg.get("role") == "assistant":
                        meta = msg.get("metadata", {})
                        print(f"  Msg {i} metadata keys: {list(meta.keys())}")
                        if "cost" in meta:
                            print(f"    Saved cost: {meta['cost']}")
                        if "usage" in meta:
                            print(f"    Usage: {meta['usage']}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
