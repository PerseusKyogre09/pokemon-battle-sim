from pokemon import Pokemon
from priority_system import PriorityResolver, create_battle_action
import random

class Game:
    def __init__(self):
        self.player_pokemon = None
        self.opponent_pokemon = None
        self.battle_over = False
        self.priority_resolver = PriorityResolver()
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
        
        # Create battle actions for priority resolution
        player_action = create_battle_action(
            self.player_pokemon, 
            player_move, 
            self.opponent_pokemon, 
            self.priority_resolver
        )
        
        opponent_action = create_battle_action(
            self.opponent_pokemon, 
            opponent_move, 
            self.player_pokemon, 
            self.priority_resolver
        ) if opponent_move else None
        
        # Resolve turn order using comprehensive priority system
        if opponent_action:
            action_order = self.priority_resolver.resolve_turn_order(player_action, opponent_action)
            player_first = action_order[0].pokemon == self.player_pokemon
        else:
            # If opponent has no move, player goes first
            action_order = [player_action]
            player_first = True
        
        turn_info['player_first'] = player_first
        turn_info['action_order'] = action_order
        
        # Add priority explanation messages before move execution
        if len(action_order) == 2:
            first_action = action_order[0]
            second_action = action_order[1]
            
            # Add turn order explanation message
            priority_explanation = self._get_priority_explanation_message(first_action, second_action)
            if priority_explanation:
                turn_info['battle_events'].append({
                    'type': 'priority_explanation',
                    'message': priority_explanation,
                    'timestamp': len(turn_info['battle_events'])
                })
        
        # Check for priority counter failures and add appropriate messages
        for action in action_order:
            if action.effective_priority == -999:  # Priority counter failed
                failure_message = self.priority_resolver.get_priority_counter_failure_message(action.move)
                turn_info['battle_events'].append({
                    'type': 'priority_counter_failure',
                    'message': f"{action.pokemon.name} used {action.move.name}! {failure_message}",
                    'target': 'player' if action.pokemon == self.player_pokemon else 'opponent',
                    'timestamp': len(turn_info['battle_events'])
                })
        
        print(f"DEBUG: Turn order resolved - Player first: {player_first}")
        
        def execute_move(attacker, defender, move, move_name, is_player_attacking, action=None):
            """Helper function to execute a move and return damage and effectiveness."""
            # Skip if no move (shouldn't happen, but just in case)
            if not move:
                return False
            
            # Check for priority counter failure
            if action and action.effective_priority == -999:
                # Priority counter failed - move doesn't execute
                print(f"DEBUG: {attacker.name}'s {move_name} failed due to priority counter conditions")
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
            
            # Add priority counter success message if applicable
            if action and action.is_priority_counter and action.effective_priority != -999:
                success_message = self.priority_resolver.get_priority_counter_success_message(
                    move, attacker.name, defender.name, action.counter_target_move.name if action.counter_target_move else "unknown move"
                )
                if success_message:
                    turn_info['battle_events'].append({
                        'type': 'priority_counter_success',
                        'message': success_message,
                        'target': 'player' if is_player_attacking else 'opponent',
                        'timestamp': len(turn_info['battle_events'])
                    })
                
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
            
            # Execute moves in priority order
            for action in action_order:
                # Skip if battle is already over
                if self.battle_over:
                    break
                
                # Skip if the attacking Pokemon has fainted
                if action.pokemon.is_fainted():
                    continue
                
                # Determine if this is the player's action
                is_player_action = action.pokemon == self.player_pokemon
                move_to_use = action.move
                move_name_to_use = move_to_use.name if move_to_use else "unknown"
                
                # Get the correct move name for display
                if is_player_action:
                    move_name_to_use = move_name
                else:
                    move_name_to_use = opponent_move_name
                
                # Execute the move
                if move_to_use:
                    target_pokemon = action.target
                    if execute_move(action.pokemon, target_pokemon, move_to_use, move_name_to_use, is_player_action, action):
                        fainted_pokemon = (target_pokemon, target_pokemon == self.player_pokemon)
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
        
        # Collect status change events from both Pokemon
        player_status_events = self.player_pokemon.get_status_change_events()
        for event in player_status_events:
            turn_info['battle_events'].append({
                'type': 'status_change',
                'event_type': event['type'],
                'status_type': event['status_type'],
                'status_name': event['status_name'],
                'pokemon': 'player',
                'pokemon_name': event['pokemon_name'],
                'timestamp': len(turn_info['battle_events'])
            })
        
        opponent_status_events = self.opponent_pokemon.get_status_change_events()
        for event in opponent_status_events:
            turn_info['battle_events'].append({
                'type': 'status_change',
                'event_type': event['type'],
                'status_type': event['status_type'],
                'status_name': event['status_name'],
                'pokemon': 'opponent',
                'pokemon_name': event['pokemon_name'],
                'timestamp': len(turn_info['battle_events'])
            })
            
        return turn_info

    def _get_priority_explanation_message(self, first_action, second_action):
        """
        Generate an explanation message for why moves executed in a specific order.
        
        Args:
            first_action: The action that goes first
            second_action: The action that goes second
            
        Returns:
            str: Explanation message, or None if no explanation needed
        """
        first_priority = first_action.effective_priority
        second_priority = second_action.effective_priority
        first_name = first_action.pokemon.name.capitalize()
        second_name = second_action.pokemon.name.capitalize()
        first_move = first_action.move.name
        second_move = second_action.move.name
        
        # Priority counter success
        if first_action.is_priority_counter and first_priority != -999:
            return f"{first_name}'s {first_move} intercepted {second_name}'s {second_move}!"
        
        # Different priority levels
        if first_priority > second_priority:
            if first_priority > 0:
                return f"{first_name}'s {first_move} has higher priority (+{first_priority}) and goes first!"
            elif second_priority < 0:
                return f"{second_name}'s {second_move} has negative priority ({second_priority}) and goes last!"
            else:
                return f"{first_name}'s {first_move} has priority (+{first_priority}) and goes first!"
        
        # Same priority, speed determines order
        elif first_priority == second_priority and first_priority != 0:
            first_speed = getattr(first_action.pokemon, 'speed', 0)
            second_speed = getattr(second_action.pokemon, 'speed', 0)
            if first_speed > second_speed:
                return f"Both moves have priority {'+' + str(first_priority) if first_priority >= 0 else str(first_priority)}, but {first_name} is faster!"
            elif second_speed > first_speed:
                return f"Both moves have priority {'+' + str(first_priority) if first_priority >= 0 else str(first_priority)}, but {first_name} got lucky!"
            else:
                return f"Both moves have priority {'+' + str(first_priority) if first_priority >= 0 else str(first_priority)}, turn order was random!"
        
        # Normal speed-based order (both priority 0)
        elif first_priority == second_priority == 0:
            first_speed = getattr(first_action.pokemon, 'speed', 0)
            second_speed = getattr(second_action.pokemon, 'speed', 0)
            if abs(first_speed - second_speed) > 10:  # Only explain if speed difference is significant
                if first_speed > second_speed:
                    return f"{first_name} is faster and goes first!"
                else:
                    return f"{first_name} got lucky and goes first!"
        
        return None

    def is_battle_over(self):
        return self.player_pokemon.is_fainted() or self.opponent_pokemon.is_fainted()

    def get_battle_result(self):
        if self.player_pokemon.is_fainted():
            return f"Your {self.player_pokemon.name.capitalize()} fainted! Opponent's {self.opponent_pokemon.name.capitalize()} wins!"
        elif self.opponent_pokemon.is_fainted():
            return f"Opponent's {self.opponent_pokemon.name.capitalize()} fainted! Your {self.player_pokemon.name.capitalize()} wins!"
        return "The battle is ongoing."
