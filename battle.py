class Battle:
    def __init__(self, player_pokemon, opponent_pokemon):
        self.player_pokemon = player_pokemon
        self.opponent_pokemon = opponent_pokemon
        self.battle_log = []

    def player_attack(self, move_name):
        move = self.player_pokemon.moves.get(move_name)
        if move:
            damage, effectiveness_msg, status_message = move.use_move(self.player_pokemon, self.opponent_pokemon)
            
            # Handle miss
            if damage == 0 and effectiveness_msg and "missed" in effectiveness_msg:
                self.battle_log.append(effectiveness_msg)
                return
                
            self.opponent_pokemon.take_damage(damage)
            log_message = f"{self.player_pokemon.name} used {move_name}! {effectiveness_msg}"
            self.battle_log.append(log_message.strip())
            
            # Add status effect message if any
            if status_message:
                self.battle_log.append(status_message)
                
            if move.pp == 0:
                self.battle_log.append(f"{move_name} has no PP left!")

    def opponent_attack(self):
        move_name, move = next(iter(self.opponent_pokemon.moves.items()))  # for now AI uses first move
        damage, effectiveness_msg, status_message = move.use_move(self.opponent_pokemon, self.player_pokemon)
        
        # Handle miss
        if damage == 0 and effectiveness_msg and "missed" in effectiveness_msg:
            self.battle_log.append(effectiveness_msg)
            return
            
        self.player_pokemon.take_damage(damage)
        log_message = f"{self.opponent_pokemon.name} used {move_name}! {effectiveness_msg}"
        self.battle_log.append(log_message.strip())
        
        # Add status effect message if any
        if status_message:
            self.battle_log.append(status_message)

    def is_battle_over(self):
        return self.player_pokemon.current_hp <= 0 or self.opponent_pokemon.current_hp <= 0

    def get_battle_log(self):
        return self.battle_log
