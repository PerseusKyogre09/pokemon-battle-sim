from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import requests
import os
import random
from game import Game
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

@app.get("/api/audio/signed-url/{filename}")
async def get_signed_url(filename: str, request: Request):
    if not supabase:
        print(f"[AUDIO] ⚠️ Supabase not configured. Falling back to local: {filename}")
        base_url = str(request.base_url).rstrip('/')
        return {"url": f"{base_url}/api/music/local/{filename}", "source": "local"}
    
    try:
        response = supabase.storage.from_(bucket_name).create_signed_url(filename, 3600)
        if "error" in response:
            print(f"[AUDIO] ❌ Supabase error: {response['error']}")
            base_url = str(request.base_url).rstrip('/')
            return {"url": f"{base_url}/api/music/local/{filename}", "source": "local"}
        
        print(f"[AUDIO] ✅ Serving {filename} from Supabase")
        return {"url": response["signedURL"], "source": "supabase"}
    except Exception as e:
        print(f"[AUDIO] ❌ Exception: {e}")
        base_url = str(request.base_url).rstrip('/')
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
    query = q.lower()
    if not query:
        return []
    
    try:
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{query}')
        if response.status_code == 200:
            pokemon = response.json()
            return [{
                'name': pokemon['name'],
                'sprite': pokemon['sprites']['front_default'],
                'types': [t['type']['name'] for t in pokemon['types']]
            }]
    except:
        pass
    
    try:
        response = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1000')
        if response.status_code == 200:
            data = response.json()
            matches = [p for p in data['results'] if query in p['name']][:5]
            return [{'name': p['name']} for p in matches]
    except Exception as e:
        print(f"Error searching Pokémon: {e}")
    
    return []

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
        if selected_set and 'moves' in selected_set:
            for move_name in selected_set['moves']:
                player_moves.append({'name': move_name})
        else:
            player_moves = get_pokemon_moves(player_data)
            
        opponent_moves = get_pokemon_moves(opponent_data)
        
        # Get abilities
        player_ability = "noability"
        if selected_set and 'ability' in selected_set:
            player_ability = selected_set['ability']
            
        opponent_ability = "noability"
        # Try to get a competitive set for the opponent to find an ability
        opponent_sets = get_all_pokemon_sets(opponent_pokemon_name)
        if opponent_sets:
            # Pick a random ability from the available sets
            all_opponent_abilities = []
            for fmt_sets in opponent_sets.values():
                for s in fmt_sets.values():
                    if s.get('ability'):
                        all_opponent_abilities.append(s['ability'])
            if all_opponent_abilities:
                opponent_ability = random.choice(all_opponent_abilities)

        game_instance = Game()
        start_messages = game_instance.start_battle(
            player_data, opponent_data, player_moves, opponent_moves,
            player_ability=player_ability, opponent_ability=opponent_ability
        )
        
        player_sprite = game_instance.player_pokemon.sprite_url or player_data.get('sprites', {}).get('back_default', '')
        opponent_sprite = game_instance.opponent_pokemon.sprite_url or opponent_data.get('sprites', {}).get('front_default', '')
        
        base_url = str(request.base_url).rstrip('/')
        
        battle_data = {
            'start_events': start_messages,
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
    return response_data

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
