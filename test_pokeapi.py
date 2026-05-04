import requests
import json
from moveset import get_battle_ready_pokemon_list
import time

def check_pokemon():
    pokemon_list = get_battle_ready_pokemon_list()
    failed = []
    
    print(f"Checking {len(pokemon_list)} pokemon...")
    for p in pokemon_list:
        p_lower = p.lower()
        res = requests.get(f'https://pokeapi.co/api/v2/pokemon/{p_lower}')
        if res.status_code != 200:
            failed.append(p_lower)
            print(f"Failed: {p_lower}")
        # time.sleep(0.01)

    print(f"\nFailed {len(failed)} pokemon: {failed}")

if __name__ == "__main__":
    check_pokemon()
