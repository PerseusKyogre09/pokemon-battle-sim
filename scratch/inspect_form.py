import json

with open('datasets/learnsets.json', 'r') as f:
    learnsets = json.load(f)

print(json.dumps(learnsets.get('zaciancrowned', {}), indent=2))
