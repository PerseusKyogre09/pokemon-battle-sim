
import sys
import os

# Add the backend/src directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.pokemon import Pokemon

def test_stat_norm():
    p = Pokemon("Pikachu", stats={'hp': 35, 'attack': 55, 'defense': 40, 'special_attack': 50, 'special_defense': 50, 'speed': 90})
    
    print(f"Initial Def: {p.stat_stages['defense']}")
    msg = p.modify_stat_stage('def', -1)
    print(f"Msg: {msg}")
    print(f"New Def: {p.stat_stages['defense']}")
    
    if p.stat_stages['defense'] == -1:
        print("SUCCESS: Abbreviation 'def' normalized to 'defense'")
    else:
        print("FAILURE: Abbreviation 'def' not normalized")

if __name__ == "__main__":
    test_stat_norm()
