import json

with open('datasets/learnsets.json', 'r') as f:
    learnsets = json.load(f)

for key in ['zacian', 'zaciancrowned']:
    if key in learnsets:
        print(f"--- {key} ---")
        print(f"Learnset keys: {list(learnsets[key].get('learnset', {}).keys())[:10]}...")
        print(f"Total moves: {len(learnsets[key].get('learnset', {}))}")
    else:
        print(f"--- {key} NOT FOUND ---")
