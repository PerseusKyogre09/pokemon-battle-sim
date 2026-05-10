from ..models.pokemon import Pokemon
from ..systems.priority_system import PriorityResolver, create_battle_action
from .ai import BattleAI
from typing import List, Dict, Any, Optional, Tuple
import random

class BattleSide:
    def __init__(self, owner_name):
        self.owner_name = owner_name
        self.spikes = 0
        self.stealth_rock = False
        self.sticky_web = False
        self.toxic_spikes = 0
        self.reflect = 0
        self.light_screen = 0
        self.aurora_veil = 0
        self.tailwind = 0
        self.safeguard = 0
        self.wish = None # {amount: int, turns: int}
        
    def process_turn_end(self):
        if self.reflect > 0: self.reflect -= 1
        if self.light_screen > 0: self.light_screen -= 1
        if self.aurora_veil > 0: self.aurora_veil -= 1
        if self.tailwind > 0: self.tailwind -= 1
        if self.safeguard > 0: self.safeguard -= 1
    
    def apply_entry_hazards(self, pokemon) -> List[str]:
        messages = []
        if pokemon.is_fainted(): return []
        
        if self.stealth_rock:
            from ..utils.data_loader import data_loader
            effectiveness = data_loader.get_type_effectiveness('rock', pokemon.types[0])
            if len(pokemon.types) > 1:
                effectiveness *= data_loader.get_type_effectiveness('rock', pokemon.types[1])
            
            damage = int(pokemon.max_hp * (0.125 * effectiveness))
            if damage > 0:
                pokemon.take_damage(damage)
                messages.append(f"Pointed stones dug into {pokemon.name}!")
        
        # Spikes
        if self.spikes > 0 and 'flying' not in pokemon.types and not pokemon.has_ability('levitate'):
            spike_damage = [0, 0.125, 0.1666, 0.25][self.spikes]
            damage = int(pokemon.max_hp * spike_damage)
            if damage > 0:
                pokemon.take_damage(damage)
                messages.append(f"{pokemon.name} was hurt by the spikes!")
                
        # Toxic Spikes
        if self.toxic_spikes > 0 and 'poison' not in pokemon.types and 'steel' not in pokemon.types and 'flying' not in pokemon.types and not pokemon.has_ability('levitate'):
            if 'poison' in pokemon.types:
                self.toxic_spikes = 0
                messages.append(f"The poison spikes disappeared from around your feet!")
            else:
                status = 'poison' if self.toxic_spikes == 1 else 'toxic'
                msg = pokemon.apply_status(status)
                if msg: messages.append(msg)
                
        # Sticky Web
        if self.sticky_web and 'flying' not in pokemon.types and not pokemon.has_ability('levitate'):
            msg = pokemon.modify_stat_stage('speed', -1)
            if msg: messages.append(f"{pokemon.name} was caught in a sticky web! {msg}")
            
        return messages

class Game:
    def __init__(self):
        self.player_team: List[Pokemon] = []
        self.opponent_team: List[Pokemon] = []
        self.player_side = BattleSide("Player")
        self.opponent_side = BattleSide("Opponent")
        self.player_pokemon = None # Active
        self.opponent_pokemon = None # Active
        self.battle_over = False
        self.weather = 'none'
        self.weather_duration = 0
        self.priority_resolver = PriorityResolver()
        self.ai = BattleAI()
    def start_battle(self, player_team_data: List[Dict], opponent_team_data: List[Dict]):
        self.player_team = []
        self.opponent_team = []
        
        for p_data in player_team_data:
            pokemon = self._create_pokemon_from_data(p_data, is_player=True)
            self.player_team.append(pokemon)
            
        for o_data in opponent_team_data:
            pokemon = self._create_pokemon_from_data(o_data, is_player=False)
            self.opponent_team.append(pokemon)
            
        # Set actives
        if self.player_team: self.player_pokemon = self.player_team[0]
        if self.opponent_team: self.opponent_pokemon = self.opponent_team[0]
        
        # Initial switch-in effects
        messages = []
        if self.player_pokemon:
            messages.extend(self._on_pokemon_switch_in(self.player_pokemon, self.opponent_pokemon, self.player_side))
        if self.opponent_pokemon:
            messages.extend(self._on_pokemon_switch_in(self.opponent_pokemon, self.player_pokemon, self.opponent_side))
            
        return messages

    def _create_pokemon_from_data(self, data, is_player):
        pokemon = Pokemon(
            data['name'],
            data.get('types', ['normal']),
            data.get('sprite_url'),
            data.get('stats', {}),
            data.get('moves', []),
            level=data.get('level', 100),
            ability=data.get('ability', 'noability'),
            item=data.get('item', ''),
            evs=data.get('evs', {}),
            ivs=data.get('ivs', {}),
            nature=data.get('nature', 'Hardy')
        )
        pokemon.is_player = is_player
        return pokemon

    def _on_pokemon_switch_in(self, pokemon, opponent, side) -> List[Dict]:
        events = []
        hazard_msgs = side.apply_entry_hazards(pokemon)
        for msg in hazard_msgs:
            events.append({
                'type': 'status',
                'message': msg,
                'target': 'player' if pokemon.is_player else 'opponent',
                'pokemon_hp': pokemon.current_hp
            })
            
        if pokemon.is_fainted():
            events.append({
                'type': 'faint',
                'pokemon_name': pokemon.name,
                'is_player': pokemon.is_player
            })
            return events
            
        ability_msgs = pokemon.on_switch_in(opponent)
        for msg in ability_msgs:
            if 'set_weather' in msg:
                self.weather = msg['set_weather']
                self.weather_duration = 5
            is_p = pokemon.is_player
            normalized_msg = {
                **msg,
                'target': 'player' if is_p else 'opponent',
                'is_player': is_p,
                'player_hp': self.player_pokemon.current_hp,
                'opponent_hp': self.opponent_pokemon.current_hp,
                'timestamp': len(events)
            }
            events.append(normalized_msg)
            
        return events

    def check_battle_over(self) -> Tuple[bool, Optional[str]]:
        """Returns (is_over, winner_name)."""
        player_lost = all(p.is_fainted() for p in self.player_team)
        opponent_lost = all(p.is_fainted() for p in self.opponent_team)
        
        if player_lost:
            return True, "Opponent"
        if opponent_lost:
            return True, "Player"
        return False, None

    def switch_pokemon(self, is_player: bool, index: int) -> List[Dict]:
        team = self.player_team if is_player else self.opponent_team
        side = self.player_side if is_player else self.opponent_side
        
        if index < 0 or index >= len(team):
            return []
            
        new_pokemon = team[index]
        if new_pokemon.is_fainted() or new_pokemon == (self.player_pokemon if is_player else self.opponent_pokemon):
            return []
            
        # Switch out current
        old_pokemon = self.player_pokemon if is_player else self.opponent_pokemon
        if old_pokemon:
            old_pokemon.volatile_statuses = set() # Reset volatiles on switch out
            
        if is_player:
            self.player_pokemon = new_pokemon
        else:
            self.opponent_pokemon = new_pokemon
            
        events = []
        # 1. Recall event
        if old_pokemon and not old_pokemon.is_fainted():
            events.append({
                'type': 'recall',
                'message': f"Come back, {old_pokemon.name}!",
                'is_player_switch': is_player,
                'is_opponent_switch': not is_player,
                'recalled_pokemon_name': old_pokemon.name
            })
        elif old_pokemon and old_pokemon.is_fainted():
            # If fainted, we still want a 'recall' event for the frontend animation to 'exit' the fainted mon
            # but without the "Come back" message if we want to avoid redundancy
            events.append({
                'type': 'recall',
                'message': None, # No message for fainted mon
                'is_player_switch': is_player,
                'is_opponent_switch': not is_player,
                'recalled_pokemon_name': old_pokemon.name
            })
        # 2. Send-out event - include current HP BEFORE opponent's move hits
        events.append({
            'type': 'status',
            'message': f"Go! {new_pokemon.name}!",
            'is_player_switch': is_player,
            'is_opponent_switch': not is_player,
            'new_pokemon_name': new_pokemon.name,
            'player_hp': self.player_pokemon.current_hp,
            'opponent_hp': self.opponent_pokemon.current_hp,
        })
        
        # Apply switch-in effects
        opponent = self.opponent_pokemon if is_player else self.player_pokemon
        switch_in_events = self._on_pokemon_switch_in(new_pokemon, opponent, side)
        events.extend(switch_in_events)
        
        return events

    def process_turn(self, move_name=None, switch_index=None):
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
            'initial_player_hp': self.player_pokemon.current_hp,
            'initial_opponent_hp': self.opponent_pokemon.current_hp,
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
                    'player_hp': self.player_pokemon.current_hp,
                    'opponent_hp': self.opponent_pokemon.current_hp,
                    'player_max_hp': self.player_pokemon.max_hp,
                    'opponent_max_hp': self.opponent_pokemon.max_hp,
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
                    'player_hp': self.player_pokemon.current_hp,
                    'opponent_hp': self.opponent_pokemon.current_hp,
                    'player_max_hp': self.player_pokemon.max_hp,
                    'opponent_max_hp': self.opponent_pokemon.max_hp,
                    'status_effects': self.opponent_pokemon.get_status_display(),
                    'timestamp': len(turn_info['battle_events'])
                })
        
        if self.player_pokemon.current_hp <= 0:
            if switch_index is not None:
                switch_events = self.switch_pokemon(True, switch_index)
                turn_info['battle_events'].extend(switch_events)
                return turn_info
            
            is_over, winner = self.check_battle_over()
            if is_over:
                self.battle_over = True
                turn_info['winner'] = winner
                if not any(e.get('type') == 'faint' and e.get('pokemon_name') == self.player_pokemon.name for e in turn_info['battle_events']):
                    turn_info['battle_events'].append({
                        'type': 'faint', 'pokemon_name': self.player_pokemon.name, 'is_player': True, 'timestamp': len(turn_info['battle_events'])
                    })
                return turn_info
            
            if not any(e.get('type') == 'faint' and e.get('pokemon_name') == self.player_pokemon.name for e in turn_info['battle_events']):
                faint_events = self.player_pokemon.on_faint(self.opponent_pokemon)
                for event in faint_events:
                    turn_info['battle_events'].append({
                        'type': 'ability', 'ability_name': event.get('ability_name'), 'pokemon_name': event.get('pokemon_name'),
                        'message': event.get('message'), 'target': 'player', 'timestamp': len(turn_info['battle_events'])
                    })
                turn_info['battle_events'].append({
                    'type': 'faint', 'pokemon_name': self.player_pokemon.name, 'is_player': True, 'timestamp': len(turn_info['battle_events'])
                })
            return turn_info
        
        if self.opponent_pokemon.current_hp <= 0:
            is_over, winner = self.check_battle_over()
            if is_over:
                self.battle_over = True
                turn_info['winner'] = winner
                turn_info['battle_events'].append({
                    'type': 'faint',
                    'pokemon_name': self.opponent_pokemon.name,
                    'is_player': False,
                    'timestamp': len(turn_info['battle_events'])
                })
                return turn_info
            else:
                # AI automatically switches
                new_idx = self.ai.select_switch(self.opponent_team, self.player_pokemon)
                if new_idx is not None:
                    switch_events = self.switch_pokemon(False, new_idx)
                    turn_info['battle_events'].extend(switch_events)
                else:
                    pass
        
        if switch_index is None:
            player_move = self.player_pokemon.moves.get(move_name)
            if not player_move or player_move.pp <= 0:
                return turn_info  # Invalid move or no PP left
                
        opponent_move_name, opponent_move = self.ai.select_move(self.opponent_pokemon, self.player_pokemon, self.weather)
        
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
        
        if opponent_move and opponent_move.pp <= 0:
            # If opponent has no PP, they struggle
            opponent_move = None
            turn_info['battle_events'].append({
                'type': 'status',
                'message': f"{self.opponent_pokemon.name} has no PP left for {opponent_move_name}!",
                'target': 'opponent',
                'timestamp': len(turn_info['battle_events'])
            })
        
        player_action = None
        if switch_index is not None:
            from ..models.move import Move
            switch_move = Move("Switch")
            switch_move.priority = 6
            player_action = create_battle_action(self.player_pokemon, switch_move, self.opponent_pokemon, self.priority_resolver)
            player_action.is_switch = True
            player_action.switch_index = switch_index
        elif move_name:
            player_move = self.player_pokemon.moves.get(move_name)
            if player_move and player_move.pp > 0:
                player_action = create_battle_action(self.player_pokemon, player_move, self.opponent_pokemon, self.priority_resolver)
                player_action.is_switch = False

        if not player_action:
            return turn_info # Should not happen with valid input
            
        opponent_move_name, opponent_move = self.ai.select_move(self.opponent_pokemon, self.player_pokemon, self.weather)
        opponent_action = create_battle_action(self.opponent_pokemon, opponent_move, self.player_pokemon, self.priority_resolver) if opponent_move else None
        if opponent_action: opponent_action.is_switch = False
        
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
            if not defender or defender.current_hp <= 0:
                return False
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
                    'player_hp': self.player_pokemon.current_hp,
                    'opponent_hp': self.opponent_pokemon.current_hp,
                    'player_max_hp': self.player_pokemon.max_hp,
                    'opponent_max_hp': self.opponent_pokemon.max_hp,
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
                    'player_hp': self.player_pokemon.current_hp,
                    'opponent_hp': self.opponent_pokemon.current_hp,
                    'player_max_hp': self.player_pokemon.max_hp,
                    'opponent_max_hp': self.opponent_pokemon.max_hp,
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
            
            # Item damage modifiers
            if attacker.item_obj:
                dmg = attacker.item_obj.modify_damage_dealt(attacker, defender, move, dmg)
            if defender.item_obj:
                dmg = defender.item_obj.modify_damage_taken(defender, attacker, move, dmg)
            
            if weather_to_set:
                self.weather = weather_to_set
                self.weather_duration = 5
                w_name = weather_to_set.replace('day', ' sunlight').replace('dance', '').replace('hail', 'snow')
                turn_info['battle_events'].append({
                    'type': 'status', 'message': f"The weather changed to {w_name}!", 
                    'set_weather': weather_to_set, 'timestamp': len(turn_info['battle_events'])
                })
            
            prev_hp = defender.current_hp
            defender.take_damage(dmg, from_move=True)
            actual_dmg = prev_hp - defender.current_hp
            
            turn_info['battle_events'].append({
                'type': 'move', 'attacker_name': attacker.name, 'defender_name': defender.name, 'move': move_name,
                'category': move.category,
                'move_type': move.type,
                'damage': actual_dmg, 'substitute_damage': sub_dmg, 'is_player': is_player_attacking,
                'attacker_hp': attacker.current_hp, 'defender_hp': defender.current_hp,
                'player_hp': self.player_pokemon.current_hp, 'opponent_hp': self.opponent_pokemon.current_hp,
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
            
            # Check for on_damage item triggers (e.g. Focus Sash, Sitrus Berry)
            if defender.item_obj:
                item_damage_events = defender.item_obj.on_damage(defender, actual_dmg)
                for event in item_damage_events:
                    turn_info['battle_events'].append({
                        'type': 'item',
                        'item_name': event.get('item_name'),
                        'pokemon_name': event.get('pokemon_name'),
                        'message': event.get('message'),
                        'target': 'opponent' if is_player_attacking else 'player',
                        'pokemon_hp': defender.current_hp,
                        'player_hp': self.player_pokemon.current_hp,
                        'opponent_hp': self.opponent_pokemon.current_hp,
                        'player_max_hp': self.player_pokemon.max_hp,
                        'opponent_max_hp': self.opponent_pokemon.max_hp,
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
            
            if eff_msg: turn_info['battle_events'].append({
                'type': 'effectiveness', 
                'message': eff_msg, 
                'is_player': is_player_attacking, 
                'player_hp': self.player_pokemon.current_hp,
                'opponent_hp': self.opponent_pokemon.current_hp,
                'player_max_hp': self.player_pokemon.max_hp,
                'opponent_max_hp': self.opponent_pokemon.max_hp,
                'timestamp': len(turn_info['battle_events'])
            })
            
            move.pp -= 1
            
            # Post-move item effects (e.g. Life Orb recoil)
            if attacker.item_obj:
                item_results = attacker.item_obj.on_after_move(attacker, {'damage_dealt': actual_dmg})
                for res in item_results:
                    turn_info['battle_events'].append({
                        'type': 'item',
                        'item_name': res.get('item_name'),
                        'pokemon_name': res.get('pokemon_name'),
                        'message': res.get('message'),
                        'target': 'player' if is_player_attacking else 'opponent',
                        'pokemon_hp': attacker.current_hp,
                        'player_hp': self.player_pokemon.current_hp,
                        'opponent_hp': self.opponent_pokemon.current_hp,
                        'player_max_hp': self.player_pokemon.max_hp,
                        'opponent_max_hp': self.opponent_pokemon.max_hp,
                        'timestamp': len(turn_info['battle_events'])
                    })

            return defender.current_hp <= 0
        
        try:
            for action in action_order:
                if self.battle_over: continue
                # CRITICAL: Do NOT skip Switch actions if the Pokemon is fainted.
                # A fainted Pokemon MUST be able to switch out to send in a replacement.
                if action.pokemon.is_fainted() and not getattr(action, 'is_switch', False):
                    continue
                is_p = action.pokemon == self.player_pokemon
                
                # Handle Switch Actions
                if getattr(action, 'is_switch', False):
                    switch_evs = self.switch_pokemon(is_p, action.switch_index)
                    turn_info['battle_events'].extend(switch_evs)
                    # CRITICAL: Update action targets for remaining actions so they hit the new pokemon
                    new_active = self.player_pokemon if is_p else self.opponent_pokemon
                    for remaining_action in action_order:
                        if remaining_action != action and remaining_action.target == action.pokemon:
                            remaining_action.target = new_active
                    continue

                # Handle Move Actions
                mv = action.move
                mv_name = move_name if is_p else opponent_move_name
                
                if mv and execute_move(action.pokemon, action.target, mv, mv_name, is_p, action):
                    # Target fainted
                    target = action.target
                    is_target_player = (target == self.player_pokemon)
                    attacker = action.pokemon
                    
                    # Victory effects
                    for event in attacker.on_victory(target):
                        turn_info['battle_events'].append({
                            'type': 'ability', 'ability_name': event.get('ability_name'), 'pokemon_name': event.get('pokemon_name'),
                            'message': event.get('message'), 'target': 'player' if is_p else 'opponent', 'timestamp': len(turn_info['battle_events'])
                        })
                    
                    # Global faint triggers
                    for p in [self.player_pokemon, self.opponent_pokemon]:
                        if p and p.current_hp > 0:
                            for event in p.on_any_faint():
                                turn_info['battle_events'].append({
                                    'type': 'ability', 'ability_name': event.get('ability_name'), 'pokemon_name': event.get('pokemon_name'),
                                    'message': event.get('message'), 'target': 'player' if p == self.player_pokemon else 'opponent', 'timestamp': len(turn_info['battle_events'])
                                })
                    
                    # Check if team is fully defeated
                    is_over, winner = self.check_battle_over()
                    if is_over:
                        self.battle_over = True
                        turn_info['winner'] = winner
            
                    turn_info['battle_events'].append({
                        'type': 'faint', 'pokemon_name': target.name, 'is_player': is_target_player, 
                        'timestamp': len(turn_info['battle_events']),
                        'player_hp': self.player_pokemon.current_hp,
                        'opponent_hp': self.opponent_pokemon.current_hp
                    })

                    # If it was the opponent who fainted and battle is NOT over, switch them in
                    if not is_target_player and not self.battle_over:
                        new_idx = self.ai.select_switch(self.opponent_team, self.player_pokemon)
                        if new_idx is not None:
                            switch_events = self.switch_pokemon(False, new_idx)
                            turn_info['battle_events'].extend(switch_events)
                    
                    # End turn processing after a faint
                    break
        except Exception as e:
            print(f"Error during turn: {e}")
        
        # Process turn-end effects for both Pokemon
        if not self.battle_over:
            if self.player_pokemon.current_hp > 0:
                player_end_messages = self.player_pokemon.process_turn_end_effects()
                for msg in player_end_messages:
                    if msg:
                        turn_info['battle_events'].append({
                            'type': 'status',
                            'message': msg,
                            'target': 'player',
                            'pokemon_hp': self.player_pokemon.current_hp,
                            'player_hp': self.player_pokemon.current_hp,
                            'opponent_hp': self.opponent_pokemon.current_hp,
                            'player_max_hp': self.player_pokemon.max_hp,
                            'opponent_max_hp': self.opponent_pokemon.max_hp,
                            'status_effects': self.player_pokemon.get_status_display(),
                            'timestamp': len(turn_info['battle_events'])
                        })
            
            if self.opponent_pokemon.current_hp > 0:
                opponent_end_messages = self.opponent_pokemon.process_turn_end_effects()
                for msg in opponent_end_messages:
                    if msg:
                        turn_info['battle_events'].append({
                            'type': 'status',
                            'message': msg,
                            'target': 'opponent',
                            'pokemon_hp': self.opponent_pokemon.current_hp,
                            'timestamp': len(turn_info['battle_events'])
                        })
            
            # Item turn-end effects (e.g. Leftovers)
            if self.player_pokemon.item_obj and self.player_pokemon.current_hp > 0:
                player_item_msgs = self.player_pokemon.item_obj.on_residual(self.player_pokemon)
                for msg in player_item_msgs:
                    turn_info['battle_events'].append({
                        'type': 'item',
                        'item_name': msg.get('item_name'),
                        'message': msg.get('message'),
                        'target': 'player',
                        'pokemon_hp': self.player_pokemon.current_hp,
                        'player_hp': self.player_pokemon.current_hp,
                        'opponent_hp': self.opponent_pokemon.current_hp,
                        'player_max_hp': self.player_pokemon.max_hp,
                        'opponent_max_hp': self.opponent_pokemon.max_hp,
                        'timestamp': len(turn_info['battle_events'])
                    })
            
            if self.opponent_pokemon.item_obj and self.opponent_pokemon.current_hp > 0:
                opponent_item_msgs = self.opponent_pokemon.item_obj.on_residual(self.opponent_pokemon)
                for msg in opponent_item_msgs:
                    turn_info['battle_events'].append({
                        'type': 'item',
                        'item_name': msg.get('item_name'),
                        'message': msg.get('message'),
                        'target': 'opponent',
                        'pokemon_hp': self.opponent_pokemon.current_hp,
                        'timestamp': len(turn_info['battle_events'])
                    })
            
            # Check if either Pokemon fainted from turn-end effects
            if self.player_pokemon.current_hp <= 0 and not self.battle_over and not any(e.get('type') == 'faint' and e.get('is_player') for e in turn_info['battle_events']):
                is_over, winner = self.check_battle_over()
                if is_over:
                    self.battle_over = True
                    turn_info['winner'] = winner
                
                turn_info['battle_events'].append({
                    'type': 'faint',
                    'pokemon_name': self.player_pokemon.name,
                    'is_player': True,
                    'timestamp': len(turn_info['battle_events'])
                })
            
            if self.opponent_pokemon.current_hp <= 0 and not self.battle_over:
                is_over, winner = self.check_battle_over()
                if is_over:
                    self.battle_over = True
                    turn_info['winner'] = winner
                else:
                    # AI automatically switches
                    new_idx = self.ai.select_switch(self.opponent_team, self.player_pokemon)
                    if new_idx is not None:
                        switch_events = self.switch_pokemon(False, new_idx)
                        turn_info['battle_events'].extend(switch_events)

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
                                    'pokemon_hp': p.current_hp, 
                                    'player_hp': self.player_pokemon.current_hp,
                                    'opponent_hp': self.opponent_pokemon.current_hp,
                                    'player_max_hp': self.player_pokemon.max_hp,
                                    'opponent_max_hp': self.opponent_pokemon.max_hp,
                                    'timestamp': len(turn_info['battle_events'])
                                })
                                if p.current_hp <= 0:
                                    is_over, winner = self.check_battle_over()
                                    if is_over:
                                        self.battle_over = True
                                        turn_info['winner'] = winner
                                    elif p == self.opponent_pokemon:
                                        # AI automatically switches
                                        new_idx = self.ai.select_switch(self.opponent_team, self.player_pokemon)
                                        if new_idx is not None:
                                            switch_events = self.switch_pokemon(False, new_idx)
                                            turn_info['battle_events'].extend(switch_events)

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
                'player_hp': self.player_pokemon.current_hp,
                'opponent_hp': self.opponent_pokemon.current_hp,
                'player_max_hp': self.player_pokemon.max_hp,
                'opponent_max_hp': self.opponent_pokemon.max_hp,
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
                'player_hp': self.player_pokemon.current_hp,
                'opponent_hp': self.opponent_pokemon.current_hp,
                'player_max_hp': self.player_pokemon.max_hp,
                'opponent_max_hp': self.opponent_pokemon.max_hp,
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
                'player_hp': self.player_pokemon.current_hp,
                'opponent_hp': self.opponent_pokemon.current_hp,
                'player_max_hp': self.player_pokemon.max_hp,
                'opponent_max_hp': self.opponent_pokemon.max_hp,
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
                'player_hp': self.player_pokemon.current_hp,
                'opponent_hp': self.opponent_pokemon.current_hp,
                'player_max_hp': self.player_pokemon.max_hp,
                'opponent_max_hp': self.opponent_pokemon.max_hp,
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
        player_lost = all(p.is_fainted() for p in self.player_team)
        opponent_lost = all(p.is_fainted() for p in self.opponent_team)
        
        if player_lost:
            return "Opponent wins the battle!"
        elif opponent_lost:
            return "Player wins the battle!"
        return "Battle ongoing"
