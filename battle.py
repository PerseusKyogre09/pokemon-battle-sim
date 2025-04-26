class Battle:
    def __init__(self, player_pokemon, opponent_pokemon):
        self.player_pokemon = player_pokemon
        self.opponent_pokemon = opponent_pokemon
        self.battle_log = []

    def player_attack(self, move_name):
        move = self.player_pokemon.moves.get(move_name)
        if move:
            damage = move.use_move()
            self.opponent_pokemon.current_hp -= damage
            self.battle_log.append(f"{self.player_pokemon.name} used {move_name}! It dealt {damage} damage.")
            if move.pp == 0:
                self.battle_log.append(f"{move_name} has no PP left!")

    def opponent_attack(self):
<<<<<<< HEAD
        move_name, move = next(iter(self.opponent_pokemon.moves.items()))  # Simple opponent AI, always uses first move
=======
        move_name, move = next(iter(self.opponent_pokemon.moves.items())) #for now AI uses first move
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
        damage = move.use_move()
        self.player_pokemon.current_hp -= damage
        self.battle_log.append(f"{self.opponent_pokemon.name} used {move_name}! It dealt {damage} damage.")

    def is_battle_over(self):
        return self.player_pokemon.current_hp <= 0 or self.opponent_pokemon.current_hp <= 0

    def get_battle_log(self):
        return self.battle_log
