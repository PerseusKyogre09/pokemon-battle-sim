from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import requests
import os
import random
from typing import List, Dict, Any, Optional
from functools import lru_cache
from game import Game
from pokemon import Pokemon
from data_loader import data_loader
from moveset import get_strategic_moveset, get_all_pokemon_sets, get_random_battle_ready_pokemon, get_battle_ready_pokemon_list
from pokemon_utils import POKEAPI_NAME_MAP, get_mandatory_item
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

@app.get("/api/audio/signed-url/{filename}")
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
        url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}'
        response = requests.get(url)
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
                cry_response = requests.get(cry_url)
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

def get_best_sprite(data, side='front', shiny=False):
    name = data['name'].lower()
    
    # Showdown often uses lowercased, hyphenated names for forms.
    pokemon_name = name.replace(' ', '').replace('-', '')
    
    OVERRIDES = {
        'ho-oh': 'hooh',
        'porygon-z': 'porygonz',
        'jangmo-o': 'jangmoo',
        'hakamo-o': 'hakamoo',
        'kommo-o': 'kommoo',
        'sirfetch’d': 'sirfetchd',
        'farfetch’d': 'farfetchd',
        'mr.-mime': 'mrmime',
        'mr.-rime': 'mrrime',
        'mime-jr.': 'mimejr'
    }
    
    if '-' in name:
        parts = name.split('-')
        if any(f in name for f in ['alola', 'galar', 'hisui', 'paldea', 'mega', 'primal', 'origin', 'therian', 'crowned', 'eternamax', 'ultra', 'dusk', 'dawn']):
            pokemon_name = name.replace(' ', '') # Keep the hyphen for forms
    
    if pokemon_name in OVERRIDES:
        pokemon_name = OVERRIDES[pokemon_name]

    prefix = ""
    back_suffix = "-back" if side == 'back' else ""
    shiny_suffix = "-shiny" if shiny else ""

    url_pixel_ani = f"https://play.pokemonshowdown.com/sprites/gen5ani{back_suffix}{shiny_suffix}/{pokemon_name}.gif"
    
    url_pixel_static = f"https://play.pokemonshowdown.com/sprites/gen5{back_suffix}{shiny_suffix}/{pokemon_name}.png"
    
    url_3d_ani = f"https://play.pokemonshowdown.com/sprites/ani{back_suffix}{shiny_suffix}/{pokemon_name}.gif"
    
    return url_pixel_static # Always return static gen 5 first as requested

def to_display_name(name: str) -> str:
    # Special cases
    if name.lower() == 'urshifu-single-strike': return 'Urshifu-Single-Strike'
    if name.lower() == 'urshifu': return 'Urshifu-Single-Strike'
    if name.lower() == 'giratina-altered': return 'Giratina-Altered'
    if name.lower() == 'giratina': return 'Giratina-Altered'
    
    # General rule: capitalize parts
    parts = re.split(r'[- ]', name)
    return '-'.join(p.capitalize() for p in parts)

@lru_cache(maxsize=1000)
def get_pokemon_data(pokemon_name):
    # 1. Try normalizing to map (e.g. "Giratina Origin" -> "giratinaorigin" -> "giratina-origin")
    normalized_name = pokemon_name.lower().replace(' ', '').replace('-', '')
    api_name = POKEAPI_NAME_MAP.get(normalized_name, None)
    
    # 2. If not in map, but input has hyphens, it might already be a PokeAPI name (e.g. "stunfisk-galar")
    if not api_name:
        if '-' in pokemon_name:
            api_name = pokemon_name.lower().strip()
        else:
            api_name = normalized_name

    url = f'https://pokeapi.co/api/v2/pokemon/{api_name}'
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
        
        patterns = [
            f"{api_name}-galar", f"{api_name}-alola", f"{api_name}-hisui", 
            f"{api_name}-origin", f"{api_name}-altered", f"{api_name}-single-strike",
            f"{api_name}-amped", f"{api_name}-low-key"
        ]
        for p_name in patterns:
            try:
                res = requests.get(f'https://pokeapi.co/api/v2/pokemon/{p_name}')
                if res.status_code == 200:
                    return res.json()
            except:
                continue
                
    raise HTTPException(status_code=404, detail=f'Pokémon {pokemon_name} (API: {api_name}) not found!')

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
        from moveset import get_battle_ready_pokemon_list, BATTLE_ONLY_FORM_SUFFIXES
        names = set(get_battle_ready_pokemon_list())
    except:
        names = set()
        BATTLE_ONLY_FORM_SUFFIXES = []
        
    # Add PokeAPI names
    try:
        with open('all_pokemon_names.json', 'r') as f:
            api_names = json.load(f)
            for n in api_names:
                names.add(n)
    except Exception as e:
        print(f"Error loading PokeAPI names: {e}")
        
    return sorted(list(names))

@app.get("/api/search-pokemon")
async def search_pokemon(q: str = "", sets_only: bool = False):
    query = q.lower().strip()
    if not query or len(query) < 2:
        return {"success": False, "results": []}
        
    try:
        # Use comprehensive list
        all_names = get_comprehensive_pokemon_list()
        
        # If sets_only, we can narrow down the search list immediately or filter later
        # Naming wise, matches from battle_ready already have sets.
        matches = [p for p in all_names if query in p.lower()][:15]
        
        results = []
        for pokemon_name in matches:
            try:
                api_name = POKEAPI_NAME_MAP.get(normalized, pokemon_name.lower())
                
                has_sets = bool(moveset)
                
                if sets_only and not has_sets:
                    continue
                
                ability_name = pokemon_data.get('abilities', [{}])[0].get('ability', {}).get('name', 'unknown')
                
                results.append({
                    'name': api_name,
                    'display_name': to_display_name(pokemon_name),
                    'ability': ability_name.replace('-', ' ').title(),
                    'item': get_mandatory_item(pokemon_name) or '',
                    'moveset': moveset[:4] if moveset else ['Tackle'],
                    'has_sets': has_sets
                })
                
                if len(results) >= 10:
                    break
            except:
                continue
        
        seen_names = set()
        final_results = []
        for r in results:
            if r['name'] not in seen_names:
                final_results.append(r)
                seen_names.add(r['name'])
        
        return {"success": True, "results": final_results[:10]}
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
        from data_loader import data_loader
        moves = sorted(list(set([m['name'] for m in data_loader.moves_data.values() if 'name' in m])))
        return {"success": True, "moves": moves}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/start")
async def start_game(request: Request):
    global game_instance
    try:
        data = await request.json()
        player_pokemon_name = data.get('pokemon', 'pikachu').lower()
        selected_set = data.get('selected_set')
        opponent_choice = data.get('opponent', 'charizard').lower()
        
        if opponent_choice == 'random':
            opponent_pokemon_name = get_random_battle_ready_pokemon().lower()
        else:
            opponent_pokemon_name = opponent_choice
            
        player_data = get_pokemon_data(player_pokemon_name)
        opponent_data = get_pokemon_data(opponent_pokemon_name)
        
        player_moves = []
        player_stats_config = {}
        if selected_set:
            if 'moves' in selected_set:
                for move_name in selected_set['moves']:
                    player_moves.append({'name': move_name})
            
            player_stats_config = {
                'ability': selected_set.get('ability', player_data.get('abilities', [{}])[0].get('ability', {}).get('name', 'noability')),
                'item': selected_set.get('item', get_mandatory_item(player_pokemon_name) or '')
            }
                player_stats_config['item'] = mandatory
        else:
            player_stats_config = {
                'item': get_mandatory_item(player_pokemon_name) or ''
            }
            player_moves = get_pokemon_moves(player_data)
            
        opponent_moves = get_pokemon_moves(opponent_data)
        
        # Determine opponent competitive config
        opponent_stats_config = {}
        opponent_sets = get_all_pokemon_sets(opponent_pokemon_name)
        if opponent_sets:
            all_sets = []
            for fmt in opponent_sets:
                for set_name, s in opponent_sets[fmt].items():
                    all_sets.append(s)
            
            if all_sets:
                best_set = random.choice(all_sets)
                mandatory = get_mandatory_item(opponent_pokemon_name)
                opponent_stats_config = {
                    'evs': best_set.get('evs', {}),
                    'ivs': best_set.get('ivs', {}),
                    'nature': best_set.get('nature', 'Hardy'),
                    'ability': best_set.get('ability', 'noability'),
                    'item': best_set.get('item', mandatory or '')
                }
                if mandatory:
                    opponent_stats_config['item'] = mandatory
                if best_set.get('moves'):
                    opponent_moves = [{'name': m} for m in best_set['moves']]

        game_instance = Game()
        
        game_instance.player_pokemon = Pokemon(
            player_data['name'], 
            [t['type']['name'] for t in player_data['types']],
            get_best_sprite(player_data, side='back', shiny=selected_set.get('shiny', False) if selected_set else False),
            player_data['stats'],
            player_moves,
            **player_stats_config
        )
        game_instance.player_pokemon.is_player = True
        
        game_instance.opponent_pokemon = Pokemon(
            opponent_data['name'],
            [t['type']['name'] for t in opponent_data['types']],
            get_best_sprite(opponent_data, side='front', shiny=False),
            opponent_data['stats'],
            opponent_moves,
            **opponent_stats_config
        )
        game_instance.opponent_pokemon.is_player = False
        
        # Trigger switch-in effects
        start_messages = []
        p_msgs = game_instance.player_pokemon.on_switch_in(game_instance.opponent_pokemon)
        o_msgs = game_instance.opponent_pokemon.on_switch_in(game_instance.player_pokemon)
        
        all_msgs = p_msgs + o_msgs
        for msg in all_msgs:
            if 'set_weather' in msg:
                game_instance.weather = msg['set_weather']
                game_instance.weather_duration = 5
            start_messages.append(msg)
        
        is_shiny = selected_set.get('shiny', False) if selected_set else False
        player_sprite = get_best_sprite(player_data, side='back', shiny=is_shiny)
        opponent_sprite = get_best_sprite(opponent_data, side='front', shiny=False)
        
        base_url = get_public_base_url(request)
        
        battle_data = {
            'start_events': start_messages,
            'weather': game_instance.weather,
            'player_pokemon': {
                **game_instance.player_pokemon.to_dict(),
                'sprite': player_sprite,
                'cry_url': f"{base_url}/api/pokemon/cry/{player_pokemon_name}"
            },
            'opponent_pokemon': {
                **game_instance.opponent_pokemon.to_dict(),
                'sprite': opponent_sprite,
                'cry_url': f"{base_url}/api/pokemon/cry/{opponent_pokemon_name}"
            },
            'player_moves': [{
                'name': move.name,
                'power': move.power,
                'type': move.type,
                'pp': move.pp,
                'max_pp': move.max_pp
            } for name, move in game_instance.player_pokemon.moves.items()]
        }
        return battle_data
    except Exception as e:
        print(f"Error starting battle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/move")
async def move(request: Request):
    global game_instance
    if game_instance is None:
        raise HTTPException(status_code=400, detail="Battle not initialized")

    data = await request.json()
    move_name = data.get('move')
    turn_info = game_instance.process_turn(move_name)
    
    if 'action_order' in turn_info:
        del turn_info['action_order']
    
    response_data = {
        "player_hp": game_instance.player_pokemon.current_hp,
        "opponent_hp": game_instance.opponent_pokemon.current_hp,
        "player_max_hp": game_instance.player_pokemon.max_hp,
        "opponent_max_hp": game_instance.opponent_pokemon.max_hp,
        "player_status_effects": game_instance.player_pokemon.get_status_display(),
        "opponent_status_effects": game_instance.opponent_pokemon.get_status_display(),
        "turn_info": turn_info,
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
