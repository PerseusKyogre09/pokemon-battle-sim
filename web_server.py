from flask import Flask, render_template, request, jsonify
from game import Game
import requests

app = Flask(__name__)
game = None  # Declare game globally to keep it persistent

def get_pokemon_data(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Pokémon {pokemon_name} not found!')

def get_pokemon_moves(pokemon_data):
    moves = pokemon_data['moves'][:4]  # Get only the first 4 moves
    selected_moves = []

    for move_entry in moves:
        move_name = move_entry['move']['name']
        move_url = move_entry['move']['url']  # Get URL for move details

        move_response = requests.get(move_url)
        if move_response.status_code == 200:
            move_data = move_response.json()
            move_power = move_data.get('power', 50)  # Default power if unavailable

            # Add the move name and power to the list
            selected_moves.append({
                'name': move_name,
                'power': move_power
            })
    
    return selected_moves

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start_game():
    global game  # Access the global game object

    player_data = get_pokemon_data('pikachu')
    opponent_data = get_pokemon_data('charmander')
    player_moves = get_pokemon_moves(player_data)
    opponent_moves = get_pokemon_moves(opponent_data)

    # Initialize the game and battle
    game = Game()
    game.start_battle(player_data, opponent_data, player_moves, opponent_moves)

    return render_template('battle.html', 
                           player_sprite=player_data['sprites']['front_default'], 
                           opponent_sprite=opponent_data['sprites']['front_default'], 
                           player_moves=player_moves,  # Pass moves to the template
                           opponent_hp=game.opponent_pokemon.current_hp,
                           player_hp=game.player_pokemon.current_hp,
                           battle_log=[])

@app.route('/move', methods=['POST'])
def move():
    global game

    if game is None or game.player_pokemon is None or game.opponent_pokemon is None:
        return jsonify({"error": "Battle not initialized! Please start the game first."}), 400

    move_name = request.json.get('move')

    game.process_turn(move_name)

    player_hp = game.player_pokemon.current_hp
    opponent_hp = game.opponent_pokemon.current_hp
    battle_log = [f"Player used {move_name}. Opponent used its move."]

    # Check if the game is over
    is_game_over = game.battle_over
    if is_game_over:
        result = game.get_battle_result()
    else:
        result = None

    return jsonify({
        "player_hp": player_hp,
        "opponent_hp": opponent_hp,
        "player_max_hp": game.player_pokemon.max_hp,
        "opponent_max_hp": game.opponent_pokemon.max_hp,
        "battle_log": battle_log,
        "is_game_over": is_game_over,
        "battle_result": result
    })


if __name__ == '__main__':
    app.run(debug=True)
