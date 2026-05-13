from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import requests
import os
import random
from typing import List, Dict, Any, Optional
from functools import lru_cache
from .game import Game
from ..models.pokemon import Pokemon
from ..utils.data_loader import data_loader
from ..models.moveset import get_strategic_moveset, get_all_pokemon_sets, get_random_battle_ready_pokemon, get_battle_ready_pokemon_list, BATTLE_ONLY_FORM_SUFFIXES
from ..utils.pokemon_utils import POKEAPI_NAME_MAP, get_mandatory_item
import json
import re
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
bucket_name = os.getenv("SUPABASE_BUCKET_NAME", "pokemon-music")

supabase: Client = None
if supabase_url and supabase_key and "PASTE_YOUR" not in supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("✓ Supabase client initialized")
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")

game_instance = None

# Resolve data path robustly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Load name-to-ID mapping
POKEMON_ID_MAP = {}
try:
    id_map_path = os.path.join(DATA_DIR, 'pokemon_ids.json')
    with open(id_map_path, 'r') as f:
        POKEMON_ID_MAP = json.load(f)
    print(f"✓ Loaded {len(POKEMON_ID_MAP)} Pokémon ID mappings")
except Exception as e:
    print(f"⚠️ Warning: Could not load pokemon_ids.json at {id_map_path}: {e}")

music_path = os.path.join(os.path.dirname(__file__), 'music')
if os.path.exists(music_path):
    app.mount("/api/music/local", StaticFiles(directory=music_path), name="music")


def get_public_base_url(request: Request) -> str:
    configured = os.getenv("PUBLIC_BASE_URL") or os.getenv("NEXT_PUBLIC_API_URL")
    if configured:
        return configured.rstrip('/')

    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    host = forwarded_host or request.headers.get("host")

    if host:
        scheme = forwarded_proto or request.url.scheme
        if scheme == "http" and host not in {"localhost", "127.0.0.1"} and not host.startswith("localhost:") and not host.startswith("127.0.0.1:"):
            scheme = "https"
        return f"{scheme}://{host}"

    return str(request.base_url).rstrip('/')

@app.get("/api/audio/signed-url/{filename:path}")
async def get_signed_url(filename: str, request: Request):
    if not supabase:
        print(f"[AUDIO] ⚠️ Supabase not configured. Falling back to local: {filename}")
        base_url = get_public_base_url(request)
        return {"url": f"{base_url}/api/music/local/{filename}", "source": "local"}
    
    try:
        response = supabase.storage.from_(bucket_name).create_signed_url(filename, 3600)
        if "error" in response:
            print(f"[AUDIO] ❌ Supabase error: {response['error']}")
            base_url = get_public_base_url(request)
            return {"url": f"{base_url}/api/music/local/{filename}", "source": "local"}
        
        print(f"[AUDIO] ✅ Serving {filename} from Supabase")
        return {"url": response["signedURL"], "source": "supabase"}
    except Exception as e:
        print(f"[AUDIO] ❌ Exception: {e}")
        base_url = get_public_base_url(request)
        return {"url": f"{base_url}/api/music/local/{filename}", "source": "local"}

@app.get("/api/pokemon/cry/{pokemon_name}")
async def pokemon_cry(pokemon_name: str):
    try:
        # Try to get ID first
        normalized = pokemon_name.lower().replace(' ', '').replace('-', '')
        api_name = POKEAPI_NAME_MAP.get(normalized, pokemon_name.lower())
        pokemon_id = POKEMON_ID_MAP.get(api_name) or POKEMON_ID_MAP.get(normalized)
        
        # Fallback to name if ID not found
        identifier = str(pokemon_id) if pokemon_id else api_name
        
        url = f'https://pokeapi.co/api/v2/pokemon/{identifier}'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            pokemon_data = response.json()
            cry_url = None
            
            if 'cries' in pokemon_data and 'latest' in pokemon_data['cries']:
                cry_url = pokemon_data['cries']['latest']
            
            if not cry_url:
                pokemon_id = pokemon_data.get('id')
                if pokemon_id:
                    cry_url = f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/{pokemon_id}.ogg"
            
            if cry_url:
                cry_response = requests.get(cry_url, timeout=5)
                if cry_response.status_code == 200:
                    return Response(content=cry_response.content, media_type='audio/ogg')
        
        fallback_path = os.path.join(music_path, 'nidorino.ogg')
        if os.path.exists(fallback_path):
            return FileResponse(fallback_path)
        return Response(status_code=404, content="Cry not found")
    except Exception as e:
        print(f"Error fetching Pokémon cry: {e}")
        fallback_path = os.path.join(music_path, 'nidorino.ogg')
        if os.path.exists(fallback_path):
            return FileResponse(fallback_path)
        raise HTTPException(status_code=500, detail=str(e))

from ..utils.pokemon_api import get_best_sprite, get_pokemon_data, to_display_name

def get_pokemon_moves(pokemon_data):
    pokemon_name = pokemon_data['name'].lower()
    strategic_moves = get_strategic_moveset(pokemon_name, debug=False)
    
    if strategic_moves:
        return [{'name': move_name} for move_name in strategic_moves[:4]]
    return [{'name': 'tackle'}, {'name': 'growl'}]

@lru_cache(maxsize=1)
def get_comprehensive_pokemon_list() -> List[str]:
    # Start with Smogon list
    try:
        names = set(get_battle_ready_pokemon_list())
    except:
        names = set()
        
    # Add names from our ID map (most comprehensive)
    if 'POKEMON_ID_MAP' in globals() and POKEMON_ID_MAP:
        for n in POKEMON_ID_MAP.keys():
            names.add(n)
            
    # Add PokeAPI names fallback
    try:
        names_path = os.path.join(DATA_DIR, 'all_pokemon_names.json')
        if os.path.exists(names_path):
            with open(names_path, 'r') as f:
                api_names = json.load(f)
                for n in api_names:
                    names.add(n)
    except Exception as e:
        print(f"Error loading PokeAPI names: {e}")
        
    # Filter out battle-only forms
    filtered_names = []
    lower_suffixes = [s.lower() for s in BATTLE_ONLY_FORM_SUFFIXES]
    for n in names:
        if any(n.lower().endswith(s) for s in lower_suffixes):
            continue
        filtered_names.append(n)
        
    return sorted(list(set(filtered_names)))

@app.get("/api/search-pokemon")
async def search_pokemon(q: str = "", sets_only: bool = False):
    query = q.lower().strip()
    if not query or len(query) < 2:
        return {"success": False, "results": []}
        
    try:
        # Use comprehensive list
        all_names = get_comprehensive_pokemon_list()
        
        # Filter matches
        matches = [p for p in all_names if query in p.lower()][:20]
        
        results = []
        for pokemon_name in matches:
            # Check for sets (this is local and fast)
            moveset = get_strategic_moveset(pokemon_name, debug=False)
            has_sets = bool(moveset)
            
            if sets_only and not has_sets:
                continue
            
            normalized = pokemon_name.lower().replace(' ', '').replace('-', '').replace('.', '')
            api_name = POKEAPI_NAME_MAP.get(normalized, pokemon_name.lower().replace(' ', '-').replace('.', ''))
            
            # Deduplicate by API name to avoid Glastrier/glastrier duplicates
            if any(r['name'] == api_name for r in results):
                continue
                
            # FAST: Only provide basic info. Detailed info like abilities will be fetched 
            # when the user actually selects the Pokemon in the UI.
            results.append({
                'name': api_name,
                'display_name': to_display_name(pokemon_name),
                'item': get_mandatory_item(pokemon_name) or '',
                'moveset': moveset[:4] if moveset else ['Tackle'],
                'has_sets': has_sets
            })
            
            if len(results) >= 15:
                break
        
        return {"success": True, "results": results}
    except Exception as e:
        print(f"Error searching Pokémon: {e}")
        return {"success": False, "results": []}

@app.get("/api/get_moveset/{pokemon_name}")
async def get_moveset(pokemon_name: str):
    try:
        moveset = get_strategic_moveset(pokemon_name, debug=False)
        if moveset:
            return {'success': True, 'moves': moveset[:4]}
        return {'success': True, 'moves': ['tackle', 'growl', 'scratch', 'leer']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_all_sets/{pokemon_name}")
async def get_all_sets(pokemon_name: str):
    try:
        all_sets = get_all_pokemon_sets(pokemon_name, debug=False)
        if all_sets:
            flattened_sets = []
            for format_name, sets in all_sets.items():
                for set_name, set_data in sets.items():
                    moves = set_data.get('moves', [])[:4]
                    if moves:
                        flattened_sets.append({
                            'format': format_name,
                            'set_name': set_name,
                            'moves': moves,
                            'item': set_data.get('item', ''),
                            'ability': set_data.get('ability', ''),
                            'nature': set_data.get('nature', ''),
                            'evs': set_data.get('evs', {})
                        })
            return {'success': True, 'sets': flattened_sets}
        return {'success': False, 'error': 'No sets found'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search-pokemon-optimized")
async def search_pokemon_optimized(q: str = ""):
    return await search_pokemon(q)

@app.get("/api/battle-ready-pokemon")
async def get_battle_ready_list():
    try:
        return {"success": True, "pokemon": get_battle_ready_pokemon_list()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/pokemon/{name}/moves")
async def get_pokemon_learnset_api(name: str):
    moves = data_loader.get_pokemon_moves(name)
    return moves

@app.get("/api/all-moves")
async def get_all_moves_list():
    try:
        from ..utils.data_loader import data_loader
        moves = sorted(list(set([m['name'] for m in data_loader.moves_data.values() if 'name' in m])))
        return {"success": True, "moves": moves}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/items")
async def get_all_items_list():
    try:
        from ..utils.data_loader import data_loader
        # items_data keys are normalized IDs, but we want the display names
        items = []
        for item_id, item_data in data_loader.items_data.items():
            name = item_data.get('name')
            if name:
                items.append(name)
        return {"success": True, "items": sorted(list(set(items)))}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/start")
async def start_game(request: Request):
    global game_instance
    try:
        data = await request.json()
        
        # Support both single pokemon and team array
        player_team_raw = data.get('team')
        if isinstance(player_team_raw, list):
            # Use the provided team
            pass
        elif player_team_raw == 'random':
            player_team_raw = []
            while len(player_team_raw) < 6:
                name = get_random_battle_ready_pokemon()
                if not any(p['name'].lower() == name.lower() for p in player_team_raw):
                    player_team_raw.append({'name': name})
        elif not player_team_raw:
            # Fallback to single pokemon
            p_name = data.get('pokemon', 'pikachu').lower()
            p_set = data.get('selected_set', {})
            player_team_raw = [{
                'name': p_name,
                'ability': p_set.get('ability'),
                'item': p_set.get('item'),
                'moves': p_set.get('moves', []),
                'shiny': p_set.get('shiny', False)
            }]
            
        opponent_choice = data.get('opponent', 'charizard').lower()
        opponent_team_raw = []
        battle_mode = data.get('mode', '1v1')
        if opponent_choice == 'random':
            team_size = 6 if battle_mode == '6v6' else 1
            for _ in range(team_size):
                name = get_random_battle_ready_pokemon()
                while any(p['name'].lower() == name.lower() for p in opponent_team_raw):
                    name = get_random_battle_ready_pokemon()
                opponent_team_raw.append({'name': name})
        elif battle_mode == '6v6':
            opponent_team_raw = [{'name': opponent_choice}]
            while len(opponent_team_raw) < 6:
                name = get_random_battle_ready_pokemon()
                if name.lower() not in [p['name'].lower() for p in opponent_team_raw]:
                    opponent_team_raw.append({'name': name})
        else:
            opponent_team_raw = [{'name': opponent_choice}]

        player_team_processed = []
        for p in player_team_raw:
            p_data = get_pokemon_data(p['name'])
            if not p_data:
                continue # Skip if no data
            moves = [{'name': m} for m in p.get('moves', [])]
            if not moves:
                moves = get_pokemon_moves(p_data)
                
            mandatory = get_mandatory_item(p['name'])
            config = {
                'name': p_data['name'],
                'types': [t['type']['name'] for t in p_data['types']],
                'sprite_url': get_best_sprite(p_data, side='back', shiny=p.get('shiny', False)),
                'stats': p_data['stats'],
                'moves': moves,
                'cry_url': p_data.get('cries', {}).get('latest', ''),
                'ability': p.get('ability') or p_data.get('abilities', [{}])[0].get('ability', {}).get('name', 'noability'),
                'item': p.get('item') or mandatory or ''
            }
            player_team_processed.append(config)
            
        opponent_team_processed = []
        for o in opponent_team_raw:
            o_data = get_pokemon_data(o['name'])
            if not o_data:
                continue # Skip if no data
            o_name = o['name'].lower()
            
            o_moves = []
            o_config = {}
            o_sets = get_all_pokemon_sets(o_name)
            if o_sets:
                all_sets = []
                for fmt in o_sets:
                    for set_name, s in o_sets[fmt].items():
                        all_sets.append(s)
                
                if all_sets:
                    best_set = random.choice(all_sets)
                    mandatory = get_mandatory_item(o_name)
                    o_config = {
                        'evs': best_set.get('evs', {}),
                        'ivs': best_set.get('ivs', {}),
                        'nature': best_set.get('nature', 'Hardy'),
                        'ability': best_set.get('ability', 'noability'),
                        'item': best_set.get('item', mandatory or '')
                    }
                    if best_set.get('moves'):
                        o_moves = [{'name': m} for m in best_set['moves']]
            
            if not o_moves:
                o_moves = get_pokemon_moves(o_data)
                
            config = {
                'name': o_data['name'],
                'types': [t['type']['name'] for t in o_data['types']],
                'sprite_url': get_best_sprite(o_data, side='front', shiny=False),
                'stats': o_data['stats'],
                'moves': o_moves,
                'cry_url': o_data.get('cries', {}).get('latest', ''),
                **o_config
            }
            opponent_team_processed.append(config)

        game_instance = Game()
        initial_events = game_instance.start_battle(player_team_processed, opponent_team_processed)
        
        # Prepare response
        return {
            "success": True,
            "weather": game_instance.weather,
            "player_pokemon": {
                "name": game_instance.player_pokemon.name,
                "current_hp": game_instance.player_pokemon.current_hp,
                "max_hp": game_instance.player_pokemon.max_hp,
                "sprite": game_instance.player_pokemon.sprite_url,
                "cry_url": game_instance.player_pokemon.cry_url,
                "types": game_instance.player_pokemon.types,
                "level": game_instance.player_pokemon.level,
                "status_effects": game_instance.player_pokemon.get_status_display(),
                "substitute_hp": game_instance.player_pokemon.substitute_hp,
                "can_mega_evolve": game_instance.can_mega_evolve(True)
            },
            "opponent_pokemon": {
                "name": game_instance.opponent_pokemon.name,
                "current_hp": game_instance.opponent_pokemon.current_hp,
                "max_hp": game_instance.opponent_pokemon.max_hp,
                "sprite": game_instance.opponent_pokemon.sprite_url,
                "cry_url": game_instance.opponent_pokemon.cry_url,
                "types": game_instance.opponent_pokemon.types,
                "level": game_instance.opponent_pokemon.level,
                "status_effects": game_instance.opponent_pokemon.get_status_display(),
                "substitute_hp": game_instance.opponent_pokemon.substitute_hp
            },
            "player_moves": [m.to_dict() for m in game_instance.player_pokemon.moves.values()],
            "player_team": [p.to_dict() for p in game_instance.player_team],
            "opponent_team": [p.to_dict() for p in game_instance.opponent_team],
            "start_events": initial_events
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/random-team")
async def get_random_team():
    try:
        team = []
        max_attempts = 20
        attempts = 0
        while len(team) < 6 and attempts < max_attempts:
            attempts += 1
            name = get_random_battle_ready_pokemon()
            # Ensure uniqueness
            if any(p['name'].lower() == name.lower() for p in team):
                continue
                
            p_data = get_pokemon_data(name)
            
            p_sets = get_all_pokemon_sets(name)
            best_set = None
            if p_sets:
                all_sets = []
                for fmt in p_sets:
                    for set_name, s in p_sets[fmt].items():
                        all_sets.append(s)
                if all_sets:
                    best_set = random.choice(all_sets)
            
            config = {
                'name': p_data['name'],
                'types': [t['type']['name'] for t in p_data['types']],
                'sprite_url': get_best_sprite(p_data, side='front', shiny=False),
                'ability': best_set.get('ability', 'Unknown') if best_set else 'Unknown',
                'item': best_set.get('item', 'None') if best_set else 'None'
            }
            team.append(config)
        return {"success": True, "team": team}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/team")
async def get_team():
    global game_instance
    if not game_instance:
        return {"player_team": []}
    return {
        "player_team": [
            {
                "index": i,
                "name": p.name,
                "hp": p.current_hp,
                "max_hp": p.max_hp,
                "is_fainted": p.is_fainted(),
                "sprite": p.sprite_url,
                "status": p.get_status_display()
            } for i, p in enumerate(game_instance.player_team)
        ]
    }

@app.post("/api/move")
async def move(request: Request):
    global game_instance
    if game_instance is None:
        raise HTTPException(status_code=400, detail="Battle not initialized")

    data = await request.json()
    move_name = data.get('move')
    switch_index = data.get('switch_index')
    mega = data.get('mega', False)
    
    turn_info = game_instance.process_turn(move_name=move_name, switch_index=switch_index, mega=mega)
    
    if 'action_order' in turn_info:
        del turn_info['action_order']
    
    response_data = {
        "success": True,
        "player_pokemon": {
            "name": game_instance.player_pokemon.name,
            "current_hp": game_instance.player_pokemon.current_hp,
            "max_hp": game_instance.player_pokemon.max_hp,
            "sprite": game_instance.player_pokemon.sprite_url,
            "cry_url": game_instance.player_pokemon.cry_url,
            "types": game_instance.player_pokemon.types,
            "level": game_instance.player_pokemon.level,
            "status_effects": game_instance.player_pokemon.get_status_display(),
            "substitute_hp": game_instance.player_pokemon.substitute_hp,
            "can_mega_evolve": game_instance.can_mega_evolve(True)
        },
        "opponent_pokemon": {
            "name": game_instance.opponent_pokemon.name,
            "current_hp": game_instance.opponent_pokemon.current_hp,
            "max_hp": game_instance.opponent_pokemon.max_hp,
            "sprite": game_instance.opponent_pokemon.sprite_url,
            "cry_url": game_instance.opponent_pokemon.cry_url,
            "types": game_instance.opponent_pokemon.types,
            "level": game_instance.opponent_pokemon.level,
            "status_effects": game_instance.opponent_pokemon.get_status_display(),
            "substitute_hp": game_instance.opponent_pokemon.substitute_hp
        },
        "player_moves": [m.to_dict() for m in game_instance.player_pokemon.moves.values()],
        "player_team": [p.to_dict() for p in game_instance.player_team],
        "opponent_team": [p.to_dict() for p in game_instance.opponent_team],
        "turn_info": turn_info,
        "pending_player_switch": game_instance.pending_player_self_switch,
        "is_game_over": game_instance.battle_over,
        "battle_result": game_instance.get_battle_result() if game_instance.battle_over else None
    }
    
    print(f"DEBUG: Move {move_name} result: {list(response_data.keys())}")
    if response_data["turn_info"]:
        print(f"DEBUG: Turn Info Events: {len(response_data['turn_info'].get('battle_events', []))}")
        
    return response_data

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
