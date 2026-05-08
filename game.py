from pokemon import Pokemon
from priority_system import PriorityResolver, create_battle_action
from ai import BattleAI
import random

class Game:
    def __init__(self):
        self.player_pokemon = None
        self.opponent_pokemon = None
        self.battle_over = False
        self.weather = 'none'
        self.weather_duration = 0
        self.priority_resolver = PriorityResolver()
        self.ai = BattleAI()
    def start_battle(self, player_data, opponent_data, player_moves, opponent_moves, player_ability="noability", opponent_ability="noability"):
        # ... (keep existing setup code)
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
        p_messages = self.player_pokemon.on_switch_in(self.opponent_pokemon)
        o_messages = self.opponent_pokemon.on_switch_in(self.player_pokemon)
        
        all_msgs = p_messages + o_messages
        for msg in all_msgs:
            if 'set_weather' in msg:
                self.weather = msg['set_weather']
                self.weather_duration = 5
            messages.append(msg)
            
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
                
        # Get opponent's move using AI
        opponent_move_name, opponent_move = self.ai.select_move(self.opponent_pokemon, self.player_pokemon, self.weather)
        
        # Fallback if AI somehow fails or has no PP
        if not opponent_move:
            # Try to find any move with PP
            for m_name, m in self.opponent_pokemon.moves.items():
                if m.pp > 0:
                    opponent_move_name, opponent_move = m_name, m
                    break
            
            # If still no move, opponent struggles (handled below)
            if not opponent_move:
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
            action_order, player_first = [player_action], True
        
        turn_info.update({'player_first': player_first, 'action_order': action_order})
        
        if len(action_order) == 2:
            expl = self._get_priority_explanation_message(action_order[0], action_order[1])
            if expl: turn_info['battle_events'].append({'type': 'priority_explanation', 'message': expl, 'timestamp': len(turn_info['battle_events'])})
        
        for action in action_order:
            if action.effective_priority == -999:
                fail_msg = self.priority_resolver.get_priority_counter_failure_message(action.move)
                turn_info['battle_events'].append({
                    'type': 'priority_counter_failure', 'message': f"{action.pokemon.name} used {action.move.name}! {fail_msg}",
                    'target': 'player' if action.pokemon == self.player_pokemon else 'opponent',
                    'timestamp': len(turn_info['battle_events'])
                })
        
        def execute_move(attacker, defender, move, move_name, is_player_attacking, action=None):
            if not move: return False
            if not getattr(move, 'stalling_move', False): attacker.consecutive_stalling_moves = 0
            attacker.last_move_name = move_name
            
            if action and action.effective_priority == -999: return False
            
            can_use, msg = attacker.can_use_move()
            if not can_use:
                attacker.consecutive_stalling_moves = 0
                is_ability_msg = 'ability:' in msg.lower() or 'loafing' in msg.lower() or (attacker.ability and attacker.ability.id == 'truant')
                event_type = 'ability' if is_ability_msg else 'status'
                turn_info['battle_events'].append({
                    'type': event_type, 
                    'ability_name': attacker.ability.name if event_type == 'ability' else None,
                    'pokemon_name': attacker.name,
                    'message': msg, 
                    'target': 'player' if is_player_attacking else 'opponent',
                    'is_player': is_player_attacking,
                    'pokemon_hp': attacker.current_hp, 
                    'status_effects': attacker.get_status_display(),
                    'substitute_hp': attacker.substitute_hp,
                    'timestamp': len(turn_info['battle_events'])
                })
                return False
                
            PROT = {'protect': 'all', 'spikyshield': 'all', 'banefulbunker': 'all', 'silktrap': 'all', 'burningbulwark': 'all', 'kingsshield': 'damaging', 'obstruct': 'damaging'}
            active_prot = [s for s in PROT if s in defender.volatile_statuses]
            is_blocked = False
            if active_prot and attacker != defender:
                p_used = active_prot[0]
                if move.category in ['physical', 'special'] or PROT[p_used] == 'all': is_blocked = True
            
            if is_blocked:
                # 1. Announce the move usage FIRST
                turn_info['battle_events'].append({
                    'type': 'move', 
                    'attacker_name': attacker.name, 
                    'move': move_name, 
                    'is_player': is_player_attacking,
                    'attacker_hp': attacker.current_hp,
                    'defender_hp': defender.current_hp,
                    'attacker_status': attacker.get_status_display(),
                    'defender_status': defender.get_status_display(),
                    'attacker_substitute_hp': attacker.substitute_hp,
                    'defender_substitute_hp': defender.substitute_hp,
                    'timestamp': len(turn_info['battle_events'])
                })
                # 2. Announce the protection SECOND
                turn_info['battle_events'].append({
                    'type': 'status', 
                    'message': f"{defender.name} protected itself!", 
                    'target': 'player' if not is_player_attacking else 'opponent', 
                    'pokemon_hp': defender.current_hp,
                    'status_effects': defender.get_status_display(),
                    'timestamp': len(turn_info['battle_events'])
                })
                
                if move.flags.get('contact'):
                    if active_prot[0] == 'spikyshield':
                        attacker.take_damage(defender.max_hp // 8)
                        turn_info['battle_events'].append({'type': 'status', 'message': f"{attacker.name} was hurt by {defender.name}'s Spiky Shield!", 'target': 'player' if is_player_attacking else 'opponent', 'timestamp': len(turn_info['battle_events'])})
                    elif active_prot[0] == 'kingsshield':
                        m = attacker.modify_stat_stage('attack', -1)
                        if m: turn_info['battle_events'].append({'type': 'status', 'message': m, 'target': 'player' if is_player_attacking else 'opponent', 'timestamp': len(turn_info['battle_events'])})
                
                move.pp -= 1
                return False
            
            if action and action.is_priority_counter and action.effective_priority != -999:
                s_msg = self.priority_resolver.get_priority_counter_success_message(move, attacker.name, defender.name, action.counter_target_move.name if action.counter_target_move else "unknown")
                if s_msg: turn_info['battle_events'].append({'type': 'priority_counter_success', 'message': s_msg, 'target': 'player' if is_player_attacking else 'opponent', 'timestamp': len(turn_info['battle_events'])})
                
            dmg, sub_dmg, eff_msg, stat_msg, weather_to_set = move.use_move(attacker, defender, self.weather)
            if hasattr(defender, 'ability'): dmg = defender.ability.modify_damage_taken(defender, attacker, move, dmg)
            
            if weather_to_set:
                self.weather = weather_to_set
                self.weather_duration = 5
                w_name = weather_to_set.replace('day', ' sunlight').replace('dance', '').replace('hail', 'snow')
                turn_info['battle_events'].append({
                    'type': 'status', 'message': f"The weather changed to {w_name}!", 
                    'set_weather': weather_to_set, 'timestamp': len(turn_info['battle_events'])
                })
            
            prev_hp = defender.current_hp
            defender.take_damage(dmg)
            actual_dmg = prev_hp - defender.current_hp
            
            turn_info['battle_events'].append({
                'type': 'move', 'attacker_name': attacker.name, 'defender_name': defender.name, 'move': move_name,
                'damage': actual_dmg, 'substitute_damage': sub_dmg, 'is_player': is_player_attacking,
                'attacker_hp': attacker.current_hp, 'defender_hp': defender.current_hp,
                'attacker_max_hp': attacker.max_hp, 'defender_max_hp': defender.max_hp,
                'attacker_status': attacker.get_status_display(), 'defender_status': defender.get_status_display(),
                'attacker_substitute_hp': attacker.substitute_hp, 'defender_substitute_hp': defender.substitute_hp,
                'timestamp': len(turn_info['battle_events']), 'status_message': stat_msg
            })
            
            # Check for on_damage ability triggers (e.g. Defeatist)
            damage_events = defender.on_damage(actual_dmg)
            for event in damage_events:
                turn_info['battle_events'].append({
                    'type': 'ability',
                    'ability_name': event.get('ability_name'),
                    'pokemon_name': event.get('pokemon_name'),
                    'message': event.get('message'),
                    'target': 'opponent' if is_player_attacking else 'player',
                    'timestamp': len(turn_info['battle_events'])
                })
            
            if sub_dmg > 0:
                turn_info['battle_events'].append({'type': 'status', 'message': f"The substitute took damage for {defender.name}!", 'target': 'player' if not is_player_attacking else 'opponent', 'pokemon_hp': defender.current_hp, 'substitute_hp': defender.substitute_hp, 'timestamp': len(turn_info['battle_events'])})
                if defender.substitute_hp <= 0 and 'substitute' in defender.volatile_statuses:
                    defender.volatile_statuses.discard('substitute')
                    turn_info['battle_events'].append({'type': 'status', 'message': f"{defender.name}'s substitute broke!", 'target': 'player' if not is_player_attacking else 'opponent', 'pokemon_hp': defender.current_hp, 'substitute_hp': 0, 'timestamp': len(turn_info['battle_events'])})
            elif actual_dmg > 0 and defender.current_hp == 1 and dmg >= prev_hp and 'endure' in defender.volatile_statuses:
                turn_info['battle_events'].append({'type': 'status', 'message': f"{defender.name} endured the hit!", 'target': 'player' if not is_player_attacking else 'opponent', 'pokemon_hp': defender.current_hp, 'timestamp': len(turn_info['battle_events'])})
            
            if is_player_attacking: turn_info['player_damage'] = actual_dmg
            else: turn_info['opponent_damage'] = actual_dmg
            
            if eff_msg: turn_info['battle_events'].append({'type': 'effectiveness', 'message': eff_msg, 'is_player': is_player_attacking, 'timestamp': len(turn_info['battle_events'])})
            
            move.pp -= 1
            return defender.current_hp <= 0
        
        try:
            fainted_mon = None
            for action in action_order:
                if self.battle_over or action.pokemon.is_fainted(): continue
                is_p = action.pokemon == self.player_pokemon
                mv = action.move
                mv_name = move_name if is_p else opponent_move_name
                
                if mv and execute_move(action.pokemon, action.target, mv, mv_name, is_p, action):
                    fainted_mon = (action.target, action.target == self.player_pokemon)
                    attacker = action.pokemon
                    for event in attacker.on_victory(action.target):
                        turn_info['battle_events'].append({
                            'type': 'ability', 'ability_name': event.get('ability_name'), 'pokemon_name': event.get('pokemon_name'),
                            'message': event.get('message'), 'target': 'player' if is_p else 'opponent', 'timestamp': len(turn_info['battle_events'])
                        })
                    
                    for p in [self.player_pokemon, self.opponent_pokemon]:
                        if p and p.current_hp > 0:
                            for event in p.on_any_faint():
                                turn_info['battle_events'].append({
                                    'type': 'ability', 'ability_name': event.get('ability_name'), 'pokemon_name': event.get('pokemon_name'),
                                    'message': event.get('message'), 'target': 'player' if p == self.player_pokemon else 'opponent', 'timestamp': len(turn_info['battle_events'])
                                })
                    self.battle_over = True
            
            if fainted_mon:
                mon, is_p = fainted_mon
                turn_info['battle_events'].append({'type': 'faint', 'pokemon_name': mon.name, 'is_player': is_p, 'timestamp': len(turn_info['battle_events'])})
        except Exception as e:
            print(f"Error during turn: {e}")
        
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

        # Process weather duration and effects
        if self.weather != 'none':
            self.weather_duration -= 1
            if self.weather_duration <= 0:
                turn_info['battle_events'].append({
                    'type': 'status', 'message': "The weather returned to normal!", 
                    'set_weather': 'none', 'timestamp': len(turn_info['battle_events'])
                })
                self.weather = 'none'
            else:
                if self.weather in ['sandstorm']: # Hail (Snow) no longer damages
                    for p in [self.player_pokemon, self.opponent_pokemon]:
                        if p and p.current_hp > 0:
                            is_immune = False
                            p_types = [t.lower() for t in p.types]
                            if self.weather == 'sandstorm':
                                is_immune = any(t in ['rock', 'ground', 'steel'] for t in p_types)
                            
                            if not is_immune:
                                dmg = p.max_hp // 16
                                p.take_damage(dmg)
                                turn_info['battle_events'].append({
                                    'type': 'status', 'message': f"{p.name} is buffeted by the {self.weather}!", 
                                    'target': 'player' if p == self.player_pokemon else 'opponent',
                                    'pokemon_hp': p.current_hp, 'timestamp': len(turn_info['battle_events'])
                                })
                                if p.current_hp <= 0:
                                    self.battle_over = True
                                    turn_info['battle_events'].append({
                                        'type': 'faint', 'pokemon_name': p.name, 
                                        'is_player': p == self.player_pokemon, 'timestamp': len(turn_info['battle_events'])
                                    })

        turn_info['weather'] = self.weather
        
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
