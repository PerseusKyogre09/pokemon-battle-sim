import json
import sys

def check_pokemon(name):
    try:
        with open('datasets/learnsets.json', 'r') as f:
            data = json.load(f)
        
        if name in data:
            print(f"Learnset for {name}:")
            learnset = data[name].get('learnset', {})
            for move in sorted(learnset.keys()):
                print(f"  - {move}")
        else:
            print(f"Pokemon {name} not found in learnsets.json")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_pokemon(sys.argv[1])
    else:
        print("Usage: python check_learnset.py <pokemon_name>")
