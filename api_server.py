from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from game import Game
from data_loader import data_loader
from moveset import get_strategic_moveset, get_all_pokemon_sets
import requests
import json
import os

app = Flask(__name__)
CORS(app) # Enable CORS for Next.js development
game = None

@app.route('/api/music/<path:filename>')
def music(filename):
    return send_from_directory(os.path.join(app.root_path, 'music'), filename)

@app.route('/api/sounds/<path:filename>')
def sounds(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/sounds'), filename)

@app.route('/api/pokemon/cry/<pokemon_name>')
def pokemon_cry(pokemon_name):
    try:
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}')
        if response.status_code == 200:
            pokemon_data = response.json()
            if 'cries' in pokemon_data and 'latest' in pokemon_data['cries']:
                cry_url = pokemon_data['cries']['latest']
                cry_response = requests.get(cry_url)
                if cry_response.status_code == 200:
                    return Response(cry_response.content, mimetype='audio/ogg')
        return send_from_directory('music', 'nidorino.ogg')
    except Exception as e:
        print(f"Error fetching Pokémon cry: {e}")
        return send_from_directory('music', 'nidorino.ogg')

def get_pokemon_data(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Pokémon {pokemon_name} not found!')

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
    
    # Fallback to dataset/PokeAPI (simplified for now)
    return []

@app.route('/api/search-pokemon')
def search_pokemon():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    try:
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{query}')
        if response.status_code == 200:
            pokemon = response.json()
            return jsonify([{
                'name': pokemon['name'],
                'sprite': pokemon['sprites']['front_default'],
                'types': [t['type']['name'] for t in pokemon['types']]
            }])
    except:
        pass
    
    try:
        response = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1000')
        if response.status_code == 200:
            data = response.json()
            matches = [p for p in data['results'] if query in p['name']][:5]
            return jsonify([{'name': p['name']} for p in matches])
    except Exception as e:
        print(f"Error searching Pokémon: {e}")
    
    return jsonify([])

@app.route('/api/get_moveset/<pokemon_name>')
def get_moveset(pokemon_name):
    # Same as web_server.py
    try:
        moveset = get_strategic_moveset(pokemon_name, debug=False)
        if moveset:
            return jsonify({'success': True, 'moves': moveset[:4]})
        return jsonify({'success': True, 'moves': ['tackle', 'growl', 'scratch', 'leer']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get_all_sets/<pokemon_name>')
def get_all_sets(pokemon_name):
    # Same as web_server.py
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
            return jsonify({'success': True, 'sets': flattened_sets})
        return jsonify({'success': False, 'error': 'No sets found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_game():
    global game
    try:
        data = request.json
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
        
        game = Game()
        game.start_battle(player_data, opponent_data, player_moves, opponent_moves)
        
        player_sprite = game.player_pokemon.sprite_url or player_data.get('sprites', {}).get('back_default', '')
        opponent_sprite = game.opponent_pokemon.sprite_url or opponent_data.get('sprites', {}).get('front_default', '')
        
        battle_data = {
            'player_pokemon': {
                **game.player_pokemon.to_dict(),
                'sprite': player_sprite,
                'cry_url': f"http://localhost:5000/api/pokemon/cry/{player_pokemon}"
            },
            'opponent_pokemon': {
                **game.opponent_pokemon.to_dict(),
                'sprite': opponent_sprite,
                'cry_url': "http://localhost:5000/api/pokemon/cry/charizard"
            },
            'player_moves': [{
                'name': move.name,
                'power': move.power,
                'type': move.type,
                'pp': move.pp,
                'max_pp': move.max_pp
            } for name, move in game.player_pokemon.moves.items()]
        }
        return jsonify(battle_data)
    except Exception as e:
        print(f"Error starting battle: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/move', methods=['POST'])
def move():
    global game
    if game is None:
        return jsonify({"error": "Battle not initialized"}), 400

    move_name = request.json.get('move')
    turn_info = game.process_turn(move_name)
    
    # Remove non-serializable objects from turn_info
    if 'action_order' in turn_info:
        del turn_info['action_order']
    
    response_data = {
        "player_hp": game.player_pokemon.current_hp,
        "opponent_hp": game.opponent_pokemon.current_hp,
        "player_max_hp": game.player_pokemon.max_hp,
        "opponent_max_hp": game.opponent_pokemon.max_hp,
        "player_status_effects": game.player_pokemon.get_status_display(),
        "opponent_status_effects": game.opponent_pokemon.get_status_display(),
        "turn_info": turn_info,
        "is_game_over": game.battle_over,
        "battle_result": game.get_battle_result() if game.battle_over else None
    }
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
