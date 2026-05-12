from ..models.pokemon import Pokemon
from ..systems.priority_system import PriorityResolver, create_battle_action
from .builtin_hooks import register_builtin_hooks
from .hooks import BattleContext, HookRegistry
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
        self.future_move = None # {move: Move, attacker: Pokemon, turns: int}
        
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
        self.pending_player_self_switch = False
        self.player_has_mega = False
        self.opponent_has_mega = False
        self.hooks = HookRegistry()
        register_builtin_hooks(self.hooks)
        self.priority_resolver = PriorityResolver()
        self.ai = BattleAI()
        
    def set_weather(self, new_weather: str, duration: int = 5):
        STRONG_WEATHERS = ['primordialsea', 'desolateland', 'deltastream']
        
        # If current weather is strong, only another strong weather (from a slower pokemon) can overwrite it
        if self.weather in STRONG_WEATHERS and new_weather not in STRONG_WEATHERS:
            return False
            
        self.weather = new_weather
        self.weather_duration = duration
        return True

    def check_primal_weather_end(self):
        """Primal weathers end if the source pokemon is no longer active."""
        STRONG_TO_ABILITY = {
            'primordialsea': 'primordialsea',
            'desolateland': 'desolateland',
            'deltastream': 'deltastream'
        }
        
        if self.weather not in STRONG_TO_ABILITY:
            return
            
        target_ability = STRONG_TO_ABILITY[self.weather]
        source_present = False
        for p in [self.player_pokemon, self.opponent_pokemon]:
            if p and p.current_hp > 0 and p.ability and p.ability.id == target_ability:
                source_present = True
                break
        
        if not source_present:
            self.weather = 'none'
            self.weather_duration = 0
            return True
        return False

    def can_mega_evolve(self, is_player: bool) -> bool:
        has_mega = self.player_has_mega if is_player else self.opponent_has_mega
        if has_mega:
            return False
        
        pokemon = self.player_pokemon if is_player else self.opponent_pokemon
        if not pokemon or pokemon.is_fainted() or 'mega' in pokemon.name.lower():
            return False
            
        from ..utils.pokemon_utils import MEGA_STONES, PRIMAL_ORBS
        
        # Rayquaza special case (Dragon Ascent)
        pokemon_name = pokemon.name.lower().strip()
        if "rayquaza" in pokemon_name:
            # Check for Dragon Ascent move
            for m in pokemon.moves.values():
                m_id = m.id.lower().replace(" ", "").replace("-", "")
                m_name = m.name.lower().replace(" ", "").replace("-", "")
                if m_id == "dragonascent" or m_name == "dragonascent":
                    return True
        
        # Check if the pokemon's item is a valid mega stone
        from ..utils.pokemon_utils import MEGA_STONES
        item_id = pokemon.item.lower().replace(' ', '').replace('-', '')
        
        if item_id in MEGA_STONES:
            target_form = MEGA_STONES[item_id]
            base_species = target_form.split('-mega')[0]
            if pokemon.name.lower() == base_species:
                return True
        return False

    def can_primal_revert(self, is_player: bool) -> bool:
        pokemon = self.player_pokemon if is_player else self.opponent_pokemon
        if not pokemon or pokemon.is_fainted() or 'primal' in pokemon.name.lower():
            return False
        
        from ..utils.pokemon_utils import PRIMAL_ORBS
        item_id = pokemon.item.lower().replace(' ', '').replace('-', '')
        
        if item_id in PRIMAL_ORBS:
            target_form = PRIMAL_ORBS[item_id]
            base_species = target_form.split('-primal')[0]
            if pokemon.name.lower() == base_species:
                return True
        return False

    def perform_mega_evolution(self, is_player: bool, turn_info: dict):
        pokemon = self.player_pokemon if is_player else self.opponent_pokemon
        if not pokemon:
            return
            
        from ..utils.pokemon_utils import MEGA_STONES, PRIMAL_ORBS
        from ..utils.pokemon_api import get_forme_data
        
        target_form = None
        # Rayquaza special case
        if "rayquaza" in pokemon.name.lower():
            target_form = "rayquaza-mega"
            mega_message = f"{self._get_pokemon_name(pokemon)}'s fervent wish has been granted!"
        else:
            item_id = pokemon.item.lower().replace(' ', '').replace('-', '')
            if item_id in MEGA_STONES:
                target_form = MEGA_STONES[item_id]
                mega_message = f"{self._get_pokemon_name(pokemon)}'s {pokemon.item} is reacting to the Key Stone!"
        
        if target_form:
            side = 'back' if is_player else 'front'
            forme_data = get_forme_data(target_form, side=side)
            
            if forme_data:
                pokemon.forme_change(
                    new_name=forme_data['name'],
                    new_types=forme_data['types'],
                    new_sprite=forme_data['sprite_url'],
                    new_stats=forme_data['stats'],
                    new_cry=forme_data['cry_url'],
                    new_ability=forme_data.get('ability', '')
                )
                
                if is_player:
                    self.player_has_mega = True
                else:
                    self.opponent_has_mega = True
                    
                turn_info['battle_events'].append({
                    "type": "mega_evolution",
                    "pokemon_name": self._get_pokemon_name(pokemon),
                    "message": mega_message,
                    "target": "player" if is_player else "opponent",
                    "is_player": is_player,
                    "new_sprite": pokemon.sprite_url,
                    "new_name": pokemon.name,
                    "timestamp": len(turn_info['battle_events'])
                })
                
                # Trigger ability on Mega Evolution (e.g., Drought, Intimidate)
                opponent = self.opponent_pokemon if is_player else self.player_pokemon
                ability_events = pokemon.on_switch_in(opponent)
                if ability_events:
                    turn_info['battle_events'].extend(ability_events); [self.set_weather(e['set_weather'], 999) for e in ability_events if 'set_weather' in e]; [self.set_terrain(e['set_terrain'], 5) for e in ability_events if 'set_terrain' in e]

    def perform_primal_reversion(self, is_player: bool, turn_info: dict):
        pokemon = self.player_pokemon if is_player else self.opponent_pokemon
        if not pokemon:
            return
            
        from ..utils.pokemon_utils import PRIMAL_ORBS
        from ..utils.pokemon_api import get_forme_data
        
        item_id = pokemon.item.lower().replace(' ', '').replace('-', '')
        if item_id in PRIMAL_ORBS:
            target_form = PRIMAL_ORBS[item_id]
            side = 'back' if is_player else 'front'
            forme_data = get_forme_data(target_form, side=side)
            
            if forme_data:
                pokemon.forme_change(
                    new_name=forme_data['name'],
                    new_types=forme_data['types'],
                    new_sprite=forme_data['sprite_url'],
                    new_stats=forme_data['stats'],
                    new_cry=forme_data['cry_url'],
                    new_ability=forme_data.get('ability', '')
                )
                
                turn_info['battle_events'].append({
                    "type": "mega_evolution", # Use same type for animation
                    "pokemon_name": self._get_pokemon_name(pokemon),
                    "message": f"{self._get_pokemon_name(pokemon)}'s {pokemon.item} is reacting to the transformation!",
                    "target": "player" if is_player else "opponent",
                    "is_player": is_player,
                    "new_sprite": pokemon.sprite_url,
                    "new_name": pokemon.name,
                    "is_primal": True,
                    "timestamp": len(turn_info['battle_events'])
                })
                
                # Trigger ability on Primal Reversion
                opponent = self.opponent_pokemon if is_player else self.player_pokemon
                ability_events = pokemon.on_switch_in(opponent)
                if ability_events:
                    turn_info['battle_events'].extend(ability_events); [self.set_weather(e['set_weather'], 999) for e in ability_events if 'set_weather' in e]; [self.set_terrain(e['set_terrain'], 5) for e in ability_events if 'set_terrain' in e]

    def _get_pokemon_name(self, pokemon):
        if not pokemon: return "Unknown"
        return pokemon.get_display_name()

    def _check_move_accuracy(self, context: BattleContext) -> bool:
        if context.accuracy is True: return True
        base_accuracy = context.accuracy
        attacker, defender = context.attacker, context.defender
        acc_stage, eva_stage = attacker.stat_stages.get('accuracy', 0), defender.stat_stages.get('evasion', 0)
        def get_multiplier(stage):
            if stage > 0: return (3 + stage) / 3
            elif stage < 0: return 3 / (3 - stage)
            return 1.0
        combined_stage = max(-6, min(6, acc_stage - eva_stage))
        stage_multiplier = get_multiplier(combined_stage)
        effective_accuracy = base_accuracy * stage_multiplier
        if hasattr(attacker, 'ability'):
            if attacker.ability.id == 'victorystar': effective_accuracy *= 1.1
            elif attacker.ability.id == 'compoundeyes': effective_accuracy *= 1.3
        return random.randint(1, 100) <= effective_accuracy

    def execute_move(self, attacker, defender, move, move_name, is_player_attacking, turn_info, action=None):
        if not move: return False
        if not defender or defender.current_hp <= 0: return False
        if not getattr(move, 'stalling_move', False): attacker.consecutive_stalling_moves = 0
        attacker.last_move_name = move_name
        if action and action.effective_priority == -999: return False
        
        context = BattleContext(game=self, phase='beforeMove', attacker=attacker, defender=defender, move=move, is_player_attacking=is_player_attacking)
        self.hooks.run('beforeMove', context)
        turn_info['battle_events'].extend(context.events)
        context.events = []
        if context.flags.get('cancel_move'): return False
        
        can_use, msg = attacker.can_use_move()
        if not can_use:
            attacker.consecutive_stalling_moves = 0
            is_ability_msg = 'ability:' in msg.lower() or 'loafing' in msg.lower() or (attacker.ability and attacker.ability.id == 'truant')
            event_type = 'ability' if is_ability_msg else 'status'
            turn_info['battle_events'].append({'type': event_type, 'ability_name': attacker.ability.name if event_type == 'ability' else None, 'pokemon_name': self._get_pokemon_name(attacker), 'message': msg, 'target': 'player' if is_player_attacking else 'opponent', 'is_player': is_player_attacking, 'pokemon_hp': attacker.current_hp, 'player_hp': self.player_pokemon.current_hp, 'opponent_hp': self.opponent_pokemon.current_hp, 'player_max_hp': self.player_pokemon.max_hp, 'opponent_max_hp': self.opponent_pokemon.max_hp, 'status_effects': attacker.get_status_display(), 'substitute_hp': attacker.substitute_hp, 'timestamp': len(turn_info['battle_events'])})
            return False
            
        self.hooks.run('modifyMove', context)
        move = context.move
        
        self.hooks.run('tryHit', context)
        turn_info['battle_events'].extend(context.events)
        context.events = []
        if context.flags.get('move_failed') or context.flags.get('move_blocked'):
            move.pp -= 1
            return False
            
        PROT = {'protect': 'all', 'spikyshield': 'all', 'banefulbunker': 'all', 'silktrap': 'all', 'burningbulwark': 'all', 'kingsshield': 'damaging', 'obstruct': 'damaging'}
        active_prot = [s for s in PROT if s in defender.volatile_statuses]
        is_blocked = False
        if active_prot and attacker != defender:
            p_used = active_prot[0]
            if move.category in ['physical', 'special'] or PROT[p_used] == 'all': is_blocked = True
        if is_blocked:
            turn_info['battle_events'].append({'type': 'move', 'attacker_name': self._get_pokemon_name(attacker), 'move': move_name, 'is_player': is_player_attacking, 'attacker_hp': attacker.current_hp, 'defender_hp': defender.current_hp, 'timestamp': len(turn_info['battle_events'])})
            turn_info['battle_events'].append({'type': 'status', 'message': f"{self._get_pokemon_name(defender)} protected itself!", 'target': 'player' if not is_player_attacking else 'opponent', 'pokemon_hp': defender.current_hp, 'timestamp': len(turn_info['battle_events'])})
            if move.flags.get('contact'):
                if active_prot[0] == 'spikyshield':
                    attacker.take_damage(defender.max_hp // 8)
                    turn_info['battle_events'].append({'type': 'status', 'message': f"{self._get_pokemon_name(attacker)} was hurt by {self._get_pokemon_name(defender)}'s Spiky Shield!", 'target': 'player' if is_player_attacking else 'opponent', 'timestamp': len(turn_info['battle_events'])})
                elif active_prot[0] == 'kingsshield':
                    m = attacker.modify_stat_stage('attack', -1)
                    if m: turn_info['battle_events'].append({'type': 'status', 'message': m, 'target': 'player' if is_player_attacking else 'opponent', 'timestamp': len(turn_info['battle_events'])})
            move.pp -= 1
            return False
            
        context.accuracy = move.accuracy
        self.hooks.run('accuracy', context)
        if not self._check_move_accuracy(context):
            # If we missed while charging, clear active move
            attacker.active_move = None
            turn_info['battle_events'].append({'type': 'status', 'message': f"{self._get_pokemon_name(attacker)}'s {move.name} missed!", 'target': 'player' if is_player_attacking else 'opponent', 'timestamp': len(turn_info['battle_events'])})
            move.pp -= 1
            return False
            
        # Charge moves (Solar Beam, Fly, etc.)
        if move.flags.get('charge') and not attacker.active_move:
            is_instant = False
            if move.id == 'solarbeam' and self.weather == 'sunnyday': is_instant = True
            
            if not is_instant:
                attacker.active_move = {'move': move, 'turns': 1}
                msg = f"{self._get_pokemon_name(attacker)} is charging!"
                if move.id == 'solarbeam': msg = f"{self._get_pokemon_name(attacker)} absorbed light!"
                elif move.id == 'fly': msg = f"{self._get_pokemon_name(attacker)} flew up high!"
                elif move.id == 'dig': msg = f"{self._get_pokemon_name(attacker)} burrowed its way under the ground!"
                
                turn_info['battle_events'].append({'type': 'status', 'message': msg, 'target': 'player' if is_player_attacking else 'opponent', 'timestamp': len(turn_info['battle_events'])})
                move.pp -= 1
                return True
        
        # If we get here and had an active move, we are executing it now. Clear it.
        if attacker.active_move and attacker.active_move['move'].id == move.id:
            attacker.active_move = None
            
        context.base_power = move.power
        self.hooks.run('basePower', context)
        
        defender_side = self.player_side if defender == self.player_pokemon else self.opponent_side
        
        # Future Sight / Doom Desire
        if move.flags.get('futuremove'):
            if defender_side.future_move:
                turn_info['battle_events'].append({'type': 'status', 'message': f"But it failed!", 'timestamp': len(turn_info['battle_events'])})
                return False
            defender_side.future_move = {'move': move, 'attacker': attacker, 'turns': 2}
            turn_info['battle_events'].append({'type': 'status', 'message': f"{self._get_pokemon_name(attacker)} foresaw an attack!", 'timestamp': len(turn_info['battle_events'])})
            move.pp -= 1
            return True

        field = {'weather': self.weather, 'is_reflect': defender_side.reflect > 0, 'is_light_screen': defender_side.light_screen > 0, 'is_aurora_veil': defender_side.aurora_veil > 0}
        
        dmg, sub_dmg, eff_msg, stat_msg, weather_to_set = move.use_move(attacker, defender, self.weather, field=field)
        context.actual_damage, context.substitute_damage, context.status_message = dmg, sub_dmg, stat_msg
        
        self.hooks.run('damage', context)
        dmg = context.actual_damage
        
        if weather_to_set:
            self.set_weather(weather_to_set)
            self.weather_duration = 5
            w_name = weather_to_set.replace('day', ' sunlight').replace('dance', '').replace('hail', 'snow')
            turn_info['battle_events'].append({'type': 'status', 'message': f"The weather changed to {w_name}!", 'set_weather': weather_to_set, 'timestamp': len(turn_info['battle_events'])})
            
        prev_hp = defender.current_hp
        defender.take_damage(dmg, from_move=True)
        actual_dmg = prev_hp - defender.current_hp
        context.actual_damage = actual_dmg
        
        turn_info['battle_events'].append({'type': 'move', 'attacker_name': self._get_pokemon_name(attacker), 'defender_name': self._get_pokemon_name(defender), 'move': move_name, 'category': move.category, 'move_type': move.type, 'damage': actual_dmg, 'substitute_damage': sub_dmg, 'is_player': is_player_attacking, 'attacker_hp': attacker.current_hp, 'defender_hp': defender.current_hp, 'player_hp': self.player_pokemon.current_hp, 'opponent_hp': self.opponent_pokemon.current_hp, 'attacker_status': attacker.get_status_display(), 'defender_status': defender.get_status_display(), 'timestamp': len(turn_info['battle_events']), 'status_message': stat_msg})
        
        for event in defender.on_damage(actual_dmg): turn_info['battle_events'].append({**event, 'target': 'opponent' if is_player_attacking else 'player', 'timestamp': len(turn_info['battle_events'])})
        if defender.item_obj:
            for event in defender.item_obj.on_damage(defender, actual_dmg): turn_info['battle_events'].append({**event, 'target': 'opponent' if is_player_attacking else 'player', 'timestamp': len(turn_info['battle_events'])})
            
        if sub_dmg > 0: turn_info['battle_events'].append({'type': 'status', 'message': f"The substitute took damage!", 'target': 'opponent' if is_player_attacking else 'player', 'timestamp': len(turn_info['battle_events'])})
        if eff_msg: turn_info['battle_events'].append({'type': 'effectiveness', 'message': eff_msg, 'is_player': is_player_attacking, 'timestamp': len(turn_info['battle_events'])})
        
        move.pp -= 1
        self.hooks.run('onHit', context)
        turn_info['battle_events'].extend(context.events)
        context.events = []
        
        self.hooks.run('secondary', context)
        turn_info['battle_events'].extend(context.events)
        context.events = []
        
        self.hooks.run('afterMove', context)
        turn_info['battle_events'].extend(context.events)
        context.events = []
        
        # Hyper Beam / Recharge moves
        if move.flags.get('recharge'):
            attacker.must_recharge = True
            
        return defender.current_hp <= 0

    def start_battle(self, player_team_data: List[Dict], opponent_team_data: List[Dict]):
        self.player_team = []
        self.opponent_team = []
        for p_data in player_team_data:
            pokemon = self._create_pokemon_from_data(p_data, is_player=True)
            self.player_team.append(pokemon)
        for o_data in opponent_team_data:
            pokemon = self._create_pokemon_from_data(o_data, is_player=False)
            self.opponent_team.append(pokemon)
        if self.player_team: self.player_pokemon = self.player_team[0]
        if self.opponent_team: self.opponent_pokemon = self.opponent_team[0]
        messages = []
        if self.player_pokemon: messages.extend(self._on_pokemon_switch_in(self.player_pokemon, self.opponent_pokemon, self.player_side))
        if self.opponent_pokemon: messages.extend(self._on_pokemon_switch_in(self.opponent_pokemon, self.player_pokemon, self.opponent_side))
        return messages

    def _create_pokemon_from_data(self, data, is_player):
        pokemon = Pokemon(data['name'], data.get('types', ['normal']), data.get('sprite_url'), data.get('stats', {}), data.get('moves', []), level=data.get('level', 100), ability=data.get('ability', 'noability'), item=data.get('item', ''), evs=data.get('evs', {}), ivs=data.get('ivs', {}), nature=data.get('nature', 'Hardy'), cry_url=data.get('cry_url', ''))
        pokemon.is_player = is_player
        return pokemon

    def _on_pokemon_switch_in(self, pokemon, opponent, side) -> List[Dict]:
        events = []
        context = BattleContext(game=self, phase='switchIn', attacker=pokemon, defender=opponent)
        self.hooks.run('switchIn', context)
        events.extend(context.events)
        if pokemon.is_fainted():
            events.append({'type': 'faint', 'pokemon_name': self._get_pokemon_name(pokemon), 'is_player': pokemon.is_player})
        return events

    def check_battle_over(self) -> Tuple[bool, Optional[str]]:
        player_lost = all(p.is_fainted() for p in self.player_team)
        opponent_lost = all(p.is_fainted() for p in self.opponent_team)
        if player_lost: return True, "Opponent"
        if opponent_lost: return True, "Player"
        return False, None

    def _has_available_switch(self, is_player: bool) -> bool:
        team = self.player_team if is_player else self.opponent_team
        active = self.player_pokemon if is_player else self.opponent_pokemon
        return any(p is not active and not p.is_fainted() for p in team)

    def _first_available_switch_index(self, is_player: bool) -> Optional[int]:
        team = self.player_team if is_player else self.opponent_team
        active = self.player_pokemon if is_player else self.opponent_pokemon
        for idx, pokemon in enumerate(team):
            if pokemon is not active and not pokemon.is_fainted(): return idx
        return None

    def switch_pokemon(self, is_player: bool, index: int) -> List[Dict]:
        team = self.player_team if is_player else self.opponent_team
        side = self.player_side if is_player else self.opponent_side
        if index < 0 or index >= len(team): return []
        new_pokemon = team[index]
        if new_pokemon.is_fainted() or new_pokemon == (self.player_pokemon if is_player else self.opponent_pokemon): return []
        old_pokemon = self.player_pokemon if is_player else self.opponent_pokemon
        if old_pokemon: old_pokemon.volatile_statuses = set()
        if is_player: self.player_pokemon = new_pokemon
        else: self.opponent_pokemon = new_pokemon
        
        # Check if primal weather should end
        ended = self.check_primal_weather_end()
        
        events = []
        if ended:
            events.append({'type': 'status', 'message': "The mysterious weather dissipated!", 'timestamp': 0})
            
        old_display = self._get_pokemon_name(old_pokemon) if old_pokemon else "Pokemon"
        new_display = self._get_pokemon_name(new_pokemon)
        
        if old_pokemon and not old_pokemon.is_fainted():
            events.append({'type': 'recall', 'message': f"Come back, {old_display}!", 'is_player_switch': is_player, 'is_opponent_switch': not is_player, 'recalled_pokemon_name': old_pokemon.name})
        elif old_pokemon and old_pokemon.is_fainted():
            events.append({'type': 'recall', 'message': None, 'is_player_switch': is_player, 'is_opponent_switch': not is_player, 'recalled_pokemon_name': old_pokemon.name})
        
        events.append({'type': 'status', 'message': f"Go! {new_display}!", 'is_player_switch': is_player, 'is_opponent_switch': not is_player, 'new_pokemon_name': new_pokemon.name, 'player_hp': self.player_pokemon.current_hp, 'opponent_hp': self.opponent_pokemon.current_hp})
        
        # Trigger switch-in hooks (Entry Hazards, Intimidate, etc.)
        events.extend(self._on_pokemon_switch_in(new_pokemon, self.opponent_pokemon if is_player else self.player_pokemon, side))
        
        return events

    def handle_fainted(self, turn_info):
        """Check for fainted Pokemon and handle switches/victory."""
        faint_occurred = False
        
        # Check both pokemons
        processed_faints = [e.get('pokemon_name') for e in turn_info['battle_events'] if e.get('type') == 'faint']
        
        for pokemon in [self.opponent_pokemon, self.player_pokemon]:
            if pokemon and pokemon.current_hp <= 0:
                display_name = self._get_pokemon_name(pokemon)
                if display_name in processed_faints:
                    continue
                    
                is_player = pokemon == self.player_pokemon
                is_over, winner = self.check_battle_over()
                
                # Run faint hooks
                faint_context = BattleContext(game=self, phase='faint', attacker=None, defender=pokemon)
                self.hooks.run('faint', faint_context)
                turn_info['battle_events'].extend(faint_context.events)
                
                # Faint event
                turn_info['battle_events'].append({
                    'type': 'faint', 
                    'pokemon_name': display_name, 
                    'is_player': is_player, 
                    'timestamp': len(turn_info['battle_events']), 
                    'player_hp': self.player_pokemon.current_hp, 
                    'opponent_hp': self.opponent_pokemon.current_hp
                })
                
                faint_occurred = True
                
                if is_over:
                    self.battle_over, turn_info['winner'] = True, winner
                    return True
                
                # Check if primal weather should end
                if self.check_primal_weather_end():
                    turn_info['battle_events'].append({'type': 'status', 'message': "The mysterious weather dissipated!", 'timestamp': len(turn_info['battle_events'])})

                if not is_player: # Opponent fainted
                    new_idx = self.ai.select_switch(self.opponent_team, self.player_pokemon)
                    if new_idx is not None:
                        turn_info['battle_events'].extend(self.switch_pokemon(False, new_idx))
                else: # Player fainted
                    if self._has_available_switch(True):
                        turn_info['battle_events'].append({
                            'type': 'pending_switch',
                            'message': f"Choose a Pokemon to switch in!",
                            'target': 'player',
                            'is_player_switch': True
                        })
        
        return faint_occurred

    def process_turn(self, move_name=None, switch_index=None, mega=False):
        if self.battle_over: return {}
        if switch_index is not None:
            turn_info = {'player_move': 'Switch', 'battle_events': []}
            turn_info['battle_events'].extend(self.switch_pokemon(True, switch_index))
            return turn_info
        turn_info = {'player_move': move_name, 'initial_player_hp': self.player_pokemon.current_hp, 'initial_opponent_hp': self.opponent_pokemon.current_hp, 'player_damage': 0, 'opponent_damage': 0, 'battle_events': []}
        
        if mega and self.can_mega_evolve(True):
            self.perform_mega_evolution(True, turn_info)
            
        if self.can_mega_evolve(False):
            self.perform_mega_evolution(False, turn_info)
            
        before_turn_context = BattleContext(game=self, phase='beforeTurn')
        self.hooks.run('beforeTurn', before_turn_context)
        turn_info['battle_events'].extend(before_turn_context.events)
        STALLING_STATUSES = ['protect', 'spikyshield', 'banefulbunker', 'kingsshield', 'obstruct', 'silktrap', 'burningbulwark', 'endure']
        for p in [self.player_pokemon, self.opponent_pokemon]:
            if p:
                p.acted_this_turn = False
                for status in STALLING_STATUSES: p.volatile_statuses.discard(status)
        for p, target, is_player in [(self.player_pokemon, self.opponent_pokemon, True), (self.opponent_pokemon, self.player_pokemon, False)]:
            for msg in p.process_turn_start_effects():
                if msg: turn_info['battle_events'].append({'type': 'status', 'message': msg, 'target': 'player' if is_player else 'opponent', 'timestamp': len(turn_info['battle_events'])})
        if self.player_pokemon.current_hp <= 0 or self.opponent_pokemon.current_hp <= 0:
            is_over, winner = self.check_battle_over()
            if is_over: self.battle_over, turn_info['winner'] = True, winner
            return turn_info
        # Handle player locked moves
        if self.player_pokemon.active_move:
            player_move = self.player_pokemon.active_move['move']
            move_name = player_move.name
        elif self.player_pokemon.must_recharge:
            player_move = self.player_pokemon.moves.get(move_name) if move_name else next(iter(self.player_pokemon.moves.values()))
        else:
            player_move = self.player_pokemon.moves.get(move_name)
            
        if not player_move or player_move.pp <= 0: return turn_info
        
        # Handle opponent locked moves
        if self.opponent_pokemon.active_move:
            opponent_move = self.opponent_pokemon.active_move['move']
            opponent_move_name = opponent_move.name
        elif self.opponent_pokemon.must_recharge:
            opponent_move_name, opponent_move = next(iter(self.opponent_pokemon.moves.items()))
        else:
            opponent_move_name, opponent_move = self.ai.select_move(self.opponent_pokemon, self.player_pokemon, self.weather)
            if not opponent_move: opponent_move_name, opponent_move = next(iter(self.opponent_pokemon.moves.items()))
            
        turn_info['opponent_move'] = opponent_move_name
        player_action = create_battle_action(self.player_pokemon, player_move, self.opponent_pokemon, self.priority_resolver)
        opponent_action = create_battle_action(self.opponent_pokemon, opponent_move, self.player_pokemon, self.priority_resolver)
        action_order = self.priority_resolver.resolve_turn_order(player_action, opponent_action)
        turn_info['player_first'] = action_order[0].pokemon == self.player_pokemon
        for action in action_order:
            attacker = action.pokemon
            defender = self.opponent_pokemon if attacker == self.player_pokemon else self.player_pokemon
            is_player = attacker == self.player_pokemon
            
            # Attacker might have fainted from previous action's residual effects or something
            if attacker.current_hp <= 0: continue
            
            self.execute_move(attacker, defender, action.move, action.move.name, is_player, turn_info, action)
            attacker.acted_this_turn = True
            
            # Check for faints after move
            if self.handle_fainted(turn_info):
                break # Turn ends if someone fainted
                
        if not self.battle_over:
            residual_context = BattleContext(game=self, phase='residual')
            self.hooks.run('residual', residual_context)
            turn_info['battle_events'].extend(residual_context.events)
            
            # Check for faints after residuals (e.g. poison/burn/hazards)
            self.handle_fainted(turn_info)
            
            if not self.battle_over:
                end_turn_context = BattleContext(game=self, phase='endTurn')
                self.hooks.run('endTurn', end_turn_context)
                turn_info['battle_events'].extend(end_turn_context.events)
                
                # Future Move Processing
                for side in [self.player_side, self.opponent_side]:
                    if side.future_move:
                        side.future_move['turns'] -= 1
                        if side.future_move['turns'] <= 0:
                            fm = side.future_move
                            target = self.player_pokemon if side == self.player_side else self.opponent_pokemon
                            if target and not target.is_fainted():
                                # Recalculate damage at hit time
                                dmg, _, eff_msg, _, _ = fm['move'].use_move(fm['attacker'], target, self.weather)
                                target.take_damage(dmg)
                                turn_info['battle_events'].append({
                                    'type': 'move',
                                    'attacker_name': self._get_pokemon_name(fm['attacker']),
                                    'defender_name': self._get_pokemon_name(target),
                                    'move': fm['move'].name,
                                    'damage': dmg,
                                    'message': f"{self._get_pokemon_name(target)} took the {fm['move'].name} attack!",
                                    'target': 'player' if target == self.player_pokemon else 'opponent',
                                    'pokemon_hp': target.current_hp,
                                    'timestamp': len(turn_info['battle_events'])
                                })
                                if eff_msg: turn_info['battle_events'].append({'type': 'effectiveness', 'message': eff_msg, 'timestamp': len(turn_info['battle_events'])})
                            side.future_move = None

                # Final check after end-turn effects
                self.handle_fainted(turn_info)
                
        return turn_info

    def _get_priority_explanation_message(self, first_action, second_action):
        first_priority, second_priority = first_action.effective_priority, second_action.effective_priority
        first_name, second_name = first_action.pokemon.name.capitalize(), second_action.pokemon.name.capitalize()
        first_move, second_move = first_action.move.name, second_action.move.name
        if first_action.is_priority_counter and first_priority != -999: return f"{first_name}'s {first_move} intercepted {second_name}'s {second_move}!"
        if first_priority > second_priority:
            if first_priority > 0: return f"{first_name}'s {first_move} has higher priority (+{first_priority}) and goes first!"
            elif second_priority < 0: return f"{second_name}'s {second_move} has negative priority ({second_priority}) and goes last!"
            else: return f"{first_name}'s {first_move} has priority (+{first_priority}) and goes first!"
        elif first_priority == second_priority and first_priority != 0:
            first_speed, second_speed = getattr(first_action.pokemon, 'speed', 0), getattr(second_action.pokemon, 'speed', 0)
            if first_speed > second_speed: return f"Both moves have priority {'+' + str(first_priority) if first_priority >= 0 else str(first_priority)}, but {first_name} is faster!"
            elif second_speed > first_speed: return f"Both moves have priority {'+' + str(first_priority) if first_priority >= 0 else str(first_priority)}, but {first_name} got lucky!"
            else: return f"Both moves have priority {'+' + str(first_priority) if first_priority >= 0 else str(first_priority)}, turn order was random!"
        elif first_priority == second_priority == 0:
            first_speed, second_speed = getattr(first_action.pokemon, 'speed', 0), getattr(second_action.pokemon, 'speed', 0)
            if abs(first_speed - second_speed) > 10:
                if first_speed > second_speed: return f"{first_name} is faster and goes first!"
                else: return f"{first_name} got lucky and goes first!"
        return None

    def is_battle_over(self): return self.player_pokemon.is_fainted() or self.opponent_pokemon.is_fainted()

    def get_battle_result(self):
        player_lost = all(p.is_fainted() for p in self.player_team)
        opponent_lost = all(p.is_fainted() for p in self.opponent_team)
        if player_lost: return "Opponent wins the battle!"
        elif opponent_lost: return "Player wins the battle!"
        return "Battle ongoing"
