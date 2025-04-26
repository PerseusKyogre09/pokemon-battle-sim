from pokemon import Pokemon

class Game:
    def __init__(self):
        self.player_pokemon = None
        self.opponent_pokemon = None
        self.battle_over = False

    def start_battle(self, player_data, opponent_data, player_moves, opponent_moves):
        self.player_pokemon = Pokemon(player_data['name'], player_data['types'][0]['type']['name'], player_data['sprites']['front_default'], player_data['stats'], player_moves)
        self.opponent_pokemon = Pokemon(opponent_data['name'], opponent_data['types'][0]['type']['name'], opponent_data['sprites']['front_default'], opponent_data['stats'], opponent_moves)

    def process_turn(self, move_name):
        # Get player's selected move
        player_move = self.player_pokemon.moves.get(move_name)
        if not player_move:
            return  # Invalid move selected
            
        # Get opponent's move (AI always picks first move)
        opponent_move_name, opponent_move = next(iter(self.opponent_pokemon.moves.items()))
        
        # Determine who goes first based on speed
        if self.player_pokemon.speed >= self.opponent_pokemon.speed:
            # Player goes first
            player_damage = player_move.use_move()
            self.opponent_pokemon.take_damage(player_damage)
                
            # Check if opponent fainted
            if self.opponent_pokemon.is_fainted():
                self.battle_over = True
                return
            
            # Opponent goes second
            opponent_damage = opponent_move.use_move()
            self.player_pokemon.take_damage(opponent_damage)
        else:
            # Opponent goes first
            opponent_damage = opponent_move.use_move()
            self.player_pokemon.take_damage(opponent_damage)
                
            # Check if player fainted
            if self.player_pokemon.is_fainted():
                self.battle_over = True
                return
            
            # Player goes second
            player_damage = player_move.use_move()
            self.opponent_pokemon.take_damage(player_damage)

        # Check if battle is over
        self.battle_over = self.is_battle_over()

    def is_battle_over(self):
        return self.player_pokemon.is_fainted() or self.opponent_pokemon.is_fainted()

    def get_battle_result(self):
        if self.player_pokemon.is_fainted():
            return "You lost!"
        elif self.opponent_pokemon.is_fainted():
            return "You won!"
        return "The battle is ongoing."
