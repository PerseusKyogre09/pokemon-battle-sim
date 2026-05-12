from ..utils.data_loader import data_loader
from ..systems.damage_engine import smogon_damage_for_move
from typing import Optional, Tuple, Dict, Any, Union, List
import random
import re

class Move:
    def __init__(self, name: str, move_data: Optional[Dict[str, Any]] = None):
        self.name = name
        self.data = move_data if move_data else data_loader.get_move(name)
        self.id = self.data.get('id', name.lower().replace(' ', '')) if self.data else name.lower()
        
        if not self.data:
            self.power = 0
            self.pp = 10
            self.max_pp = 10
            self.type = 'normal'
            self.accuracy = 100
            self.category = 'physical'
            self.priority = 0
            self.is_status_move = True
            self.priority_counter_conditions = None
            self.is_priority_counter = False
        else:
            self.power = self.data.get('basePower', 0)
            self.pp = self.data.get('pp', 10)
            self.max_pp = self.pp
            self.type = self.data.get('type', 'normal').lower()
            self.accuracy = self.data.get('accuracy', 100)
            self.category = self.data.get('category', 'physical').lower()
            self.priority = self.data.get('priority', 0)
            self.is_status_move = self.category == 'status' or self.power == 0
            self.priority_counter_conditions = self.data.get('priority_counter_conditions')
            self.is_priority_counter = self.data.get('is_priority_counter', False)
        
        self.is_healing_move, self.heal_amount, self.drain_ratio = self._parse_healing_data()
        self.is_multihit_move, self.multihit_data = self._parse_multihit_data()
        self.stat_modifications, self.targets_self = self._parse_stat_modifications()
        self.is_recoil_move, self.recoil_ratio = self._parse_recoil_data()
        
        data_dict = self.data or {}
        self.fixed_damage = data_dict.get('damage')
        self.self_switch = data_dict.get('selfSwitch')
        self.volatile_status = data_dict.get('volatileStatus')
        self.stalling_move = data_dict.get('stallingMove', False)
        self.target = data_dict.get('target', 'normal')
        self.flags = data_dict.get('flags', {})
        self.ohko = data_dict.get('ohko', False)
        self.defensive_category = data_dict.get('defensiveCategory')
        self.use_target_offensive = data_dict.get('useTargetOffensive', False)
        self.effectiveness = 1.0
        self.damage_source = 'python'
        self.last_damage_range = None
        self.last_damage_description = None

    def _parse_chain_modify(self, logic_str: str) -> float:
        """Extract multiplier from chainModify([num1, num2]) or chainModify(float)."""
        if not logic_str or "chainModify" not in logic_str:
            return 1.0
            
        # Look for [num1, num2] pattern
        match = re.search(r'chainModify\(\[?([\d., ]+)\]?\)', logic_str)
        if match:
            parts = [p.strip() for p in match.group(1).split(',')]
            if len(parts) >= 2:
                try:
                    return float(parts[0]) / float(parts[1])
                except (ValueError, ZeroDivisionError):
                    return 1.0
            else:
                try:
                    return float(parts[0])
                except ValueError:
                    return 1.0
        
        # Look for modify(stat, mult) pattern
        match = re.search(r'this\.modify\([^,]+,\s*([\d.]+)\)', logic_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 1.0
                
        return 1.0

    def _check_condition(self, logic_str: str, pokemon, opponent, move=None) -> bool:
        """Check if conditions in logic_str are met."""
        if not logic_str:
            return True
            
        if "target.getItem()" in logic_str or "target.item" in logic_str:
            return True 
            
        if "hp <= pokemon.maxhp / 4" in logic_str:
            if pokemon.current_hp <= pokemon.max_hp / 4:
                return True
            return False

        return True

    def _get_damage_stat(self, pokemon, stat_name: str, is_critical: bool, role: str) -> int:
        base = pokemon.base_stats.get(stat_name, 10)
        level = getattr(pokemon, 'level', 100)
        mapping = {'attack': 'atk', 'defense': 'def', 'special_attack': 'spa', 'special_defense': 'spd'}
        key = mapping.get(stat_name, stat_name)
        iv = pokemon.ivs.get(key, 31)
        ev = pokemon.evs.get(key, 0)

        stat = int(((2 * base + iv + int(ev / 4)) * level) / 100) + 5
        natures = {
            'Adamant': ('attack', 'special_attack'), 'Bold': ('defense', 'attack'),
            'Brave': ('attack', 'speed'), 'Calm': ('special_defense', 'attack'),
            'Careful': ('special_defense', 'special_attack'), 'Gentle': ('special_defense', 'defense'),
            'Hasty': ('speed', 'defense'), 'Impish': ('defense', 'special_attack'),
            'Jolly': ('speed', 'special_attack'), 'Lax': ('defense', 'special_defense'),
            'Lonely': ('attack', 'defense'), 'Mild': ('special_attack', 'defense'),
            'Modest': ('special_attack', 'attack'), 'Naive': ('speed', 'special_defense'),
            'Naughty': ('attack', 'special_defense'), 'Quiet': ('special_attack', 'speed'),
            'Rash': ('special_attack', 'special_defense'), 'Relaxed': ('defense', 'speed'),
            'Sassy': ('special_defense', 'speed'), 'Timid': ('speed', 'attack')
        }
        plus, minus = natures.get(pokemon.nature, (None, None))
        if plus == stat_name:
            stat = int(stat * 1.1)
        elif minus == stat_name:
            stat = int(stat * 0.9)

        stage = pokemon.stat_stages.get(stat_name, 0)
        if is_critical and role == 'attacker' and stage < 0:
            stage = 0
        elif is_critical and role == 'defender' and stage > 0:
            stage = 0

        stat = int(stat * pokemon.get_stat_stage_multiplier(stage))
        if hasattr(pokemon, 'ability'):
            stat = pokemon.ability.modify_stat(pokemon, stat_name, stat)
        if pokemon.item_obj:
            stat = pokemon.item_obj.modify_stat(pokemon, stat_name, stat)
        return max(1, stat)

    def _get_critical_hit(self, defending_pokemon=None) -> bool:
        if defending_pokemon and hasattr(defending_pokemon, 'ability') and defending_pokemon.ability.id in ['battlearmor', 'shellarmor']:
            return False
        crit_ratio = self.data.get('critRatio', 1)
        will_crit = self.data.get('willCrit', False)
        crit_chances = {1: 1/16, 2: 1/8, 3: 1/2, 4: 1.0}
        crit_chance = crit_chances.get(crit_ratio, 1.0) if crit_ratio in crit_chances else (1.0 if crit_ratio > 4 else 1/16)
        return will_crit or random.random() < crit_chance

    def _get_burn_multiplier(self, attacking_pokemon) -> float:
        if self.category != 'physical':
            return 1.0
        if self.id == 'facade':
            return 1.0
        if not attacking_pokemon or not getattr(attacking_pokemon, 'major_status', None) == 'burn':
            return 1.0
        if hasattr(attacking_pokemon, 'ability') and attacking_pokemon.ability.id == 'guts':
            return 1.0
        return 0.5
    
    def _parse_healing_data(self) -> Tuple[bool, Optional[List[int]], Optional[List[int]]]:
        if not self.data:
            return False, None, None
        
        is_healing = False
        heal_amount = None
        drain_ratio = None
        
        if 'heal' in self.data and isinstance(self.data['heal'], list):
            is_healing = True
            heal_amount = self.data['heal']
        
        if 'drain' in self.data and isinstance(self.data['drain'], list):
            is_healing = True
            drain_ratio = self.data['drain']
        
        if 'flags' in self.data and isinstance(self.data['flags'], dict):
            if self.data['flags'].get('heal') == 1:
                is_healing = True
        
        return is_healing, heal_amount, drain_ratio
    
    def _parse_multihit_data(self) -> Tuple[bool, Optional[Union[int, List[int]]]]:
        if not self.data:
            return False, None
        
        if 'multihit' in self.data:
            multihit_data = self.data['multihit']
            if isinstance(multihit_data, int):
                return True, multihit_data
            elif isinstance(multihit_data, list) and len(multihit_data) == 2:
                return True, multihit_data
            elif multihit_data is not None:
                return False, None
        
        return False, None
    
    def _apply_boosts(self, pokemon, boosts: Dict[str, int]) -> List[str]:
        if not boosts or not pokemon:
            return []
            
        stat_name_mapping = {
            'atk': 'attack',
            'def': 'defense',
            'spa': 'special_attack',
            'spd': 'special_defense',
            'spe': 'speed',
            'accuracy': 'accuracy',
            'evasion': 'evasion'
        }
        
        messages = []
        for stat_abbrev, stages in boosts.items():
            full_stat_name = stat_name_mapping.get(stat_abbrev, stat_abbrev)
            if hasattr(pokemon, 'modify_stat_stage'):
                msg = pokemon.modify_stat_stage(full_stat_name, stages)
                if msg:
                    messages.append(msg)
                    
        return messages

    def _parse_stat_modifications(self) -> Tuple[Optional[Dict[str, int]], bool]:
        if not self.data:
            return None, False
        
        stat_modifications = self.data.get('boosts')
        targets_self = False
        
        if 'target' in self.data:
            target = self.data['target']
            if target in ['self']:
                targets_self = True
        
        return stat_modifications, targets_self
    
    def _parse_recoil_data(self) -> Tuple[bool, Optional[List[int]]]:
        if not self.data:
            return False, None
        
        if 'recoil' in self.data and isinstance(self.data['recoil'], list):
            recoil_data = self.data['recoil']
            if len(recoil_data) == 2 and all(isinstance(x, (int, float)) for x in recoil_data):
                return True, recoil_data
            else:
                return False, None
        
        return False, None
    
    def _determine_hit_count(self) -> int:
        if not self.is_multihit_move or not self.multihit_data:
            return 1
        
        if isinstance(self.multihit_data, int):
            return self.multihit_data
        elif isinstance(self.multihit_data, list) and len(self.multihit_data) == 2:
            min_hits, max_hits = self.multihit_data
            
            if max_hits == 5:
                rand = random.randint(1, 100)
                if rand <= 35:
                    return 2
                elif rand <= 70:
                    return 3
                elif rand <= 85:
                    return 4
                else:
                    return 5
            else:
                return random.randint(min_hits, max_hits)
        
        return 1
    
    def is_priority_counter_move(self) -> bool:
        return self.is_priority_counter
    
    def can_counter_move(self, target_move: 'Move') -> bool:
        if not self.is_priority_counter:
            return False
        
        if not target_move:
            return False
        
        from ..systems.priority_system import SuckerPunchHandler
        
        if self.name.lower() == 'sucker punch':
            handler = SuckerPunchHandler()
            return handler.check_success_condition(target_move)
        
        if self.priority_counter_conditions:
            counters = self.priority_counter_conditions.get('counters', [])
            fails_against = self.priority_counter_conditions.get('fails_against', [])
            target_category = target_move.category.lower()
            
            if target_category in counters:
                return True
            if target_category in fails_against:
                return False
        
        return not target_move.is_status_move
    
    def get_priority_counter_failure_message(self) -> str:
        if not self.is_priority_counter:
            return ""
        
        from ..systems.priority_system import SuckerPunchHandler
        
        if self.name.lower() == 'sucker punch':
            handler = SuckerPunchHandler()
            return handler.get_failure_message()
        
        if self.priority_counter_conditions:
            return self.priority_counter_conditions.get('failure_message', "But it failed!")
        
        return "But it failed!"
    
    def validate_move_category_for_counter(self, target_move: 'Move') -> Tuple[bool, str]:
        if not self.is_priority_counter:
            return True, ""
        
        if not target_move:
            return False, self.get_priority_counter_failure_message()
        
        from ..systems.priority_system import SuckerPunchHandler
        
        if self.name.lower() == 'sucker punch':
            handler = SuckerPunchHandler()
            return handler.validate_target_move_category(target_move)
        
        can_counter = self.can_counter_move(target_move)
        
        if can_counter:
            return True, f"{self.name} intercepted {target_move.name}!"
        else:
            return False, self.get_priority_counter_failure_message()
    
    def get_effective_priority_against_move(self, target_move: Optional['Move']) -> int:
        if not self.is_priority_counter or not target_move:
            return self.priority
        
        from ..systems.priority_system import SuckerPunchHandler
        
        if self.name.lower() == 'sucker punch':
            handler = SuckerPunchHandler()
            return handler.get_effective_priority(target_move)
        
        if self.can_counter_move(target_move):
            if self.priority_counter_conditions:
                return self.priority_counter_conditions.get('priority_when_successful', self.priority)
        
        return self.priority

    def _check_accuracy(self, attacker, defender) -> bool:
        if self.accuracy is True:
            return True
            
        if not isinstance(self.accuracy, (int, float)):
            return True
            
        # Base accuracy from the move
        base_accuracy = self.accuracy
        if self.ohko and attacker and defender:
            level_delta = getattr(attacker, 'level', 100) - getattr(defender, 'level', 100)
            if level_delta < 0:
                return False
            base_accuracy = 30 + level_delta
        
        # Accuracy/Evasion stage multipliers
        acc_stage = attacker.stat_stages.get('accuracy', 0)
        eva_stage = defender.stat_stages.get('evasion', 0)
        
        # Formula for acc/eva stage multiplier: (3 + stage) / 3 if stage > 0, 3 / (3 - stage) if stage < 0
        def get_multiplier(stage):
            if stage > 0:
                return (3 + stage) / 3
            elif stage < 0:
                return 3 / (3 - stage)
            return 1.0
            
        # Effective accuracy = base_accuracy * (acc_multiplier / eva_multiplier)
        # Simplified: combine stages
        combined_stage = max(-6, min(6, acc_stage - eva_stage))
        stage_multiplier = get_multiplier(combined_stage)
        
        effective_accuracy = base_accuracy * stage_multiplier
        
        # Ability modifiers
        if hasattr(attacker, 'ability'):
            # Victory Star (simplified: +10% to all moves)
            if attacker.ability.id == 'victorystar':
                effective_accuracy *= 1.1
            # Compound Eyes (+30%)
            elif attacker.ability.id == 'compoundeyes':
                effective_accuracy *= 1.3
        
        if hasattr(defender, 'ability'):
            # Tangled Feet: 1.5x evasion (0.66x accuracy) when confused
            if defender.ability.id == 'tangledfeet' and 'confusion' in defender.volatile_statuses:
                effective_accuracy *= 0.66
            # Sand Veil / Snow Cloak in weather
            # (Need weather access here, but for now we'll skip or use a simple check)
            
        return random.randint(1, 100) <= effective_accuracy

    def _apply_effect_block(self, target, effect_block: Dict[str, Any], chance_override: Optional[int] = None, user=None) -> List[str]:
        if not effect_block or not target:
            return []

        if hasattr(target, 'substitute_hp') and target.substitute_hp > 0 and (user is None or target != user):
            return []
            
        chance = chance_override if chance_override is not None else effect_block.get('chance', 100)
        if random.randint(1, 100) > chance:
            return []
            
        messages = []
        
        if 'status' in effect_block:
            status_type = effect_block['status']
            msg = target.apply_status_effect(status_type)
            if msg:
                messages.append(msg)
                
        if 'volatileStatus' in effect_block:
            v_status = effect_block['volatileStatus']
            if hasattr(target, 'apply_volatile_status'):
                msg = target.apply_volatile_status(v_status)
                if msg:
                    messages.append(msg)
                
        if 'boosts' in effect_block:
            boost_msgs = self._apply_boosts(target, effect_block['boosts'])
            messages.extend(boost_msgs)
            
        if 'self' in effect_block and user:
            self_msgs = self._apply_effect_block(user, effect_block['self'], user=user)
            messages.extend(self_msgs)
            
        return messages

    def _apply_secondary_effects(self, user, target) -> List[str]:
        messages = []
        
        multiplier = 2.0 if hasattr(user, 'has_ability') and user.has_ability('serenegrace') else 1.0
        
        if 'secondary' in self.data and self.data['secondary']:
            chance = self.data['secondary'].get('chance', 100) * multiplier
            msgs = self._apply_effect_block(target, self.data['secondary'], chance_override=chance, user=user)
            messages.extend(msgs)
            
        if 'secondaries' in self.data and self.data['secondaries']:
            for effect in self.data['secondaries']:
                chance = effect.get('chance', 100) * multiplier
                msgs = self._apply_effect_block(target, effect, chance_override=chance, user=user)
                messages.extend(msgs)
                
        return messages

    def _apply_self_effects(self, user, target) -> List[str]:
        messages = []
        
        if 'self' in self.data and self.data['self']:
            msgs = self._apply_effect_block(user, self.data['self'], user=user)
            messages.extend(msgs)
            
        if self.stat_modifications and self.targets_self:
            boost_msgs = self._apply_boosts(user, self.stat_modifications)
            messages.extend(boost_msgs)
            
        return messages

    def _apply_status_effects(self, user, target) -> List[str]:
        if not self.is_status_move or not self.data:
            return []
            
        # Determine actual target for status effects
        effective_target = user if self.target == 'self' else target
        if not effective_target:
            return []
            
        messages = []
        if effective_target.substitute_hp > 0 and effective_target != user:
            bypasses = self.flags.get('sound') or (hasattr(user, 'ability') and user.ability.id == 'infiltrator')
            if not bypasses:
                return [f"{effective_target.name} is behind a substitute!"]

        if 'status' in self.data:
            msg = effective_target.apply_status_effect(self.data['status'])
            if msg:
                messages.append(msg)
        
        if 'volatileStatus' in self.data:
            if hasattr(effective_target, 'apply_volatile_status'):
                msg = effective_target.apply_volatile_status(self.data['volatileStatus'])
                if msg:
                    if self.data['volatileStatus'] == 'protect':
                        # Protect is handled specially in the game loop for announcements
                        pass
                    else:
                        messages.append(msg)
                    
        secondary_msgs = self._apply_secondary_effects(user, target)
        messages.extend(secondary_msgs)
            
        return messages
    
    def _calculate_heal_amount(self, user, damage_dealt: int = 0) -> int:
        try:
            if not user or not hasattr(user, 'max_hp'):
                return 0
            
            if damage_dealt < 0:
                damage_dealt = 0
            
            if not self.is_healing_move:
                return 0
            
            if self.heal_amount is not None:
                try:
                    if not isinstance(self.heal_amount, list) or len(self.heal_amount) != 2:
                        return 0
                    
                    numerator, denominator = self.heal_amount
                    heal_fraction = numerator / denominator
                    heal_amount = int(user.max_hp * heal_fraction)
                    
                    if heal_fraction > 0 and heal_amount == 0:
                        heal_amount = 1
                    
                    return max(0, heal_amount)
                except (TypeError, ValueError, ZeroDivisionError):
                    return 0
            
            elif self.drain_ratio is not None:
                try:
                    if not isinstance(self.drain_ratio, list) or len(self.drain_ratio) != 2:
                        return 0
                    
                    numerator, denominator = self.drain_ratio
                    if damage_dealt <= 0:
                        return 0
                    
                    drain_fraction = numerator / denominator
                    heal_amount = int(damage_dealt * drain_fraction)
                    
                    if drain_fraction > 0 and damage_dealt > 0 and heal_amount == 0:
                        heal_amount = 1
                    
                    return max(0, heal_amount)
                except (TypeError, ValueError, ZeroDivisionError):
                    return 0
            else:
                return 0
                
        except Exception:
            return 0

    def _apply_healing_effects(self, user, target, damage_dealt: int = 0) -> List[str]:
        messages = []
        try:
            if not user or not hasattr(user, 'current_hp') or not hasattr(user, 'max_hp'):
                return messages
            
            if not self.is_healing_move:
                return messages
            
            heal_amount = self._calculate_heal_amount(user, damage_dealt)
            
            if heal_amount <= 0:
                if self.drain_ratio is not None and damage_dealt <= 0:
                    return messages
                if self.heal_amount is not None:
                    if user.current_hp >= user.max_hp:
                        messages.append(f"{user.name} is already at full health!")
                    return messages
                return messages
            
            hp_before = user.current_hp
            user.heal(heal_amount)
            actual_heal = user.current_hp - hp_before
            
            if actual_heal <= 0:
                messages.append(f"{user.name} is already at full health!")
            else:
                if self.heal_amount is not None:
                    messages.append(f"{user.name} recovered {actual_heal} HP!")
                elif self.drain_ratio is not None:
                    if actual_heal > 0:
                        messages.append(f"{user.name} recovered {actual_heal} HP!")
                        messages.append(f"{target.name if target else 'The target'}'s energy was drained!")
                    else:
                        messages.append(f"{target.name if target else 'The target'}'s energy was drained!")
                else:
                    messages.append(f"{user.name} recovered {actual_heal} HP!")
            
        except Exception:
            pass
        
        return messages

    def _calculate_recoil_damage(self, user, damage_dealt: int) -> int:
        try:
            if not user or not hasattr(user, 'max_hp') or damage_dealt <= 0 or not self.is_recoil_move or not self.recoil_ratio:
                return 0
            
            numerator, denominator = self.recoil_ratio
            recoil_fraction = numerator / denominator
            recoil_damage = int(damage_dealt * recoil_fraction)
            
            if recoil_fraction > 0 and damage_dealt > 0 and recoil_damage == 0:
                recoil_damage = 1
            
            return max(0, recoil_damage)
        except Exception:
            return 0

    def _apply_recoil_effects(self, user, damage_dealt: int) -> List[str]:
        messages = []
        try:
            if not user or not hasattr(user, 'current_hp') or not hasattr(user, 'max_hp') or not self.is_recoil_move:
                return messages
            
            recoil_damage = self._calculate_recoil_damage(user, damage_dealt)
            if recoil_damage <= 0:
                return messages
            
            user.take_damage(recoil_damage)
            messages.append(f"{user.name} is hurt by recoil!")
        except Exception:
            pass
        
        return messages

    def _handle_special_moves(self, attacking_pokemon, defending_pokemon):
        move_name_lower = self.name.lower()
        if move_name_lower == 'belly drum':
            return self._handle_belly_drum(attacking_pokemon)
        return None
    
    def _handle_belly_drum(self, user):
        if user.stat_stages.get('attack', 0) >= 6:
            return 0, f"{user.name} used {self.name}!", f"{user.name}'s Attack won't go any higher!"
        
        hp_cost = user.max_hp // 2
        if user.current_hp <= hp_cost:
            return 0, f"{user.name} used {self.name}!", f"But it failed!"
        
        user.current_hp -= hp_cost
        user.stat_stages['attack'] = 6
        user._recalculate_stats()
        
        move_desc = data_loader.get_move_description(self.name)
        if move_desc and 'boost' in move_desc:
            boost_message = move_desc['boost'].replace('[POKEMON]', user.name)
        else:
            boost_message = f"{user.name} cut its own HP and maximized its Attack!"
        
        return 0, f"{user.name} used {self.name}!", boost_message

    def _apply_stat_modifications(self, user, target) -> List[str]:
        if not self.stat_modifications:
            return []
            
        modification_target = user if self.target == 'self' else target
        if not modification_target:
            return []
            
        return self._apply_boosts(modification_target, self.stat_modifications)

    def use_move(self, attacking_pokemon=None, defending_pokemon=None, weather='none', field=None) -> Tuple[int, int, str, Optional[str], Optional[str]]:
        self.damage_source = 'python'
        self.last_damage_range = None
        self.last_damage_description = None
            
        if self.stalling_move:
            success_rate = 1.0 / (3.0 ** attacking_pokemon.consecutive_stalling_moves)
            if random.random() >= success_rate:
                attacking_pokemon.consecutive_stalling_moves = 0
                return 0, 0, "", f"But it failed!", None
            attacking_pokemon.consecutive_stalling_moves += 1
        else:
            attacking_pokemon.consecutive_stalling_moves = 0

        # Special handling for Substitute
        if self.id == 'substitute':
            if attacking_pokemon.substitute_hp > 0:
                return 0, 0, "", "But it failed!", None
            cost = attacking_pokemon.max_hp // 4
            if attacking_pokemon.current_hp > cost:
                attacking_pokemon.current_hp -= cost
                attacking_pokemon.substitute_hp = cost
                attacking_pokemon.apply_volatile_status('substitute')
                return 0, 0, "", f"{attacking_pokemon.name} put in a substitute!", None
            else:
                return 0, 0, "", "But it failed!", None

        if self.is_status_move or self.power == 0:
            # Check for special moves first (like Belly Drum)
            special_move_result = self._handle_special_moves(attacking_pokemon, defending_pokemon)
            if special_move_result:
                damage, usage_msg, status_msg = special_move_result
                return damage, 0, usage_msg, status_msg, None
            
            status_messages = []
            if defending_pokemon:
                status_messages = self._apply_status_effects(attacking_pokemon, defending_pokemon)
            
            # Apply healing effects for status moves (like Recover)
            healing_messages = []
            if attacking_pokemon:
                healing_messages = self._apply_healing_effects(attacking_pokemon, defending_pokemon, 0)
            
            # Apply stat modifications for status moves
            stat_modification_messages = []
            if self.stat_modifications:
                stat_modification_messages = self._apply_stat_modifications(attacking_pokemon, defending_pokemon)
            
            # Combine status, healing, and stat modification messages
            all_messages = status_messages + healing_messages + stat_modification_messages
            combined_message = " ".join(all_messages) if all_messages else None
            return 0, 0, "", combined_message, None
        
        # Handle multi-hit moves
        if self.is_multihit_move:
            return self._use_multihit_move(attacking_pokemon, defending_pokemon)
        
        # If we get here, it's a single-hit damaging move
        base_damage = self.power
        effectiveness_message = ""
        
        # Check for weather-setting moves
        weather_to_set = None
        WEATHER_MOVES = {
            'raindance': 'raindance', 'sunnyday': 'sunnyday',
            'sandstorm': 'sandstorm', 'hail': 'hail', 'snowscape': 'hail'
        }
        if self.id in WEATHER_MOVES:
            weather_to_set = WEATHER_MOVES[self.id]

        # If it's a status move, it shouldn't have any damage calculation
        if self.is_status_move or self.power == 0:
            return 0, 0, f"{attacking_pokemon.name} used {self.name}!", "", weather_to_set
        
        # Apply type effectiveness if both Pokemon are provided
        if attacking_pokemon and defending_pokemon:
            # Check for ability immunities (e.g. Levitate)
            if hasattr(defending_pokemon, 'ability'):
                if defending_pokemon.ability.is_immune(self.type, self.category):
                    return 0, 0, f"It had no effect on {defending_pokemon.name}!", None, weather_to_set

            # Get the move type in lowercase for comparison
            move_type = self.type.lower()
            
            # Get defending Pokémon's types, handling both single and dual types
            if hasattr(defending_pokemon, 'types') and isinstance(defending_pokemon.types, list) and defending_pokemon.types:
                defending_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in defending_pokemon.types]
            else:
                # Fallback for backward compatibility
                defending_types = [getattr(defending_pokemon, 'type', 'normal').lower()]
                
            # Calculate effectiveness against each of the target's types
            effectiveness = 1.0
            # Calculate effectiveness against each of the target's types
            effectiveness = 1.0
            
            for target_type in defending_types:
                effectiveness *= data_loader.get_type_effectiveness(move_type, target_type)
                
            effectiveness = round(effectiveness, 2)
            self.effectiveness = effectiveness
            is_critical = self._get_critical_hit(defending_pokemon)
            
            # Determine attack and defense stats based on move category
            defending_types_lower = [t.lower() for t in defending_pokemon.types]
            
            # Determine which offensive stat to use
            if self.use_target_offensive:
                # Foul Play: Use target's attack stat
                attack_stat = self._get_damage_stat(defending_pokemon, 'attack', is_critical, 'attacker')
                attack_name = "Target's Attack"
            elif self.category == 'physical':
                attack_stat = self._get_damage_stat(attacking_pokemon, 'attack', is_critical, 'attacker')
                attack_name = 'Attack'
            else: # 'special'
                attack_stat = self._get_damage_stat(attacking_pokemon, 'special_attack', is_critical, 'attacker')
                attack_name = 'Special Attack'
                
            # Determine which defensive stat to use
            effective_defensive_category = self.defensive_category.lower() if self.defensive_category else self.category
            
            if effective_defensive_category == 'physical':
                defense_stat = self._get_damage_stat(defending_pokemon, 'defense', is_critical, 'defender')
                # Gen 9 Snow (replaces Hail): +50% Defense for Ice types
                if weather == 'hail' and 'ice' in defending_types_lower:
                    defense_stat = int(defense_stat * 1.5)
                defense_name = 'Defense'
            else: # 'special'
                defense_stat = self._get_damage_stat(defending_pokemon, 'special_defense', is_critical, 'defender')
                # Sandstorm: +50% Special Defense for Rock types
                if weather == 'sandstorm' and 'rock' in defending_types_lower:
                    defense_stat = int(defense_stat * 1.5)
                defense_name = 'Special Defense'
            level = getattr(attacking_pokemon, 'level', 100)
            move_name_lower = self.name.lower()
            smogon_result = smogon_damage_for_move(
                attacking_pokemon,
                defending_pokemon,
                self,
                field or {'weather': weather}
            )
            
            if self.fixed_damage:
                if isinstance(self.fixed_damage, int):
                    damage = self.fixed_damage
                elif self.fixed_damage == 'level':
                    damage = level
                else:
                    damage = 40
                if effectiveness == 0:
                    effectiveness_message = "It had no effect..."
                    return 0, 0, effectiveness_message, None, weather_to_set
                base_damage = damage
            elif smogon_result:
                base_damage = int(smogon_result["selected_damage"])
                self.damage_source = 'smogon'
                self.last_damage_range = [int(smogon_result["min"]), int(smogon_result["max"])]
                self.last_damage_description = smogon_result.get("description")

                if effectiveness == 0:
                    effectiveness_message = "It had no effect..."
                    return 0, 0, effectiveness_message, None, weather_to_set
                elif effectiveness < 1:
                    effectiveness_message = "It's not very effective..."
                elif effectiveness > 1:
                    effectiveness_message = "It's super effective!"
            else:
                # Check for special move logic in JSON generically
                actual_base_power = base_damage
                for hook in ["onBasePower", "onModifyMove"]:
                    logic = self.data.get(hook)
                    if not logic: continue
                    
                    if self._check_condition(logic, attacking_pokemon, defending_pokemon, self):
                        multiplier = self._parse_chain_modify(logic)
                        actual_base_power = int(actual_base_power * multiplier)

                damage = ((2 * level / 5 + 2) * actual_base_power * attack_stat / defense_stat) / 50 + 2
                damage = int(damage)

                # Apply effectiveness
                damage = int(damage * effectiveness)
                
                # Apply weather multipliers
                if weather == 'raindance':
                    if move_type == 'water':
                        damage = int(damage * 1.5)
                    elif move_type == 'fire':
                        damage = int(damage * 0.5)
                elif weather == 'sunnyday':
                    if move_type == 'fire':
                        damage = int(damage * 1.5)
                    elif move_type == 'water':
                        damage = int(damage * 0.5)
                elif weather == 'hail': # Gen 9 Snow
                    if move_type == 'ice':
                        damage = int(damage * 1.5)
                
                if effectiveness == 0:
                    effectiveness_message = "It had no effect..."
                    return 0, 0, effectiveness_message, None, weather_to_set
                elif effectiveness < 1:
                    effectiveness_message = "It's not very effective..."
                elif effectiveness > 1:
                    effectiveness_message = "It's super effective!"
                
                # Apply STAB (Same Type Attack Bonus) - 1.5x (or 2x with Adaptability)
                if hasattr(attacking_pokemon, 'types') and attacking_pokemon.types:
                    attacker_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in attacking_pokemon.types]
                    if move_type in attacker_types:
                        stab_multiplier = 1.5
                        if hasattr(attacking_pokemon, 'ability'):
                            stab_multiplier = attacking_pokemon.ability.get_stab_multiplier()
                        damage = int(damage * stab_multiplier)
                
                if is_critical:
                    damage = int(damage * 1.5)
                    if effectiveness_message:
                        effectiveness_message = "A critical hit! " + effectiveness_message
                    else:
                        effectiveness_message = "A critical hit!"
                
                damage = int(damage * random.randint(85, 100) / 100)
                damage = max(1, int(damage * self._get_burn_multiplier(attacking_pokemon)))
                
                # Apply ability damage modifiers (e.g. Blaze, Technician)
                if hasattr(attacking_pokemon, 'ability'):
                    damage = attacking_pokemon.ability.modify_damage_dealt(attacking_pokemon, defending_pokemon, self, damage)
                
                base_damage = damage

            has_substitute = getattr(defending_pokemon, 'substitute_hp', 0) > 0
            bypasses_substitute = self.flags.get('sound') or (hasattr(attacking_pokemon, 'ability') and attacking_pokemon.ability.id == 'infiltrator')
            if base_damage > 0 and has_substitute and not bypasses_substitute:
                substitute_damage = min(base_damage, defending_pokemon.substitute_hp)
                defending_pokemon.substitute_hp -= substitute_damage
                return 0, substitute_damage, effectiveness_message, None, weather_to_set
        
        # Apply status effects after damage calculation
        # Apply secondary effects, self effects, healing, and recoil
        
        
        
        
        
        # Apply legacy status effects for status moves
        status_messages = []
        if self.is_status_move and defending_pokemon:
            status_messages = self._apply_status_effects(attacking_pokemon, defending_pokemon)
        
        # Combine all messages
        all_messages = status_messages
        
        combined_message = " ".join(all_messages) if all_messages else None
        
        return base_damage, 0, effectiveness_message, combined_message, weather_to_set
    
    def _use_multihit_move(self, attacking_pokemon, defending_pokemon) -> Tuple[int, int, str, Optional[str]]:
        """Handle multi-hit moves like Pin Missile, Rock Blast, etc."""
        if not attacking_pokemon or not defending_pokemon:
            return 0, 0, f"{attacking_pokemon.name} used {self.name}!", None, None
        
        # Determine number of hits
        hit_count = self._determine_hit_count()
        print(f"DEBUG: {self.name} will hit {hit_count} times")
        
        # Get the move type in lowercase for comparison
        move_type = self.type.lower()
        
        # Get defending Pokémon's types, handling both single and dual types
        if hasattr(defending_pokemon, 'types') and isinstance(defending_pokemon.types, list) and defending_pokemon.types:
            defending_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in defending_pokemon.types]
        else:
            # Fallback for backward compatibility
            defending_types = [getattr(defending_pokemon, 'type', 'normal').lower()]
        
        # Calculate effectiveness against each of the target's types
        effectiveness = 1.0
        effectiveness_breakdown = {}
        
        for target_type in defending_types:
            type_effectiveness = data_loader.get_type_effectiveness(move_type, target_type)
            effectiveness_breakdown[target_type] = type_effectiveness
            effectiveness *= type_effectiveness
        
        effectiveness = round(effectiveness, 2)
        self.effectiveness = effectiveness
        
        # Debug logging
        print(f"DEBUG: {attacking_pokemon.name}'s {self.name} ({move_type}) vs {defending_pokemon.name} ({', '.join(defending_types)}):")
        for t, eff in effectiveness_breakdown.items():
            print(f"  - Against {t}: {eff}x")
        print(f"  Total effectiveness: {effectiveness}x")
        
        if effectiveness == 0:
            return 0, 0, "It had no effect...", None, None
        
        # Determine attack and defense stats based on move category
        if self.category == 'physical':
            attack_stat_name = 'attack'
            defense_stat_name = 'defense'
        else:  # 'special'
            attack_stat_name = 'special_attack'
            defense_stat_name = 'special_defense'
        
        # Calculate damage for each hit, accounting for Substitute
        total_poke_damage = 0
        total_sub_damage = 0
        level = getattr(attacking_pokemon, 'level', 100)
        
        has_substitute = getattr(defending_pokemon, 'substitute_hp', 0) > 0
        bypasses_substitute = self.flags.get('sound') or (hasattr(attacking_pokemon, 'ability') and attacking_pokemon.ability.id == 'infiltrator')
        
        for hit_num in range(1, hit_count + 1):
            # Check accuracy for each hit
            if not self._check_accuracy(attacking_pokemon, defending_pokemon):
                print(f"DEBUG: Hit {hit_num} missed!")
                continue

            is_critical = self._get_critical_hit(defending_pokemon)
            attack_stat = self._get_damage_stat(attacking_pokemon, attack_stat_name, is_critical, 'attacker')
            defense_stat = self._get_damage_stat(defending_pokemon, defense_stat_name, is_critical, 'defender')
            
            # Calculate base damage for this hit
            hit_damage = ((2 * level / 5 + 2) * self.power * attack_stat / defense_stat) / 50 + 2
            hit_damage = int(hit_damage)
            hit_damage = int(hit_damage * effectiveness)
            
            # STAB
            if hasattr(attacking_pokemon, 'types') and attacking_pokemon.types:
                attacker_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in attacking_pokemon.types]
                if move_type in attacker_types:
                    stab_multiplier = attacking_pokemon.ability.get_stab_multiplier() if hasattr(attacking_pokemon, 'ability') else 1.5
                    hit_damage = int(hit_damage * stab_multiplier)
            
            # Critical
            if is_critical:
                hit_damage = int(hit_damage * 1.5)
            
            # Variation
            hit_damage = int(hit_damage * random.randint(85, 100) / 100)
            hit_damage = max(1, int(hit_damage * self._get_burn_multiplier(attacking_pokemon)))

            if hasattr(attacking_pokemon, 'ability'):
                hit_damage = attacking_pokemon.ability.modify_damage_dealt(attacking_pokemon, defending_pokemon, self, hit_damage)
            
            # Apply to substitute if active
            if has_substitute and not bypasses_substitute and defending_pokemon.substitute_hp > 0:
                absorbed = min(hit_damage, defending_pokemon.substitute_hp)
                defending_pokemon.substitute_hp -= absorbed
                total_sub_damage += absorbed
                
                # Check if broken mid-hit
                if defending_pokemon.substitute_hp <= 0:
                    # In Gen 5+, remaining hits strike the Pokemon
                    # But the remainder of THIS hit is usually lost? 
                    # Let's say subsequent hits will strike the poke.
                    pass
            else:
                total_poke_damage += hit_damage
                
        total_damage = total_poke_damage + total_sub_damage
        
        # Generate effectiveness message
        effectiveness_message = ""
        if effectiveness < 1:
            effectiveness_message = "It's not very effective..."
        elif effectiveness > 1:
            effectiveness_message = "It's super effective!"
        
        # Generate hit count message
        hit_message = f"Hit {hit_count} time{'s' if hit_count != 1 else ''}!"
        
        # Combine messages
        combined_message = f"{hit_message} {effectiveness_message}".strip()
        
        # Apply secondary effects, self effects, healing, and recoil
        secondary_messages = []
        self_messages = []
        healing_messages = []
        recoil_messages = []
        
        if defending_pokemon:
            secondary_messages = self._apply_secondary_effects(attacking_pokemon, defending_pokemon)
            
        if attacking_pokemon:
            self_messages = self._apply_self_effects(attacking_pokemon, defending_pokemon)
            healing_messages = self._apply_healing_effects(attacking_pokemon, defending_pokemon, total_damage)
            recoil_messages = self._apply_recoil_effects(attacking_pokemon, total_damage)
        
        # Combine all messages
        all_messages = secondary_messages + self_messages + healing_messages + recoil_messages
        if all_messages:
            combined_message = f"{combined_message} {' '.join(all_messages)}".strip()
        
        return total_poke_damage, total_sub_damage, combined_message, None, None
    
    def get_multihit_hits(self, attacking_pokemon, defending_pokemon) -> List[Dict[str, Any]]:
        """Get individual hit information for multi-hit moves (for progressive damage display)"""
        if not self.is_multihit_move or not attacking_pokemon or not defending_pokemon:
            return []
        
        # Determine number of hits
        hit_count = self._determine_hit_count()
        
        # Get the move type in lowercase for comparison
        move_type = self.type.lower()
        
        # Get defending Pokémon's types
        if hasattr(defending_pokemon, 'types') and isinstance(defending_pokemon.types, list) and defending_pokemon.types:
            defending_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in defending_pokemon.types]
        else:
            defending_types = [getattr(defending_pokemon, 'type', 'normal').lower()]
        
        # Calculate effectiveness
        effectiveness = 1.0
        for target_type in defending_types:
            type_effectiveness = data_loader.get_type_effectiveness(move_type, target_type)
            effectiveness *= type_effectiveness
        effectiveness = round(effectiveness, 2)
        self.effectiveness = effectiveness
        
        if effectiveness == 0:
            return []
        
        # Determine attack and defense stats
        if self.category == 'physical':
            attack_stat_name = 'attack'
            defense_stat_name = 'defense'
        else:
            attack_stat_name = 'special_attack'
            defense_stat_name = 'special_defense'
        
        # Calculate each hit
        hits = []
        level = getattr(attacking_pokemon, 'level', 100)
        
        for hit_num in range(1, hit_count + 1):
            # Check accuracy for each hit
            if not self._check_accuracy(attacking_pokemon, defending_pokemon):
                hits.append({
                    'hit_number': hit_num,
                    'damage': 0,
                    'missed': True,
                    'critical': False
                })
                continue

            is_critical = self._get_critical_hit(defending_pokemon)
            attack_stat = self._get_damage_stat(attacking_pokemon, attack_stat_name, is_critical, 'attacker')
            defense_stat = self._get_damage_stat(defending_pokemon, defense_stat_name, is_critical, 'defender')
            
            # Calculate base damage for this hit
            damage = ((2 * level / 5 + 2) * self.power * attack_stat / defense_stat) / 50 + 2
            damage = int(damage)
            
            # Apply effectiveness
            damage = int(damage * effectiveness)
            
            # Apply STAB
            if hasattr(attacking_pokemon, 'types') and attacking_pokemon.types:
                attacker_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in attacking_pokemon.types]
                if move_type in attacker_types:
                    stab_multiplier = attacking_pokemon.ability.get_stab_multiplier() if hasattr(attacking_pokemon, 'ability') else 1.5
                    damage = int(damage * stab_multiplier)
            
            if is_critical:
                damage = int(damage * 1.5)
            
            # Apply random damage variation
            damage = int(damage * random.randint(85, 100) / 100)
            damage = max(1, int(damage * self._get_burn_multiplier(attacking_pokemon)))
            
            hits.append({
                'hit_number': hit_num,
                'damage': damage,
                'missed': False,
                'critical': is_critical
            })
        
        return hits
            
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'power': self.power,
            'pp': self.pp,
            'max_pp': self.max_pp,
            'type': self.type,
            'accuracy': self.accuracy,
            'category': self.category,
            'priority': self.priority,
            'is_status_move': self.is_status_move,
            'is_healing_move': self.is_healing_move,
            'heal_amount': self.heal_amount,
            'drain_ratio': self.drain_ratio,
            'is_multihit_move': self.is_multihit_move,
            'multihit_data': self.multihit_data,
            'stat_modifications': self.stat_modifications,
            'targets_self': self.targets_self
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Move':
        # Create move using the new data-driven constructor
        move = cls(name=data['name'])
        
        # Override fields that might have been changed/saved
        move.pp = data.get('pp', move.pp)
        move.max_pp = data.get('max_pp', move.max_pp)
        
        # Restore healing data if available
        if 'is_healing_move' in data:
            move.is_healing_move = data['is_healing_move']
        if 'heal_amount' in data:
            move.heal_amount = data['heal_amount']
        if 'drain_ratio' in data:
            move.drain_ratio = data['drain_ratio']
        
        # Restore multi-hit data if available
        if 'is_multihit_move' in data:
            move.is_multihit_move = data['is_multihit_move']
        if 'multihit_data' in data:
            move.multihit_data = data['multihit_data']
        
        # Restore stat modification data if available
        if 'stat_modifications' in data:
            move.stat_modifications = data['stat_modifications']
        if 'targets_self' in data:
            move.targets_self = data['targets_self']
            
        return move
