from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import requests
import os
from game import Game
from data_loader import data_loader
from moveset import get_strategic_moveset, get_all_pokemon_sets
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS for Next.js development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
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

# Serve static files (fallback for local dev)
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
        # Generate a signed URL valid for 1 hour (3600 seconds)
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
            
            # Try new 'cries' field first
            if 'cries' in pokemon_data and 'latest' in pokemon_data['cries']:
                cry_url = pokemon_data['cries']['latest']
            
            # Fallback to the ID-based repository if cries field is missing
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

def get_pokemon_data(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=404, detail=f'Pokémon {pokemon_name} not found!')

def get_pokemon_moves(pokemon_data):
    pokemon_name = pokemon_data['name'].lower()
    strategic_moves = get_strategic_moveset(pokemon_name, debug=False)
    
    if strategic_moves:
        selected_moves = []
        for move_name in strategic_moves:
            clean_move_name = move_name.lower().replace(' ', '-')
            move_data = data_loader.get_move(clean_move_name)
            
            move_pp = 15
            move_power = 75
            move_type = 'normal'
            
            if move_data:
                move_power = move_data.get('basePower', 75)
                move_type = move_data.get('type', 'normal')
                move_pp = data_loader.get_move_pp(clean_move_name) or 15
            else:
                try:
                    move_url = f'https://pokeapi.co/api/v2/move/{clean_move_name}'
                    move_response = requests.get(move_url)
                    if move_response.status_code == 200:
                        move_data = move_response.json()
                        move_power = move_data.get('power', 75)
                        move_type = move_data.get('type', {}).get('name', 'normal')
                        move_pp = move_data.get('pp', 15)
                except:
                    pass
            
            selected_moves.append({
                'name': move_name,
                'power': move_power or 75,
                'type': move_type or 'normal',
                'pp': move_pp,
                'max_pp': move_pp
            })
        return selected_moves
    return []

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

@app.post("/api/start")
async def start_game(request: Request):
    global game_instance
    try:
        data = await request.json()
        player_pokemon = data.get('pokemon', 'pikachu').lower()
        selected_set = data.get('selected_set')
        
        player_data = get_pokemon_data(player_pokemon)
        opponent_data = get_pokemon_data('charizard')
        
        player_moves = []
        if selected_set and 'moves' in selected_set:
            for move_name in selected_set['moves']:
                clean_move_name = move_name.lower().replace(' ', '-')
                move_data = data_loader.get_move(clean_move_name)
                if move_data:
                    move_power = move_data.get('basePower', 75)
                    move_type = move_data.get('type', 'normal')
                    move_pp = data_loader.get_move_pp(clean_move_name) or 15
                else:
                    move_power, move_type, move_pp = 75, 'normal', 15
                
                player_moves.append({
                    'name': move_name,
                    'power': move_power,
                    'type': move_type,
                    'pp': move_pp,
                    'max_pp': move_pp
                })
        else:
            player_moves = get_pokemon_moves(player_data)
            
        opponent_moves = get_pokemon_moves(opponent_data)
        
        game_instance = Game()
        game_instance.start_battle(player_data, opponent_data, player_moves, opponent_moves)
        
        player_sprite = game_instance.player_pokemon.sprite_url or player_data.get('sprites', {}).get('back_default', '')
        opponent_sprite = game_instance.opponent_pokemon.sprite_url or opponent_data.get('sprites', {}).get('front_default', '')
        
        # Get base URL for absolute cry links
        base_url = str(request.base_url).rstrip('/')
        
        battle_data = {
            'player_pokemon': {
                **game_instance.player_pokemon.to_dict(),
                'sprite': player_sprite,
                'cry_url': f"{base_url}/api/pokemon/cry/{player_pokemon}"
            },
            'opponent_pokemon': {
                **game_instance.opponent_pokemon.to_dict(),
                'sprite': opponent_sprite,
                'cry_url': f"{base_url}/api/pokemon/cry/charizard"
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
