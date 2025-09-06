from pokemon import Pokemon

class Game:
    def __init__(self):
        self.player_pokemon = None
        self.opponent_pokemon = None
        self.battle_over = False
    def start_battle(self, player_data, opponent_data, player_moves, opponent_moves):
        # Get player's back sprite (prefer Gen 5 animated, fallback to default)
        player_sprite = (
            player_data['sprites'].get('versions', {})
            .get('generation-v', {})
            .get('black-white', {})
            .get('animated', {})
            .get('back_default') or 
            player_data['sprites'].get('back_default')
        )
        
        # Get opponent's front sprite (prefer Gen 5 animated, fallback to default)
        opponent_sprite = (
            opponent_data['sprites'].get('versions', {})
            .get('generation-v', {})
            .get('black-white', {})
            .get('animated', {})
            .get('front_default') or 
            opponent_data['sprites'].get('front_default')
        )
        
        # Extract types for both Pokémon
        player_types = [t['type']['name'] for t in player_data['types']]
        opponent_types = [t['type']['name'] for t in opponent_data['types']]
        
        print(f"DEBUG: Player {player_data['name']} types: {player_types}")
        print(f"DEBUG: Opponent {opponent_data['name']} types: {opponent_types}")
        
        # Create Pokémon instances with the selected sprites and types
        self.player_pokemon = Pokemon(
            player_data['name'], 
            player_types,  # Pass all types as a list
            player_sprite, 
            player_data['stats'], 
            player_moves
        )
        self.opponent_pokemon = Pokemon(
            opponent_data['name'], 
            opponent_types,  # Pass all types as a list
            opponent_sprite, 
            opponent_data['stats'], 
            opponent_moves
        )
        
        print(f"DEBUG: Player Pokémon created with types: {self.player_pokemon.types}")
        print(f"DEBUG: Opponent Pokémon created with types: {self.opponent_pokemon.types}")

    def process_turn(self, move_name):
        turn_info = {
            'player_move': move_name,
            'player_damage': 0,
            'opponent_damage': 0,
            'battle_events': []  # Will store all battle events in order
        }
        
        # Process turn-start effects for both Pokemon
        player_start_messages = self.player_pokemon.process_turn_start_effects()
        for msg in player_start_messages:
            if msg:
                turn_info['battle_events'].append({
                    'type': 'status',
                    'message': msg,
                    'target': 'player',
                    'timestamp': len(turn_info['battle_events'])
                })
        
        opponent_start_messages = self.opponent_pokemon.process_turn_start_effects()
        for msg in opponent_start_messages:
            if msg:
                turn_info['battle_events'].append({
                    'type': 'status',
                    'message': msg,
                    'target': 'opponent',
                    'timestamp': len(turn_info['battle_events'])
                })
        
        # Check if either Pokemon fainted from turn-start effects
        if self.player_pokemon.current_hp <= 0:
            self.battle_over = True
            turn_info['battle_events'].append({
                'type': 'faint',
                'pokemon_name': self.player_pokemon.name,
                'is_player': True,
                'timestamp': len(turn_info['battle_events'])
            })
            return turn_info
        elif self.opponent_pokemon.current_hp <= 0:
            self.battle_over = True
            turn_info['battle_events'].append({
                'type': 'faint',
                'pokemon_name': self.opponent_pokemon.name,
                'is_player': False,
                'timestamp': len(turn_info['battle_events'])
            })
            return turn_info
        
        # Get player's selected move
        player_move = self.player_pokemon.moves.get(move_name)
        if not player_move or player_move.pp <= 0:
            return turn_info  # Invalid move or no PP left
                
        # Get opponent's move (AI always picks first move)
        opponent_move_name, opponent_move = next(iter(self.opponent_pokemon.moves.items()))
        turn_info['opponent_move'] = opponent_move_name
        
        # Check if opponent has PP left
        if opponent_move and opponent_move.pp <= 0:
            # If opponent has no PP, they struggle
            opponent_move = None
            turn_info['battle_events'].append({
                'type': 'status',
                'message': f"{self.opponent_pokemon.name} has no PP left for {opponent_move_name}!",
                'target': 'opponent',
                'timestamp': len(turn_info['battle_events'])
            })
        
        # Determine who goes first based on speed
        if self.player_pokemon.speed > self.opponent_pokemon.speed:
            player_first = True
        elif self.player_pokemon.speed < self.opponent_pokemon.speed:
            player_first = False
        else:
            # In case of tie, random choice (50/50)
            import random
            player_first = random.choice([True, False])
            
        turn_info['player_first'] = player_first
        print(f"DEBUG: Turn order - Player first: {player_first} (Player speed: {self.player_pokemon.speed}, Opponent speed: {self.opponent_pokemon.speed})")
        
        def execute_move(attacker, defender, move, move_name, is_player_attacking):
            """Helper function to execute a move and return damage and effectiveness."""
            # Skip if no move (shouldn't happen, but just in case)
            if not move:
                return False
            
            # Check if the attacker can use a move this turn
            can_use_move, prevention_message = attacker.can_use_move()
            if not can_use_move:
                # Pokemon is prevented from using move
                turn_info['battle_events'].append({
                    'type': 'status',
                    'message': prevention_message,
                    'target': 'player' if is_player_attacking else 'opponent',
                    'timestamp': len(turn_info['battle_events'])
                })
                print(f"DEBUG: {attacker.name} is prevented from using {move_name}: {prevention_message}")
                return False
                
            damage, effectiveness_msg, status_message = move.use_move(attacker, defender)
            prev_hp = defender.current_hp
            defender.take_damage(damage)
            actual_damage = prev_hp - defender.current_hp
            
            # Log the move and damage
            if is_player_attacking:
                turn_info['player_damage'] = actual_damage
            else:
                turn_info['opponent_damage'] = actual_damage
            
            # Create move event with status message included
            move_event = {
                'type': 'move',
                'attacker_name': attacker.name,
                'defender_name': defender.name,
                'move': move_name,
                'damage': actual_damage,
                'is_player': is_player_attacking,
                'attacker_hp': attacker.current_hp,
                'defender_hp': defender.current_hp,
                'attacker_max_hp': attacker.max_hp,
                'defender_max_hp': defender.max_hp,
                'timestamp': len(turn_info['battle_events']),
                'status_message': status_message  # Include status message in move event
            }
            turn_info['battle_events'].append(move_event)
            
            # Add effectiveness as a separate event if there is a message
            if effectiveness_msg:
                effectiveness_event = {
                    'type': 'effectiveness',
                    'message': effectiveness_msg,
                    'is_player': is_player_attacking,
                    'timestamp': len(turn_info['battle_events'])
                }
                turn_info['battle_events'].append(effectiveness_event)
            
            print(f"DEBUG: {attacker.name} used {move_name}! {defender.name} lost {actual_damage} HP (Now: {defender.current_hp}/{defender.max_hp})")
            if effectiveness_msg:
                print(f"DEBUG: {effectiveness_msg}")
            
            # Decrement PP after successful move
            move.pp -= 1
            
            # Return whether the defender fainted
            return defender.current_hp <= 0
        
        try:
            fainted_pokemon = None
            
            if player_first:
                # Player goes first
                if execute_move(self.player_pokemon, self.opponent_pokemon, player_move, move_name, True):
                    fainted_pokemon = (self.opponent_pokemon, False)  # (pokemon, is_player)
                    self.battle_over = True
                
                # Opponent goes second if they have PP and player didn't faint
                if opponent_move and not self.battle_over and not self.player_pokemon.is_fainted():
                    if execute_move(self.opponent_pokemon, self.player_pokemon, opponent_move, opponent_move_name, False):
                        fainted_pokemon = (self.player_pokemon, True)
                        self.battle_over = True
            else:
                # Opponent goes first if they have PP
                if opponent_move:
                    if execute_move(self.opponent_pokemon, self.player_pokemon, opponent_move, opponent_move_name, False):
                        fainted_pokemon = (self.player_pokemon, True)
                        self.battle_over = True
                
                # Player goes second if not fainted
                if not self.battle_over and not self.opponent_pokemon.is_fainted():
                    if execute_move(self.player_pokemon, self.opponent_pokemon, player_move, move_name, True):
                        fainted_pokemon = (self.opponent_pokemon, False)
                        self.battle_over = True
            
            # Add faint event after all other events if a Pokémon fainted
            if fainted_pokemon:
                pokemon, is_player = fainted_pokemon
                faint_event = {
                    'type': 'faint',
                    'pokemon_name': pokemon.name,
                    'is_player': is_player,
                    'timestamp': len(turn_info['battle_events'])
                }
                turn_info['battle_events'].append(faint_event)
                print(f"DEBUG: {pokemon.name} fainted!")
        except Exception as e:
            print(f"Error during turn processing: {e}")
        
        # Process turn-end effects for both Pokemon
        if not self.battle_over:
            player_end_messages = self.player_pokemon.process_turn_end_effects()
            for msg in player_end_messages:
                if msg:
                    turn_info['battle_events'].append({
                        'type': 'status',
                        'message': msg,
                        'target': 'player',
                        'timestamp': len(turn_info['battle_events'])
                    })
            
            opponent_end_messages = self.opponent_pokemon.process_turn_end_effects()
            for msg in opponent_end_messages:
                if msg:
                    turn_info['battle_events'].append({
                        'type': 'status',
                        'message': msg,
                        'target': 'opponent',
                        'timestamp': len(turn_info['battle_events'])
                    })
            
            # Check if either Pokemon fainted from turn-end effects
            if self.player_pokemon.current_hp <= 0 and not self.battle_over:
                self.battle_over = True
                turn_info['battle_events'].append({
                    'type': 'faint',
                    'pokemon_name': self.player_pokemon.name,
                    'is_player': True,
                    'timestamp': len(turn_info['battle_events'])
                })
                print(f"DEBUG: {self.player_pokemon.name} fainted from status effects!")
            elif self.opponent_pokemon.current_hp <= 0 and not self.battle_over:
                self.battle_over = True
                turn_info['battle_events'].append({
                    'type': 'faint',
                    'pokemon_name': self.opponent_pokemon.name,
                    'is_player': False,
                    'timestamp': len(turn_info['battle_events'])
                })
                print(f"DEBUG: {self.opponent_pokemon.name} fainted from status effects!")
            
        return turn_info

    def is_battle_over(self):
        return self.player_pokemon.is_fainted() or self.opponent_pokemon.is_fainted()

    def get_battle_result(self):
        if self.player_pokemon.is_fainted():
            return f"Your {self.player_pokemon.name.capitalize()} fainted! Opponent's {self.opponent_pokemon.name.capitalize()} wins!"
        elif self.opponent_pokemon.is_fainted():
            return f"Opponent's {self.opponent_pokemon.name.capitalize()} fainted! Your {self.player_pokemon.name.capitalize()} wins!"
        return "The battle is ongoing."
