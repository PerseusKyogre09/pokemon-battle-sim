from pokemon import Pokemon
from priority_system import PriorityResolver, create_battle_action
import random

class Game:
    def __init__(self):
        self.player_pokemon = None
        self.opponent_pokemon = None
        self.battle_over = False
        self.priority_resolver = PriorityResolver()
    def start_battle(self, player_data, opponent_data, player_moves, opponent_moves, player_ability="noability", opponent_ability="noability"):
        player_sprite = (
            player_data['sprites'].get('versions', {})
            .get('generation-v', {})
            .get('black-white', {})
            .get('animated', {})
            .get('back_default') or 
            player_data['sprites'].get('back_default')
        )
        
        opponent_sprite = (
            opponent_data['sprites'].get('versions', {})
            .get('generation-v', {})
            .get('black-white', {})
            .get('animated', {})
            .get('front_default') or 
            opponent_data['sprites'].get('front_default')
        )
        
        player_types = [t['type']['name'] for t in player_data['types']]
        opponent_types = [t['type']['name'] for t in opponent_data['types']]
        
        self.player_pokemon = Pokemon(
            player_data['name'], 
            player_types,
            player_sprite, 
            player_data['stats'], 
            player_moves,
            ability=player_ability
        )
        self.player_pokemon.is_player = True
        
        self.opponent_pokemon = Pokemon(
            opponent_data['name'], 
            opponent_types,
            opponent_sprite, 
            opponent_data['stats'], 
            opponent_moves,
            ability=opponent_ability
        )
        self.opponent_pokemon.is_player = False
        
        # Trigger switch-in effects (abilities like Intimidate)
        messages = []
        messages.extend(self.player_pokemon.on_switch_in(self.opponent_pokemon))
        messages.extend(self.opponent_pokemon.on_switch_in(self.player_pokemon))
        return messages

    def process_turn(self, move_name):
        # Reset turn-based volatile statuses
        STALLING_STATUSES = ['protect', 'spikyshield', 'banefulbunker', 'kingsshield', 'obstruct', 'silktrap', 'burningbulwark', 'endure']
        if self.player_pokemon:
            self.player_pokemon.is_flinched = False
            for status in STALLING_STATUSES:
                self.player_pokemon.volatile_statuses.discard(status)
        if self.opponent_pokemon:
            self.opponent_pokemon.is_flinched = False
            for status in STALLING_STATUSES:
                self.opponent_pokemon.volatile_statuses.discard(status)
            
        turn_info = {
            'player_move': move_name,
            'player_damage': 0,
            'opponent_damage': 0,
            'battle_events': []
        }
        
        player_start_messages = self.player_pokemon.process_turn_start_effects()
        for msg in player_start_messages:
            if msg:
                turn_info['battle_events'].append({
                    'type': 'status',
                    'message': msg,
                    'target': 'player',
                    'pokemon_hp': self.player_pokemon.current_hp,
                    'status_effects': self.player_pokemon.get_status_display(),
                    'timestamp': len(turn_info['battle_events'])
                })
        
        opponent_start_messages = self.opponent_pokemon.process_turn_start_effects()
        for msg in opponent_start_messages:
            if msg:
                turn_info['battle_events'].append({
                    'type': 'status',
                    'message': msg,
                    'target': 'opponent',
                    'pokemon_hp': self.opponent_pokemon.current_hp,
                    'status_effects': self.opponent_pokemon.get_status_display(),
                    'timestamp': len(turn_info['battle_events'])
                })
        
        if self.player_pokemon.current_hp <= 0:
            # Trigger fainted abilities (e.g. Aftermath)
            faint_events = self.player_pokemon.on_faint(self.opponent_pokemon)
            for event in faint_events:
                turn_info['battle_events'].append({
                    'type': 'ability',
                    'ability_name': event.get('ability_name'),
                    'pokemon_name': event.get('pokemon_name'),
                    'message': event.get('message'),
                    'target': 'player',
                    'timestamp': len(turn_info['battle_events'])
                })
            
            self.battle_over = True
            turn_info['battle_events'].append({
                'type': 'faint',
                'pokemon_name': self.player_pokemon.name,
                'is_player': True,
                'timestamp': len(turn_info['battle_events'])
            })
            return turn_info
        elif self.opponent_pokemon.current_hp <= 0:
            # Trigger fainted abilities
            faint_events = self.opponent_pokemon.on_faint(self.player_pokemon)
            for event in faint_events:
                turn_info['battle_events'].append({
                    'type': 'ability',
                    'ability_name': event.get('ability_name'),
                    'pokemon_name': event.get('pokemon_name'),
                    'message': event.get('message'),
                    'target': 'opponent',
                    'timestamp': len(turn_info['battle_events'])
                })

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
                
            # Reset stalling counter if this is not a stalling move
            if not getattr(move, 'stalling_move', False):
                attacker.consecutive_stalling_moves = 0
            
            # Update last move name
            attacker.last_move_name = move_name
            
            # Check for priority counter failure
            if action and action.effective_priority == -999:
                # Priority counter failed - move doesn't execute
                print(f"DEBUG: {attacker.name}'s {move_name} failed due to priority counter conditions")
                return False
            
            # Check if the attacker can use a move this turn
            can_use_move, prevention_message = attacker.can_use_move()
            if not can_use_move:
                # Reset stalling counter if move failed due to status
                attacker.consecutive_stalling_moves = 0
                # Pokemon is prevented from using move
                turn_info['battle_events'].append({
                    'type': 'status',
                    'message': prevention_message,
                    'target': 'player' if is_player_attacking else 'opponent',
                    'pokemon_hp': attacker.current_hp,
                    'status_effects': attacker.get_status_display(),
                    'timestamp': len(turn_info['battle_events'])
                })
                print(f"DEBUG: {attacker.name} is prevented from using {move_name}: {prevention_message}")
                return False
                
            # Check if defender is protected (Protect, Detect, Spiky Shield, etc)
            PROTECTION_STATUSES = {
                'protect': 'all',
                'spikyshield': 'all',
                'banefulbunker': 'all',
                'silktrap': 'all',
                'burningbulwark': 'all',
                'kingsshield': 'damaging',
                'obstruct': 'damaging'
            }
            
            active_protections = [s for s in PROTECTION_STATUSES if s in defender.volatile_statuses]
            is_blocked = False
            protection_used = None
            
            if active_protections and attacker != defender:
                protection_used = active_protections[0]
                protection_type = PROTECTION_STATUSES[protection_used]
                
                if move.category in ['physical', 'special']:
                    is_blocked = True
                elif protection_type == 'all':
                    is_blocked = True
            
            if is_blocked:
                # Move is blocked
                turn_info['battle_events'].append({
                    'type': 'status',
                    'message': f"{defender.name} protected itself!",
                    'target': 'player' if not is_player_attacking else 'opponent',
                    'timestamp': len(turn_info['battle_events'])
                })
                
                # Handle contact effects (Spiky Shield, King's Shield)
                if move.flags.get('contact'):
                    if protection_used == 'spikyshield':
                        damage = defender.max_hp // 8
                        attacker.take_damage(damage)
                        turn_info['battle_events'].append({
                            'type': 'status',
                            'message': f"{attacker.name} was hurt by {defender.name}'s Spiky Shield!",
                            'target': 'player' if is_player_attacking else 'opponent',
                            'timestamp': len(turn_info['battle_events'])
                        })
                    elif protection_used == 'kingsshield':
                        msg = attacker.modify_stat_stage('attack', -1)
                        if msg:
                            turn_info['battle_events'].append({
                                'type': 'status',
                                'message': msg,
                                'target': 'player' if is_player_attacking else 'opponent',
                                'timestamp': len(turn_info['battle_events'])
                            })
                
                
                # Still consume PP and add the move usage message
                move.pp -= 1
                turn_info['battle_events'].append({
                    'type': 'status',
                    'message': f"{attacker.name} used {move_name}!",
                    'target': 'player' if is_player_attacking else 'opponent',
                    'timestamp': len(turn_info['battle_events'])
                })
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
                
            poke_damage, sub_damage, effectiveness_msg, status_message = move.use_move(attacker, defender)
            prev_hp = defender.current_hp
            
            # Apply defender's ability damage modifications (e.g. Filter, Solid Rock, Thick Fat)
            if hasattr(defender, 'ability'):
                poke_damage = defender.ability.modify_damage_taken(defender, attacker, move, poke_damage)
            
            # Damage the defender (move.py already handled substitute_hp subtraction)
            defender.take_damage(poke_damage)
            actual_damage = prev_hp - defender.current_hp
            
            substitute_hit = sub_damage > 0
            substitute_damage = sub_damage
            
            # Log move event
            move_event = {
                'type': 'move',
                'attacker_name': attacker.name,
                'defender_name': defender.name,
                'move': move_name,
                'damage': actual_damage, # 0 if hit substitute
                'substitute_damage': substitute_damage,
                'is_player': is_player_attacking,
                'attacker_hp': attacker.current_hp,
                'defender_hp': defender.current_hp,
                'attacker_max_hp': attacker.max_hp,
                'defender_max_hp': defender.max_hp,
                'attacker_status': attacker.get_status_display(),
                'defender_status': defender.get_status_display(),
                'attacker_substitute_hp': attacker.substitute_hp,
                'defender_substitute_hp': defender.substitute_hp,
                'timestamp': len(turn_info['battle_events']),
                'status_message': status_message
            }
            turn_info['battle_events'].append(move_event)
            
            # Handle substitute damage events
            if substitute_hit:
                turn_info['battle_events'].append({
                    'type': 'status',
                    'message': f"The substitute took damage for {defender.name}!",
                    'target': 'player' if not is_player_attacking else 'opponent',
                    'pokemon_hp': defender.current_hp,
                    'substitute_hp': defender.substitute_hp,
                    'timestamp': len(turn_info['battle_events'])
                })
                
                if defender.substitute_hp <= 0 and 'substitute' in defender.volatile_statuses:
                    defender.volatile_statuses.discard('substitute')
                    turn_info['battle_events'].append({
                        'type': 'status',
                        'message': f"{defender.name}'s substitute broke!",
                        'target': 'player' if not is_player_attacking else 'opponent',
                        'pokemon_hp': defender.current_hp,
                        'substitute_hp': 0,
                        'timestamp': len(turn_info['battle_events'])
                    })
            elif actual_damage > 0:
                # Add Endure message if they survived with 1 HP
                if defender.current_hp == 1 and poke_damage >= prev_hp and 'endure' in defender.volatile_statuses:
                    turn_info['battle_events'].append({
                        'type': 'status',
                        'message': f"{defender.name} endured the hit!",
                        'target': 'player' if not is_player_attacking else 'opponent',
                        'pokemon_hp': defender.current_hp,
                        'timestamp': len(turn_info['battle_events'])
                    })
            
            # Log damage totals for turn summary
            if is_player_attacking:
                turn_info['player_damage'] = actual_damage
            else:
                turn_info['opponent_damage'] = actual_damage
            
            # Add effectiveness as a separate event if there is a message
            if effectiveness_msg:
                effectiveness_event = {
                    'type': 'effectiveness',
                    'message': effectiveness_msg,
                    'is_player': is_player_attacking,
                    'timestamp': len(turn_info['battle_events'])
                }
                turn_info['battle_events'].append(effectiveness_event)
            
            
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
                        
                        # Trigger victory abilities for the attacker (e.g. Moxie)
                        attacker = action.pokemon
                        victory_events = attacker.on_victory(target_pokemon)
                        for event in victory_events:
                            turn_info['battle_events'].append({
                                'type': 'ability',
                                'ability_name': event.get('ability_name'),
                                'pokemon_name': event.get('pokemon_name'),
                                'message': event.get('message'),
                                'target': 'player' if is_player_action else 'opponent',
                                'timestamp': len(turn_info['battle_events'])
                            })
                        
                        # Trigger any-faint abilities for both (e.g. Soul-Heart)
                        for p in [self.player_pokemon, self.opponent_pokemon]:
                            if p and p.current_hp > 0:
                                any_faint_events = p.on_any_faint()
                                for event in any_faint_events:
                                    turn_info['battle_events'].append({
                                        'type': 'ability',
                                        'ability_name': event.get('ability_name'),
                                        'pokemon_name': event.get('pokemon_name'),
                                        'message': event.get('message'),
                                        'target': 'player' if p == self.player_pokemon else 'opponent',
                                        'timestamp': len(turn_info['battle_events'])
                                    })

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
                        'pokemon_hp': self.player_pokemon.current_hp,
                        'status_effects': self.player_pokemon.get_status_display(),
                        'timestamp': len(turn_info['battle_events'])
                    })
            
            opponent_end_messages = self.opponent_pokemon.process_turn_end_effects()
            for msg in opponent_end_messages:
                if msg:
                    turn_info['battle_events'].append({
                        'type': 'status',
                        'message': msg,
                        'target': 'opponent',
                        'pokemon_hp': self.opponent_pokemon.current_hp,
                        'status_effects': self.opponent_pokemon.get_status_display(),
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

        # Process turn-end abilities (e.g. Speed Boost)
        player_ability_events = self.player_pokemon.on_turn_end(self.opponent_pokemon)
        for event in player_ability_events:
            turn_info['battle_events'].append({
                'type': 'ability',
                'ability_name': event.get('ability_name'),
                'pokemon_name': event.get('pokemon_name'),
                'message': event.get('message'),
                'target': 'player',
                'timestamp': len(turn_info['battle_events'])
            })
            
        opponent_ability_events = self.opponent_pokemon.on_turn_end(self.player_pokemon)
        for event in opponent_ability_events:
            turn_info['battle_events'].append({
                'type': 'ability',
                'ability_name': event.get('ability_name'),
                'pokemon_name': event.get('pokemon_name'),
                'message': event.get('message'),
                'target': 'opponent',
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
