from pokemon import Pokemon

class Game:
    def __init__(self):
        self.player_pokemon = None
        self.opponent_pokemon = None
        self.battle_over = False

    def start_battle(self, player_data, opponent_data, player_moves, opponent_moves):
        # Initialize Pokémon objects with moves
        self.player_pokemon = Pokemon(player_data['name'], player_data['types'][0]['type']['name'], player_data['sprites']['front_default'], player_data['stats'], player_moves)
        self.opponent_pokemon = Pokemon(opponent_data['name'], opponent_data['types'][0]['type']['name'], opponent_data['sprites']['front_default'], opponent_data['stats'], opponent_moves)

    def process_turn(self, move_name):
        player_move = self.player_pokemon.moves.get(move_name)
        opponent_move = next(iter(self.opponent_pokemon.moves.values()))  # Simple AI: always picks the first move

        # Player's attack
        player_move = self.player_pokemon.moves.get(move_name)
        if player_move:
            damage = player_move.use_move()
            self.opponent_pokemon.take_damage(damage)

        # Check if opponent has fainted
        if self.opponent_pokemon.is_fainted():
            self.battle_over = True
            return

        # Opponent's attack
        opponent_move = next(iter(self.opponent_pokemon.moves.values()))
        if opponent_move:
            damage = opponent_move.use_move()
            self.player_pokemon.take_damage(damage)

        # Check if player has fainted
        if self.player_pokemon.is_fainted():
            self.battle_over = True

        # Determine which Pokémon moves first based on speed
        if self.player_pokemon.speed >= self.opponent_pokemon.speed:
            # Player's move first
            if player_move:
                damage = player_move.use_move()
                self.opponent_pokemon.take_damage(damage)
                if self.opponent_pokemon.is_fainted():
                    return

            # Opponent's move second
            if opponent_move:
                damage = opponent_move.use_move()
                self.player_pokemon.take_damage(damage)
        else:
            # Opponent's move first
            if opponent_move:
                damage = opponent_move.use_move()
                self.player_pokemon.take_damage(damage)
                if self.player_pokemon.is_fainted():
                    return

            # Player's move second
            if player_move:
                damage = player_move.use_move()
                self.opponent_pokemon.take_damage(damage)

        # Check if the battle is over
        self.battle_over = self.is_battle_over()

    def is_battle_over(self):
        return self.player_pokemon.is_fainted() or self.opponent_pokemon.is_fainted()

    def get_battle_result(self):
        if self.player_pokemon.is_fainted():
            return "You lost!"
        elif self.opponent_pokemon.is_fainted():
            return "You won!"
        return "The battle is ongoing."
