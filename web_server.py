from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, Response
from game import Game
from data_loader import data_loader
from moveset import get_strategic_moveset
import requests

app = Flask(__name__)
game = None

@app.route('/music/<path:filename>')
def music(filename):
    return send_from_directory(app.root_path + '/music', filename)

@app.route('/static/sounds/<path:filename>')
def sounds(filename):
    return send_from_directory(app.root_path + '/static/sounds', filename)

@app.route('/pokemon/cry/<pokemon_name>')
def pokemon_cry(pokemon_name):
    try:
        # Fetch pokemon data from the pokeapi
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}')
        if response.status_code == 200:
            pokemon_data = response.json()
            
            # Get the cry of the pokemon
            if 'cries' in pokemon_data and 'latest' in pokemon_data['cries']:
                cry_url = pokemon_data['cries']['latest']
                
                # Fetch the cry audio file
                cry_response = requests.get(cry_url)
                if cry_response.status_code == 200:
                    # Return the audio file with the correct content type
                    return Response(cry_response.content, mimetype='audio/ogg')
            
            # Fallback to a default cry if the specific one isn't available
            return send_from_directory('music', 'nidorino.ogg')
        else:
            return send_from_directory('music', 'nidorino.ogg')
    except Exception as e:
        print(f"Error fetching Pokémon cry: {e}")
        return send_from_directory('music', 'nidorino.ogg')

def get_pokemon_data(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}' #pokeapi for pokemon data
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Pokémon {pokemon_name} not found!')

def get_pokemon_moves(pokemon_data):
    pokemon_name = pokemon_data['name'].lower()
    
    # First try to get strategic moveset
    print(f"\n{'*'*50}")
    print(f"Getting moveset for {pokemon_name}")
    print(f"{'*'*50}")
    strategic_moves = get_strategic_moveset(pokemon_name, debug=True)
    
    if strategic_moves:
        # We have a strategic moveset
        selected_moves = []
        for move_name in strategic_moves:
            # Clean up move name to match our dataset format
            clean_move_name = move_name.lower().replace(' ', '-')
            
            # First try to get move data from our dataset with debug logging
            print(f"\n=== Getting move data for {clean_move_name} ===")
            move_data = data_loader.get_move(clean_move_name)
            
            if move_data:
                move_power = move_data.get('basePower', 75)
                move_type = move_data.get('type', 'normal')
                print(f"Found in dataset: power={move_power}, type={move_type}")
            else:
                # If not found in dataset, fetch from PokeAPI
                print(f"Move {clean_move_name} not found in dataset, trying PokeAPI...")
                try:
                    move_url = f'https://pokeapi.co/api/v2/move/{clean_move_name}'
                    move_response = requests.get(move_url)
                    if move_response.status_code == 200:
                        move_data = move_response.json()
                        move_power = move_data.get('power', 75)  # Default to 75 for strategic moves
                        move_type = move_data.get('type', {}).get('name', 'normal')
                        print(f"Found in PokeAPI: power={move_power}, type={move_type}")
                    else:
                        print(f"PokeAPI returned status {move_response.status_code}")
                        raise Exception("PokeAPI call failed")
                except Exception as e:
                    # If API call fails, use reasonable defaults
                    print(f"Error getting move data: {e}")
                    move_power = 75
                    move_type = 'normal'
                    print(f"Using defaults: power={move_power}, type={move_type}")
            
            # Initialize move_pp with default value first
            move_pp = 15  # Default PP if not found
            
            # For strategic moves, we need to fetch the move data first
            try:
                move_url = f'https://pokeapi.co/api/v2/move/{clean_move_name}'
                print(f"\n=== Fetching move data for {clean_move_name} ===")
                print(f"URL: {move_url}")
                
                move_response = requests.get(move_url)
                print(f"Status code: {move_response.status_code}")
                
                if move_response.status_code == 200:
                    move_data = move_response.json()
                    print(f"Raw move data for {clean_move_name}:")
                    print(f"- Name: {move_data.get('name')}")
                    print(f"- PP: {move_data.get('pp')}")
                    print(f"- Power: {move_data.get('power')}")
                    print(f"- Type: {move_data.get('type', {}).get('name')}")
                    
                    move_pp = move_data.get('pp', 15)
                    print(f"Using PP: {move_pp} (from API)")
            except Exception as e:
                print(f"Error getting PP for {move_name}: {e}")
            
            selected_moves.append({
                'name': move_name,
                'power': move_power or 75,  # Ensure we have a power value
                'type': move_type or 'normal',  # Ensure we have a type
                'pp': move_pp,
                'max_pp': move_pp
            })
        return selected_moves
    
    # Second, try to get moves from our TypeScript dataset
    dataset_moves = data_loader.get_pokemon_moves(pokemon_name, 4)
    
    if dataset_moves:
        selected_moves = []
        for move_name in dataset_moves:
            move_power = data_loader.get_move_power(move_name)
            move_type = data_loader.get_move_type(move_name)
            # Get PP for the move from dataset
            move_pp = data_loader.get_move_pp(move_name) or 15
            
            selected_moves.append({
                'name': move_name,
                'power': move_power or 50,
                'type': move_type or 'normal',
                'pp': move_pp,
                'max_pp': move_pp
            })
        return selected_moves
    
    # Fallback to PokeAPI if no strategic or dataset moves
    moves = pokemon_data['moves'][:4]  # Gets first 4 moves in the database
    selected_moves = []

    for move_entry in moves:
        move_name = move_entry['move']['name']
        move_url = move_entry['move']['url']  # URL for more details about the move

        try:
            move_response = requests.get(move_url)
            if move_response.status_code == 200:
                move_data = move_response.json()
                move_power = move_data.get('power', 50)
                move_type = move_data.get('type', {}).get('name', 'normal')
                
                # Get PP directly from the move data
                move_pp = move_data.get('pp', 15)  # Default to 15 if PP not found
                print(f"\n=== Processing move: {move_name} ===")
                print(f"- Move PP from API: {move_pp}")
                print(f"- Move power: {move_power}")
                print(f"- Move type: {move_type}")
                
                selected_moves.append({
                    'name': move_name,
                    'power': move_power,
                    'type': move_type,
                    'pp': move_pp,
                    'max_pp': move_pp
                })
        except Exception as e:
            print(f"Error processing move {move_name}: {e}")
            # Fallback if API call fails
            selected_moves.append({
                'name': move_name,
                'power': 50,
                'type': 'normal',
                'pp': 15,
                'max_pp': 15
            })
    
    return selected_moves

# Start webpage with Pokémon selection
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Handle Pokémon search
@app.route('/search-pokemon')
def search_pokemon():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    try:
        # Try exact match first
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
    
    # If no exact match, try search
    try:
        response = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1000')
        if response.status_code == 200:
            data = response.json()
            matches = [p for p in data['results'] if query in p['name']][:5]
            return jsonify([{'name': p['name']} for p in matches])
    except Exception as e:
        print(f"Error searching Pokémon: {e}")
    
    return jsonify([])

# Start the battle with selected Pokémon
@app.route('/start', methods=['POST'])
def start_game():
    global game
    
    try:
        player_pokemon = request.form.get('pokemon', 'pikachu').lower()
        
        # Get Pokémon data
        player_data = get_pokemon_data(player_pokemon)
        opponent_data = get_pokemon_data('charizard')  # Default opponent
        
        # Get moves for both Pokémon
        player_moves = get_pokemon_moves(player_data)
        opponent_moves = get_pokemon_moves(opponent_data)
        
        # Initialize the game
        game = Game()
        game.start_battle(player_data, opponent_data, player_moves, opponent_moves)
        
        # Prepare data for the battle template
        battle_data = {
            'player_data': {
                **game.player_pokemon.to_dict(),
                'id': player_data.get('id', 25)  # Default to Pikachu's ID if not found
            },
            'opponent_data': {
                **game.opponent_pokemon.to_dict(),
                'id': opponent_data.get('id', 6)  # Default to Charizard's ID if not found
            },
            'player_sprite': game.player_pokemon.sprite_url,
            'opponent_sprite': game.opponent_pokemon.sprite_url,
            'player_hp': game.player_pokemon.current_hp,
            'opponent_hp': game.opponent_pokemon.current_hp,
            'player_moves': [{
                'name': name, 
                'power': move.power, 
                'type': move.type,
                'pp': getattr(move, 'pp', 15),
                'max_pp': getattr(move, 'max_pp', getattr(move, 'pp', 15))
            } for name, move in game.player_pokemon.moves.items()]
        }
        
        return render_template('battle.html', **battle_data)
        
    except Exception as e:
        print(f"Error starting battle: {e}")
        return render_template('index.html', error="Failed to start battle. Please try a different Pokémon.")

#for using moves
@app.route('/move', methods=['POST'])
def move():
    global game

    if game is None or game.player_pokemon is None or game.opponent_pokemon is None:
        return jsonify({"error": "Battle not initialized! Please start the game first."}), 400

    move_name = request.json.get('move')
    
    # Get the player's move and its current PP before processing the turn
    player_move = game.player_pokemon.moves.get(move_name)
    current_pp = getattr(player_move, 'pp', 15) if player_move else 0
    
    # Process the turn and get turn information including effectiveness messages
    turn_info = game.process_turn(move_name)
    
    # Get the opponent's move name
    opponent_move_name = turn_info.get('opponent_move', '')
    
    # Update PP for the used move
    updated_pp = None
    if player_move and hasattr(player_move, 'pp'):
        updated_pp = player_move.pp
    elif player_move:
        updated_pp = current_pp - 1 if current_pp > 0 else 0
    
    # Get current HP values after the turn
    player_hp = game.player_pokemon.current_hp
    opponent_hp = game.opponent_pokemon.current_hp
    
    # Check if the battle is over
    is_game_over = game.battle_over
    result = game.get_battle_result() if is_game_over else None

    # Get current PP for all player moves
    print("\n=== Current Move PP Status ===")
    player_moves_pp = {}
    for move_name, move in game.player_pokemon.moves.items():
        current_pp = getattr(move, 'pp', 15)
        max_pp = getattr(move, 'max_pp', 15)
        
        print(f"Move: {move_name}")
        print(f"- Current PP: {current_pp}")
        print(f"- Max PP: {max_pp}")
        
        player_moves_pp[move_name] = {
            'current_pp': current_pp,
            'max_pp': max_pp
        }
    
    # Prepare response data
    response_data = {
        "player_hp": player_hp,
        "opponent_hp": opponent_hp,
        "player_max_hp": game.player_pokemon.max_hp,
        "opponent_max_hp": game.opponent_pokemon.max_hp,
        "player_moves_pp": player_moves_pp,
        "turn_info": {
            "player_first": turn_info.get('player_first', True),
            "player_move": turn_info.get('player_move', ''),
            "opponent_move": opponent_move_name,
            "player_damage": turn_info.get('player_damage', 0),
            "opponent_damage": turn_info.get('opponent_damage', 0),
            "battle_events": turn_info.get('battle_events', [])  # New structured battle events
        },
        "is_game_over": is_game_over,
        "battle_result": result,
        "game_over_url": url_for('game_over_with_underscore', result_message=result) if is_game_over else None
    }
    
    # Add PP information if available
    if updated_pp is not None:
        response_data['player_pp'] = {
            'move': move_name,
            'current_pp': updated_pp,
            'max_pp': getattr(player_move, 'max_pp', 15) if player_move else 15
        }
    
    return jsonify(response_data)

@app.route('/game_over')
def game_over_with_underscore():
    result = request.args.get('result', None)
    if result == 'forfeit':
        result_message = 'You forfeited!'
    elif result:
        # Optionally handle other result codes here
        result_message = result.replace('_', ' ').capitalize() + '!'
    else:
        result_message = 'Game Over'
    return render_template('gameover.html', result_message=result_message)


if __name__ == '__main__':
    app.run(debug=True)
