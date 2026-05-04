from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import requests
import os
import random
from game import Game
from pokemon import Pokemon
from data_loader import data_loader
from moveset import get_strategic_moveset, get_all_pokemon_sets, get_random_battle_ready_pokemon, get_battle_ready_pokemon_list
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
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

POKEAPI_NAME_MAP = {
    'wishiwashi': 'wishiwashi-solo',
    'aegislash': 'aegislash-shield',
    'basculin': 'basculin-red-striped',
    'darmanitan': 'darmanitan-standard',
    'darmanitangalar': 'darmanitan-galar-standard',
    'deoxys': 'deoxys-normal',
    'enamorus': 'enamorus-incarnate',
    'eiscue': 'eiscue-ice',
    'giratina': 'giratina-altered',
    'gourgeist': 'gourgeist-average',
    'indeedee': 'indeedee-male',
    'indeedeef': 'indeedee-female',
    'keldeo': 'keldeo-ordinary',
    'landorus': 'landorus-incarnate',
    'landorustherian': 'landorus-therian',
    'lycanroc': 'lycanroc-midday',
    'meloetta': 'meloetta-aria',
    'meowstic': 'meowstic-male',
    'meowsticf': 'meowstic-female',
    'mimikyu': 'mimikyu-disguised',
    'morpeko': 'morpeko-full-belly',
    'oricorio': 'oricorio-baile',
    'pumpkaboo': 'pumpkaboo-average',
    'shaymin': 'shaymin-land',
    'thundurus': 'thundurus-incarnate',
    'thundurustherian': 'thundurus-therian',
    'tornadus': 'tornadus-incarnate',
    'tornadustherian': 'tornadus-therian',
    'toxtricity': 'toxtricity-amped',
    'urshifu': 'urshifu-single-strike',
    'urshifurapidstrike': 'urshifu-rapid-strike',
    'wormadam': 'wormadam-plant',
    'tapukoko': 'tapu-koko',
    'tapulele': 'tapu-lele',
    'tapubulu': 'tapu-bulu',
    'tapufini': 'tapu-fini',
    'kommoo': 'kommo-o',
    'jangmoo': 'jangmo-o',
    'hakamoo': 'hakamo-o',
    'hooh': 'ho-oh',
    'porygonz': 'porygon-z',
    'typenull': 'type-null',
    'mimejr': 'mime-jr',
    'mrmime': 'mr-mime',
    'mrrime': 'mr-rime',
    'mr-rime': 'mr-rime',
}
def get_best_sprite(data, side='front', shiny=False):
    """
    Intelligently fetch the best possible sprite.
    Follows priority: Gen 5 Animated Pixel > Gen 5 Static Pixel > 3D Animated.
    Includes form normalization for Showdown compatibility.
    """
    name = data['name'].lower()
    
    # Normalization for Showdown sprite filenames
    # 1. Strip spaces and hyphens
    # 2. Handle specific form patterns (e.g. "kyogre-primal" -> "kyogre-primal")
    # Showdown often uses lowercased, hyphenated names for forms.
    pokemon_name = name.replace(' ', '').replace('-', '')
    
    # Specific common overrides for Showdown's naming conventions
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
    
    # Handle forms more explicitly (e.g. Alolan, Galar, Primal, Mega)
    if '-' in name:
        parts = name.split('-')
        # If it's a known form, Showdown usually uses 'name-form'
        if any(f in name for f in ['alola', 'galar', 'hisui', 'paldea', 'mega', 'primal', 'origin', 'therian', 'crowned', 'eternamax', 'ultra', 'dusk', 'dawn']):
            pokemon_name = name.replace(' ', '') # Keep the hyphen for forms
    
    if pokemon_name in OVERRIDES:
        pokemon_name = OVERRIDES[pokemon_name]

    # Showdown Path Logic
    prefix = ""
    back_suffix = "-back" if side == 'back' else ""
    shiny_suffix = "-shiny" if shiny else ""

    # Priority 1: Pixel Animated (Gen 5 style)
    # Path: /sprites/gen5ani[-back][-shiny]/name.gif
    url_pixel_ani = f"https://play.pokemonshowdown.com/sprites/gen5ani{back_suffix}{shiny_suffix}/{pokemon_name}.gif"
    
    # Priority 2: Pixel Static (Gen 5 style)
    # Path: /sprites/gen5[-back][-shiny]/name.png
    url_pixel_static = f"https://play.pokemonshowdown.com/sprites/gen5{back_suffix}{shiny_suffix}/{pokemon_name}.png"
    
    # Priority 3: Modern 3D Animated (Gen 6+ style)
    # Path: /sprites/ani[-back][-shiny]/name.gif
    url_3d_ani = f"https://play.pokemonshowdown.com/sprites/ani{back_suffix}{shiny_suffix}/{pokemon_name}.gif"
    
    poke_id = data.get('id', 0)
    
    # Since we can't check existence synchronously without adding latency,
    # we use the generation as a heuristic.
    # Gen 1-5 (ID <= 649) almost always have gen5ani.
    if poke_id > 0 and poke_id <= 649:
        # Check for specific forms that might only be in static gen5
        return url_pixel_ani
    
    # Gen 6+ (including Mega/Primal forms which are often ID > 10000)
    # Default to static pixel as requested ("use gen 5 static first instead of the 3d model")
    return url_pixel_static

def get_pokemon_data(pokemon_name):
    normalized_name = pokemon_name.lower().replace(' ', '')
    api_name = POKEAPI_NAME_MAP.get(normalized_name, normalized_name)
    
    url = f'https://pokeapi.co/api/v2/pokemon/{api_name}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
        
    if response.status_code == 404 and '-' not in api_name:
        for p_name in [f"{api_name[:4]}-{api_name[4:]}", f"{api_name[:5]}-{api_name[5:]}", f"{api_name[:6]}-{api_name[6:]}"]:
            try_url = f'https://pokeapi.co/api/v2/pokemon/{p_name}'
            res = requests.get(try_url)
            if res.status_code == 200:
                return res.json()
                
    raise HTTPException(status_code=404, detail=f'Pokémon {pokemon_name} not found!')

def get_pokemon_moves(pokemon_data):
    pokemon_name = pokemon_data['name'].lower()
    strategic_moves = get_strategic_moveset(pokemon_name, debug=False)
    
    if strategic_moves:
        return [{'name': move_name} for move_name in strategic_moves[:4]]
    return [{'name': 'tackle'}, {'name': 'growl'}]

@app.get("/api/search-pokemon")
async def search_pokemon(q: str = ""):
    """Fast search limited to battle-ready Pokemon with movesets."""
    query = q.lower()
    if not query or len(query) < 2:
        return {"success": False, "results": []}
    
    try:
        # Use battle-ready list for faster, filtered search
        battle_ready = get_battle_ready_pokemon_list()
        matches = [p for p in battle_ready if query in p.lower()][:8]
        
        results = []
        for pokemon_name in matches:
            try:
                # Get pokemon data for ability
                pokemon_data = get_pokemon_data(pokemon_name)
                ability_name = pokemon_data.get('abilities', [{}])[0].get('ability', {}).get('name', 'unknown')
                
                # Get strategic moveset
                moveset = get_strategic_moveset(pokemon_name, debug=False)
                
                results.append({
                    'name': pokemon_name,
                    'ability': ability_name.replace('-', ' ').title(),
                    'moveset': moveset[:4] if moveset else ['Tackle'],
                    'has_sets': bool(moveset)
                })
            except:
                # Skip Pokemon that fail to load
                continue
        
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
    """Ultra-fast search using pre-cached battle-ready list."""
    query = q.lower()
    if not query or len(query) < 2:
        return {"success": False, "results": []}
    
    try:
        battle_ready = get_battle_ready_pokemon_list()
        matches = [p for p in battle_ready if query in p.lower()][:8]
        
        results = []
        for pokemon_name in matches:
            try:
                pokemon_data = get_pokemon_data(pokemon_name)
                ability_name = pokemon_data.get('abilities', [{}])[0].get('ability', {}).get('name', 'unknown')
                moveset = get_strategic_moveset(pokemon_name, debug=False)
                
                results.append({
                    'name': pokemon_name,
                    'ability': ability_name.replace('-', ' ').title(),
                    'moveset': moveset[:4] if moveset else ['Tackle'],
                    'has_sets': bool(moveset)
                })
            except:
                continue
        
        return {"success": True, "results": results}
    except Exception as e:
        print(f"Error in optimized search: {e}")
        return {"success": False, "results": []}

@app.get("/api/battle-ready-pokemon")
async def get_battle_ready_list():
    try:
        return {"success": True, "pokemon": get_battle_ready_pokemon_list()}
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
                'evs': selected_set.get('evs', {}),
                'ivs': selected_set.get('ivs', {}),
                'nature': selected_set.get('nature', 'Hardy'),
                'ability': selected_set.get('ability', player_data.get('abilities', [{}])[0].get('ability', {}).get('name', 'noability'))
            }
        else:
            player_moves = get_pokemon_moves(player_data)
            
        opponent_moves = get_pokemon_moves(opponent_data)
        
        # Determine opponent competitive config
        opponent_stats_config = {}
        opponent_sets = get_all_pokemon_sets(opponent_pokemon_name)
        if opponent_sets:
            # Pick a random set for the opponent
            all_sets = []
            for fmt in opponent_sets:
                for set_name, s in opponent_sets[fmt].items():
                    all_sets.append(s)
            
            if all_sets:
                best_set = random.choice(all_sets)
                opponent_stats_config = {
                    'evs': best_set.get('evs', {}),
                    'ivs': best_set.get('ivs', {}),
                    'nature': best_set.get('nature', 'Hardy'),
                    'ability': best_set.get('ability', 'noability')
                }
                # Use the moves from this set too
                if best_set.get('moves'):
                    opponent_moves = [{'name': m} for m in best_set['moves']]

        game_instance = Game()
        
        # Override Game.start_battle logic to pass detailed configs
        # Initialize player pokemon with full stats
        game_instance.player_pokemon = Pokemon(
            player_data['name'], 
            [t['type']['name'] for t in player_data['types']],
            get_best_sprite(player_data, side='back', shiny=selected_set.get('shiny', False) if selected_set else False),
            player_data['stats'],
            player_moves,
            **player_stats_config
        )
        game_instance.player_pokemon.is_player = True
        
        # Initialize opponent pokemon with full stats
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
