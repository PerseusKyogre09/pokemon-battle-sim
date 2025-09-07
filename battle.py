class Battle:
    def __init__(self, player_pokemon, opponent_pokemon):
        self.player_pokemon = player_pokemon
        self.opponent_pokemon = opponent_pokemon
        self.battle_log = []
        self.turn_count = 0

    def _process_turn_start_effects(self, pokemon) -> list:
        messages = []
        try:
            if hasattr(pokemon, 'process_turn_start_effects') and callable(getattr(pokemon, 'process_turn_start_effects', None)):
                status_messages = pokemon.process_turn_start_effects()
                if isinstance(status_messages, list):
                    messages.extend(status_messages)
                elif status_messages:
                    messages.append(str(status_messages))
        except Exception as e:
            print(f"ERROR: Exception in _process_turn_start_effects for {getattr(pokemon, 'name', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
        return messages

    def _process_turn_end_effects(self, pokemon) -> list:
        messages = []
        try:
            if hasattr(pokemon, 'process_turn_end_effects') and callable(getattr(pokemon, 'process_turn_end_effects', None)):
                status_messages = pokemon.process_turn_end_effects()
                if isinstance(status_messages, list):
                    messages.extend(status_messages)
                elif status_messages:  # Handle single string message
                    messages.append(str(status_messages))
            elif hasattr(pokemon, 'end_turn_status_effects') and callable(getattr(pokemon, 'end_turn_status_effects', None)):
                # Fallback to legacy method
                status_msg = pokemon.end_turn_status_effects()
                if status_msg:
                    messages.append(str(status_msg))
        except Exception as e:
            print(f"ERROR: Exception in _process_turn_end_effects for {getattr(pokemon, 'name', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
        return messages

    def _can_use_move(self, pokemon) -> tuple:
        try:
            if hasattr(pokemon, 'can_use_move') and callable(getattr(pokemon, 'can_use_move', None)):
                result = pokemon.can_use_move()
                if isinstance(result, tuple) and len(result) == 2:
                    return result
                else:
                    print(f"WARNING: can_use_move returned invalid result: {result}")
                    return True, ""
            elif hasattr(pokemon, 'can_attack') and callable(getattr(pokemon, 'can_attack', None)):
                # Fallback to legacy method
                result = pokemon.can_attack()
                if isinstance(result, tuple) and len(result) == 2:
                    return result
                else:
                    print(f"WARNING: can_attack returned invalid result: {result}")
                    return True, ""
        except Exception as e:
            print(f"ERROR: Exception in _can_use_move for {getattr(pokemon, 'name', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
        
        # Default to allowing move if all else fails
        return True, ""

    def _process_attack(self, attacker, defender, move_name, move):
        # Check if the attacker can use a move this turn
        can_use_move, reason = self._can_use_move(attacker)
        if not can_use_move:
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
        
        # Add effectiveness message
        if effectiveness_msg and "used" not in effectiveness_msg:
            self.battle_log.append(effectiveness_msg)
            
        # Process status effects from the move
        self._process_move_status_effects(move, attacker, defender, status_message)
        
        if move.pp == 0:
            self.battle_log.append(f"{move_name} has no PP left!")

    def _process_move_status_effects(self, move, attacker, defender, status_message):
        # Handle status effects from the new move system
        if hasattr(move, '_apply_status_effects'):
            status_messages = move._apply_status_effects(attacker, defender)
            for msg in status_messages:
                if msg:
                    self.battle_log.append(msg)
        
        # Always add the status message if it exists (includes healing messages)
        if status_message:
            # Handle legacy status effect application for moves with status_effect
            if hasattr(move, 'status_effect') and move.status_effect and defender:
                status_effect = move.status_effect
                if isinstance(status_effect, dict):
                    status_effect = status_effect.get('type')
                if status_effect:
                    status_msg = defender.apply_status_effect(status_effect)
                    if status_msg:
                        self.battle_log.append(status_msg)
            
            # Always add the status message (which includes healing messages)
            self.battle_log.append(status_message)
    
    def player_attack(self, move_name):
        move = self.player_pokemon.moves.get(move_name)
        if move:
            # Process turn-start status effects for player
            turn_start_messages = self._process_turn_start_effects(self.player_pokemon)
            for msg in turn_start_messages:
                if msg:
                    self.battle_log.append(msg)
            
            # Check if player fainted from turn-start effects
            if self.is_battle_over():
                return
                
            # Process the attack
            self._process_attack(self.player_pokemon, self.opponent_pokemon, move_name, move)
            
            # Process turn-end status effects for player
            turn_end_messages = self._process_turn_end_effects(self.player_pokemon)
            for msg in turn_end_messages:
                if msg:
                    self.battle_log.append(msg)
            
            # Only process opponent's turn if they're not fainted
            if not self.is_battle_over():
                self.opponent_turn()
    
    def opponent_turn(self):
        # Process turn-start status effects for opponent
        turn_start_messages = self._process_turn_start_effects(self.opponent_pokemon)
        for msg in turn_start_messages:
            if msg:
                self.battle_log.append(msg)
        
        # Check if opponent fainted from turn-start effects
        if self.is_battle_over():
            return
            
        # Only attack if not fainted from status effects
        if not self.is_battle_over():
            # Simple AI: choose a random move
            import random
            move_name = random.choice(list(self.opponent_pokemon.moves.keys()))
            move = self.opponent_pokemon.moves[move_name]
            self._process_attack(self.opponent_pokemon, self.player_pokemon, move_name, move)
            
        # Process turn-end status effects for opponent
        turn_end_messages = self._process_turn_end_effects(self.opponent_pokemon)
        for msg in turn_end_messages:
            if msg:
                self.battle_log.append(msg)
    
    def opponent_attack(self):
        self.opponent_turn()

    def is_battle_over(self):
        return self.player_pokemon.current_hp <= 0 or self.opponent_pokemon.current_hp <= 0

    def get_battle_log(self):
        return self.battle_log
        
    def end_turn(self):
        self.turn_count += 1
        
        # Process end-of-turn status effects for both Pokémon
        player_messages = self._process_turn_end_effects(self.player_pokemon)
        for msg in player_messages:
            if msg:
                self.battle_log.append(msg)
            
        opponent_messages = self._process_turn_end_effects(self.opponent_pokemon)
        for msg in opponent_messages:
            if msg:
                self.battle_log.append(msg)
            
        # Check for battle end conditions
        if self.player_pokemon.current_hp <= 0:
            self.battle_log.append(f"{self.player_pokemon.name} fainted!")
        elif self.opponent_pokemon.current_hp <= 0:
            self.battle_log.append(f"{self.opponent_pokemon.name} fainted!")
