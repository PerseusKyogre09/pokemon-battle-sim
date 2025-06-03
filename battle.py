class Battle:
    def __init__(self, player_pokemon, opponent_pokemon):
        self.player_pokemon = player_pokemon
        self.opponent_pokemon = opponent_pokemon
        self.battle_log = []
        self.turn_count = 0

    def _process_attack(self, attacker, defender, move_name, move):
        """Process an attack from one Pokémon to another."""
        # Check if the attacker can attack this turn
        can_attack, reason = attacker.can_attack()
        if not can_attack:
            self.battle_log.append(reason)
            return
            
        # Use the move
        damage, effectiveness_msg, status_message = move.use_move(attacker, defender)
        
        # Handle miss
        if damage == 0 and effectiveness_msg and "missed" in effectiveness_msg:
            self.battle_log.append(effectiveness_msg)
            return
            
        # Only deal damage if the move is not a status move and has power > 0
        if not move.is_status_move and move.power > 0:
            defender.take_damage(damage)
            log_message = f"{attacker.name} used {move_name}! {defender.name} lost {damage} HP (Now: {defender.current_hp}/{defender.max_hp})"
            self.battle_log.append(log_message.strip())
        else:
            log_message = f"{attacker.name} used {move_name}!"
            self.battle_log.append(log_message)
        
        # Add effectiveness message if any (and it's not already in the log)
        if effectiveness_msg and "used" not in effectiveness_msg:
            self.battle_log.append(effectiveness_msg)
            
        # Add status effect message if any
        if status_message:
            # Apply the status effect to the defender
            if hasattr(move, 'status_effect') and move.status_effect:
                status_effect = move.status_effect
                if isinstance(status_effect, dict):
                    status_effect = status_effect.get('type')
                if status_effect:
                    status_msg = defender.apply_status_effect(status_effect)
                    if status_msg:
                        self.battle_log.append(status_msg)
            else:
                self.battle_log.append(status_message)
            
        # Handle end of turn status effects for defender
        if not move.is_status_move or move.power > 0:  # Only trigger if not a pure status move
            status_msg = defender.end_turn_status_effects()
            if status_msg:
                self.battle_log.append(status_msg)
        
        if move.pp == 0:
            self.battle_log.append(f"{move_name} has no PP left!")
    
    def player_attack(self, move_name):
        """Player's turn to attack."""
        move = self.player_pokemon.moves.get(move_name)
        if move:
            # Handle player's turn start status effects
            player_status_msg = self.player_pokemon.end_turn_status_effects()
            if player_status_msg:
                self.battle_log.append(player_status_msg)
                
            # Process the attack
            self._process_attack(self.player_pokemon, self.opponent_pokemon, move_name, move)
            
            # Only process opponent's turn if they're not fainted
            if not self.is_battle_over():
                self.opponent_turn()
    
    def opponent_turn(self):
        """Handle the opponent's entire turn."""
        # Handle opponent's turn start status effects
        opponent_status_msg = self.opponent_pokemon.end_turn_status_effects()
        if opponent_status_msg:
            self.battle_log.append(opponent_status_msg)
            
        # Only attack if not fainted from status effects
        if not self.is_battle_over():
            # Simple AI: choose a random move
            import random
            move_name = random.choice(list(self.opponent_pokemon.moves.keys()))
            move = self.opponent_pokemon.moves[move_name]
            self._process_attack(self.opponent_pokemon, self.player_pokemon, move_name, move)
    
    def opponent_attack(self):
        """Legacy method - use opponent_turn() instead."""
        self.opponent_turn()

    def is_battle_over(self):
        return self.player_pokemon.current_hp <= 0 or self.opponent_pokemon.current_hp <= 0

    def get_battle_log(self):
        return self.battle_log
        
    def end_turn(self):
        """Handle end-of-turn effects."""
        self.turn_count += 1
        
        # Process end-of-turn status effects for both Pokémon
        player_status_msg = self.player_pokemon.end_turn_status_effects()
        if player_status_msg:
            self.battle_log.append(player_status_msg)
            
        opponent_status_msg = self.opponent_pokemon.end_turn_status_effects()
        if opponent_status_msg:
            self.battle_log.append(opponent_status_msg)
            
        # Check for battle end conditions
        if self.player_pokemon.current_hp <= 0:
            self.battle_log.append(f"{self.player_pokemon.name} fainted!")
        elif self.opponent_pokemon.current_hp <= 0:
            self.battle_log.append(f"{self.opponent_pokemon.name} fainted!")
