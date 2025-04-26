<<<<<<< HEAD
from flask import Flask, render_template, request, jsonify
=======
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
from game import Game
import requests

app = Flask(__name__)
<<<<<<< HEAD
game = None  # Declare game globally to keep it persistent

def get_pokemon_data(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}'
=======
game = None

@app.route('/music/<path:filename>')
def music(filename):
    return send_from_directory(app.root_path + '/music', filename)

def get_pokemon_data(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}' #pokeapi for pokemon data
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Pokémon {pokemon_name} not found!')

def get_pokemon_moves(pokemon_data):
<<<<<<< HEAD
    moves = pokemon_data['moves'][:4]  # Get only the first 4 moves
=======
    moves = pokemon_data['moves'][:4]  #gets first 4 move in the database
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
    selected_moves = []

    for move_entry in moves:
        move_name = move_entry['move']['name']
<<<<<<< HEAD
        move_url = move_entry['move']['url']  # Get URL for move details
=======
        move_url = move_entry['move']['url']  #url for more details abt the move (bp, pp etc)
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396

        move_response = requests.get(move_url)
        if move_response.status_code == 200:
            move_data = move_response.json()
<<<<<<< HEAD
            move_power = move_data.get('power', 50)  # Default power if unavailable

            # Add the move name and power to the list
=======
            move_power = move_data.get('power', 50)  #failsafe if move isnt in the database (for now so webpage doesnt crash)
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
            selected_moves.append({
                'name': move_name,
                'power': move_power
            })
    
    return selected_moves

@app.route('/')
def index():
    return render_template('index.html')

<<<<<<< HEAD
@app.route('/start')
def start_game():
    global game  # Access the global game object
=======
#start webpage
@app.route('/start')
def start_game():
    global game
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396

    player_data = get_pokemon_data('pikachu')
    opponent_data = get_pokemon_data('charmander')
    player_moves = get_pokemon_moves(player_data)
    opponent_moves = get_pokemon_moves(opponent_data)

<<<<<<< HEAD
    # Initialize the game and battle
=======
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
    game = Game()
    game.start_battle(player_data, opponent_data, player_moves, opponent_moves)

    return render_template('battle.html', 
                           player_sprite=player_data['sprites']['front_default'], 
                           opponent_sprite=opponent_data['sprites']['front_default'], 
                           player_moves=player_moves,  # Pass moves to the template
                           opponent_hp=game.opponent_pokemon.current_hp,
                           player_hp=game.player_pokemon.current_hp,
                           battle_log=[])

<<<<<<< HEAD
=======
#for using moves
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
@app.route('/move', methods=['POST'])
def move():
    global game

    if game is None or game.player_pokemon is None or game.opponent_pokemon is None:
        return jsonify({"error": "Battle not initialized! Please start the game first."}), 400

    move_name = request.json.get('move')
<<<<<<< HEAD

=======
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
    game.process_turn(move_name)

    player_hp = game.player_pokemon.current_hp
    opponent_hp = game.opponent_pokemon.current_hp
    battle_log = [f"Player used {move_name}. Opponent used its move."]

<<<<<<< HEAD
    # Check if the game is over
    is_game_over = game.battle_over
    if is_game_over:
        result = game.get_battle_result()
    else:
        result = None
=======
    is_game_over = game.battle_over
    result = game.get_battle_result() if is_game_over else None

    if is_game_over:
        # Redirect to the game over page with result message
        return redirect(url_for('game_over', result_message=result))
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396

    return jsonify({
        "player_hp": player_hp,
        "opponent_hp": opponent_hp,
        "player_max_hp": game.player_pokemon.max_hp,
        "opponent_max_hp": game.opponent_pokemon.max_hp,
        "battle_log": battle_log,
        "is_game_over": is_game_over,
        "battle_result": result
    })

<<<<<<< HEAD
=======
@app.route('/gameover')
def game_over():
    result_message = request.args.get('result_message', 'Game Over')
    return render_template('gameover.html', result_message=result_message)

>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396

if __name__ == '__main__':
    app.run(debug=True)
