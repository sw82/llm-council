import urllib.request
import json

try:
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models") as response:
        data = json.loads(response.read().decode()).get("data", [])
        if data:
            print(json.dumps(data[0], indent=2))
            print(f"\nTotal models: {len(data)}")
        else:
            print("No data found")
except Exception as e:
    print(f"Error: {e}")
