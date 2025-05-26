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
        # Fetch Pokémon data from the PokéAPI
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}')
        if response.status_code == 200:
            pokemon_data = response.json()
            
            # Get the cry URL from the response
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
            
            # Try to get move data from our dataset
            move_power = data_loader.get_move_power(clean_move_name)
            move_type = data_loader.get_move_type(clean_move_name)
            
            # If not found in dataset, fetch from PokeAPI
            if not move_power or not move_type:
                try:
                    move_url = f'https://pokeapi.co/api/v2/move/{clean_move_name}'
                    move_response = requests.get(move_url)
                    if move_response.status_code == 200:
                        move_data = move_response.json()
                        move_power = move_data.get('power', 75)  # Default to 75 for strategic moves
                        move_type = move_data.get('type', {}).get('name', 'normal')
                except:
                    # If API call fails, use reasonable defaults
                    move_power = 75
                    move_type = 'normal'
            
            selected_moves.append({
                'name': move_name,
                'power': move_power or 75,  # Ensure we have a power value
                'type': move_type or 'normal'  # Ensure we have a type
            })
        return selected_moves
    
    # Second, try to get moves from our TypeScript dataset
    dataset_moves = data_loader.get_pokemon_moves(pokemon_name, 4)
    
    if dataset_moves:
        selected_moves = []
        for move_name in dataset_moves:
            move_power = data_loader.get_move_power(move_name)
            move_type = data_loader.get_move_type(move_name)
            selected_moves.append({
                'name': move_name,
                'power': move_power or 50,
                'type': move_type or 'normal'
            })
        return selected_moves
    
    # Fallback to PokeAPI if no strategic or dataset moves
    moves = pokemon_data['moves'][:4]  # Gets first 4 moves in the database
    selected_moves = []

    for move_entry in moves:
        move_name = move_entry['move']['name']
        move_url = move_entry['move']['url']  # URL for more details about the move

        move_response = requests.get(move_url)
        if move_response.status_code == 200:
            move_data = move_response.json()
            move_power = move_data.get('power', 50)
            move_type = move_data.get('type', {}).get('name', 'normal')
            selected_moves.append({
                'name': move_name,
                'power': move_power,
                'type': move_type
            })
    
    return selected_moves

@app.route('/')
def index():
    return render_template('index.html')

#start webpage
@app.route('/start')
def start_game():
    global game

    player_data = get_pokemon_data('mewtwo')
    opponent_data = get_pokemon_data('conkeldurr')
    player_moves = get_pokemon_moves(player_data)
    opponent_moves = get_pokemon_moves(opponent_data)

    game = Game()
    game.start_battle(player_data, opponent_data, player_moves, opponent_moves)

    return render_template('battle.html', 
                           player_sprite=player_data['sprites']['front_default'], 
                           opponent_sprite=opponent_data['sprites']['front_default'], 
                           player_moves=player_moves,  # Pass moves to the template
                           opponent_hp=game.opponent_pokemon.current_hp,
                           player_hp=game.player_pokemon.current_hp,
                           battle_log=[],
                           player_data=player_data,
                           opponent_data=opponent_data)

#for using moves
@app.route('/move', methods=['POST'])
def move():
    global game

    if game is None or game.player_pokemon is None or game.opponent_pokemon is None:
        return jsonify({"error": "Battle not initialized! Please start the game first."}), 400

    move_name = request.json.get('move')
    
    # Store the opponent's move name before processing the turn
    opponent_move_name = next(iter(game.opponent_pokemon.moves.keys()))
    
    # Process the turn with the player's move
    game.process_turn(move_name)

    player_hp = game.player_pokemon.current_hp
    opponent_hp = game.opponent_pokemon.current_hp
    battle_log = [f"Player used {move_name}. Opponent used {opponent_move_name}."]

    is_game_over = game.battle_over
    result = game.get_battle_result() if is_game_over else None

    return jsonify({
        "player_hp": player_hp,
        "opponent_hp": opponent_hp,
        "player_max_hp": game.player_pokemon.max_hp,
        "opponent_max_hp": game.opponent_pokemon.max_hp,
        "battle_log": battle_log,
        "is_game_over": is_game_over,
        "battle_result": result,
        "opponent_move": opponent_move_name,
        "game_over_url": url_for('game_over_with_underscore', result_message=result) if is_game_over else None
    })

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
