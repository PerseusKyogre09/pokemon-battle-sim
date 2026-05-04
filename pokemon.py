from move import Move
from data_loader import data_loader
from status_effects import StatusEffect, BurnStatusEffect, ParalysisStatusEffect, FreezeStatusEffect, SleepStatusEffect, PoisonStatusEffect, StatusType
from ability_system import create_ability
from typing import Dict, List, Any
import random

class Pokemon:
    def __init__(self, name, type_, sprite_url, stats, moves=None, level=100, **kwargs):
        self.name = self._format_pokemon_name(name) if isinstance(name, str) else name
        if isinstance(type_, list):
            self.types = [t.lower() for t in type_]
            self.type = self.types[0]
        else:
            self.types = [type_.lower()]
            self.type = type_.lower()
            
        self.sprite_url = sprite_url
        self.sprite = sprite_url
        self.level = level
        
        # Initialize ability
        ability_name = kwargs.get('ability', 'noability')
        self.ability = create_ability(ability_name)
        
        # New: Full competitive stat configuration
        self.evs = kwargs.get('evs', {'hp': 0, 'atk': 0, 'def': 0, 'spa': 0, 'spd': 0, 'spe': 0})
        self.ivs = kwargs.get('ivs', {'hp': 31, 'atk': 31, 'def': 31, 'spa': 31, 'spd': 31, 'spe': 31})
        self.nature = kwargs.get('nature', 'Hardy')
        
        self.status_effects = {}
        self.major_status = None
        self.volatile_statuses = set()
        self.status_change_events = []
        
        self.status_condition = None
        self.status_counter = 0
        self.is_flinched = False
        self.consecutive_stalling_moves = 0
        self.last_move_name = None
        self.substitute_hp = 0
        
        # Base stats from PokeAPI format
        if isinstance(stats, list):
            self.base_stats = {
                'hp': stats[0]['base_stat'] if isinstance(stats[0], dict) else stats[0],
                'attack': stats[1]['base_stat'] if isinstance(stats[1], dict) else stats[1],
                'defense': stats[2]['base_stat'] if isinstance(stats[2], dict) else stats[2],
                'special_attack': stats[3]['base_stat'] if isinstance(stats[3], dict) else stats[3],
                'special_defense': stats[4]['base_stat'] if isinstance(stats[4], dict) else stats[4],
                'speed': stats[5]['base_stat'] if isinstance(stats[5], dict) else stats[5]
            }
        else:
            self.base_stats = stats
        
        self.stat_stages = {
            'attack': 0,
            'defense': 0,
            'special_attack': 0,
            'special_defense': 0,
            'speed': 0,
            'accuracy': 0,
            'evasion': 0
        }
        
        # Initial calculation
        self._recalculate_stats()
        # Set current HP to max HP after first calculation
        self.current_hp = self.max_hp
        
        if moves:
            self.moves = {}
            for move_data in moves:
                move_name = move_data if isinstance(move_data, str) else move_data.get('name')
                if move_name:
                    self.moves[move_name] = Move(move_name)
                    if isinstance(move_data, dict):
                        if 'pp' in move_data:
                            self.moves[move_name].pp = move_data['pp']
                        if 'max_pp' in move_data:
                            self.moves[move_name].max_pp = move_data['max_pp']
        else:
            available_moves = data_loader.get_pokemon_moves(self.name.lower(), 4)
            self.moves = {name: Move(name) for name in available_moves}

    def has_ability(self, ability_name: str) -> bool:
        """Check if the Pokemon has a specific ability."""
        if not self.ability:
            return False
            
        # Standardize both names for comparison
        target = ability_name.lower().replace(" ", "").replace("-", "")
        current = self.ability.name.lower().replace(" ", "").replace("-", "")
        
        return target == current

    def apply_volatile_status(self, status: str) -> str:
        status = status.lower()
        if status == 'flinch':
            self.is_flinched = True
            return f"{self.name} flinched!"
        
        if status not in self.volatile_statuses:
            self.volatile_statuses.add(status)
            return f"{self.name} became {status}!"
        return ""

    def _format_pokemon_name(self, name):
        if not name:
            return name
            
        # Handle special cases (check both original and lowercase)
        name_lower = name.lower()
        special_cases = {
            'ho-oh': 'Ho-Oh',
            'mr-mime': 'Mr. Mime',
            'mime-jr': 'Mime Jr.',
            'nidoran-m': 'Nidoran♂',
            'nidoran-f': 'Nidoran♀',
            'farfetch\'d': 'Farfetch\'d',
            'sirfetch\'d': 'Sirfetch\'d'
        }
        
        if name_lower in special_cases:
            return special_cases[name_lower]
        
        # Handle hyphenated names (capitalize each part)
        if '-' in name:
            parts = name.split('-')
            return '-'.join(part.capitalize() for part in parts)
        
        # Handle apostrophes (like Farfetch'd variants)
        if '\'' in name:
            parts = name.split('\'')
            return '\''.join(part.capitalize() for part in parts)
        
        # Default capitalization - only capitalize if all lowercase or all uppercase
        if name.islower() or name.isupper():
            return name.capitalize()
        else:
            # If it has mixed case, assume it's already properly formatted
            return name

    def take_damage(self, damage):
        old_hp = self.current_hp
        
        # Handle Endure
        if damage >= self.current_hp and 'endure' in self.volatile_statuses:
            self.current_hp = 1
            # Endure message could be added here if needed, but usually handled in game.py
        else:
            self.current_hp = max(0, self.current_hp - damage)
        
        if old_hp > 0 and self.current_hp <= 0:
            self.reset_stats()
        
    def heal(self, amount):
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def get_stat_stage_multiplier(self, stage):
        stage = max(-6, min(6, stage))
        
        if stage >= 0:
            return (2 + stage) / 2
        else:
            return 2 / (2 - stage)

    def _calculate_stat(self, stat_name):
        """Calculate a stat based on base stat, level, IVs, EVs, Nature, and stat stages."""
        base = self.base_stats.get(stat_name, 10)
        level = self.level
        
        # Stat name mapping for EVs/IVs
        mapping = {
            'attack': 'atk',
            'defense': 'def',
            'special_attack': 'spa',
            'special_defense': 'spd',
            'speed': 'spe',
            'hp': 'hp'
        }
        key = mapping.get(stat_name, stat_name)
        iv = self.ivs.get(key, 31)
        ev = self.evs.get(key, 0)
        
        if stat_name == 'hp':
            if self.name.lower() == 'shedinja': return 1
            stat = int(((2 * base + iv + int(ev / 4)) * level) / 100) + level + 10
            self.max_hp = stat
            return stat
            
        # Calculate base value
        stat = int(((2 * base + iv + int(ev / 4)) * level) / 100) + 5
        
        # Apply Nature
        NATURES = {
            'Adamant': {'plus': 'attack', 'minus': 'special_attack'},
            'Bold': {'plus': 'defense', 'minus': 'attack'},
            'Brave': {'plus': 'attack', 'minus': 'speed'},
            'Calm': {'plus': 'special_defense', 'minus': 'attack'},
            'Careful': {'plus': 'special_defense', 'minus': 'special_attack'},
            'Gentle': {'plus': 'special_defense', 'minus': 'defense'},
            'Hasty': {'plus': 'speed', 'minus': 'defense'},
            'Impish': {'plus': 'defense', 'minus': 'special_attack'},
            'Jolly': {'plus': 'speed', 'minus': 'special_attack'},
            'Lax': {'plus': 'defense', 'minus': 'special_defense'},
            'Lonely': {'plus': 'attack', 'minus': 'defense'},
            'Mild': {'plus': 'special_attack', 'minus': 'defense'},
            'Modest': {'plus': 'special_attack', 'minus': 'attack'},
            'Naive': {'plus': 'speed', 'minus': 'special_defense'},
            'Naughty': {'plus': 'attack', 'minus': 'special_defense'},
            'Quiet': {'plus': 'special_attack', 'minus': 'speed'},
            'Rash': {'plus': 'special_attack', 'minus': 'special_defense'},
            'Relaxed': {'plus': 'defense', 'minus': 'speed'},
            'Sassy': {'plus': 'special_defense', 'minus': 'speed'},
            'Timid': {'plus': 'speed', 'minus': 'attack'},
        }
        
        nature_mod = NATURES.get(self.nature, {})
        if nature_mod.get('plus') == stat_name:
            stat = int(stat * 1.1)
        elif nature_mod.get('minus') == stat_name:
            stat = int(stat * 0.9)
            
        # Apply Stat Stages
        stage = self.stat_stages.get(stat_name, 0)
        multiplier = self.get_stat_stage_multiplier(stage)
        stat = int(stat * multiplier)
            
        # Apply Status/Ability Modifications
        stat = self.get_modified_stat_value(stat_name, stat)
            
        return max(1, stat)
    
    def get_modified_stat_value(self, stat_name: str, base_value: int) -> int:
        """Get stat value with status effect and ability modifications applied."""
        modified_value = base_value
        
        for status_effect in self.status_effects.values():
            modified_value = status_effect.modify_stat(self, stat_name, modified_value)
        
        # Apply ability modifications
        if hasattr(self, 'ability'):
            modified_value = self.ability.modify_stat(self, stat_name, modified_value)
            
        return modified_value
        
    def apply_status_effect(self, status_type: str, **kwargs) -> str:
        """Apply a status effect using the new status system with proper validation."""
        if not status_type or not isinstance(status_type, str):
            return ""
        
        status_type = status_type.lower().strip()
        
        # Normalize common abbreviations from dataset
        normalization_map = {
            'par': 'paralysis',
            'psn': 'poison',
            'brn': 'burn',
            'slp': 'sleep',
            'frz': 'freeze',
            'tox': 'toxic'
        }
        status_type = normalization_map.get(status_type, status_type)
        
        status_effect = None
        
        try:
            if status_type == StatusType.BURN.value:
                status_effect = BurnStatusEffect(**kwargs)
            elif status_type == StatusType.PARALYSIS.value:
                status_effect = ParalysisStatusEffect(**kwargs)
            elif status_type == StatusType.FREEZE.value:
                status_effect = FreezeStatusEffect(**kwargs)
            elif status_type == StatusType.SLEEP.value:
                status_effect = SleepStatusEffect(**kwargs)
            elif status_type == StatusType.POISON.value:
                status_effect = PoisonStatusEffect(**kwargs)
            elif status_type == StatusType.TOXIC.value:
                try:
                    from status_effects import ToxicStatusEffect
                    status_effect = ToxicStatusEffect(**kwargs)
                except ImportError:
                    status_effect = StatusEffect(status_type, **kwargs)
            else:
                status_effect = StatusEffect(status_type, **kwargs)
        except Exception as e:
            print(f"ERROR: Failed to create status effect {status_type}: {e}")
            import traceback
            traceback.print_exc()
            return ""
        
        if status_effect:
            try:
                can_apply_before = status_effect.can_apply(self)
                message = status_effect.apply(self)
                
                if can_apply_before and message:
                    self._update_legacy_status()
                    self._recalculate_stats()
                
                return message
            except Exception as e:
                print(f"ERROR: Failed to apply status effect {status_type} to {self.name}: {e}")
                import traceback
                traceback.print_exc()
                return ""
        
        return ""
    

    
    def remove_status_effect(self, status_type: str) -> str:
        """Remove a specific status effect."""
        if status_type in self.status_effects:
            status_effect = self.status_effects[status_type]
            del self.status_effects[status_type]
            
            if self.major_status == status_type:
                self.major_status = None
            
            self._add_status_change_event('status_removed', status_type, status_effect.name)
            
            self._update_legacy_status()
            self._recalculate_stats()
            
            return f"{self.name} recovered from {status_effect.name}!"
        
        return ""
    
    def has_status(self, status_type: str) -> bool:
        """Check if pokemon has a specific status."""
        return status_type in self.status_effects
    
    def get_status_display(self) -> list:
        """Get status information for UI display."""
        status_info = []
        
        for status_type, status_effect in self.status_effects.items():
            info = {
                'type': status_type,
                'name': status_effect.name,
                'is_major': status_effect.is_major,
                'duration': getattr(status_effect, 'duration', -1),
                'counter': getattr(status_effect, 'counter', 0)
            }
            status_info.append(info)
        
        return status_info
    
    def process_turn_start_effects(self) -> list:
        """Process all status effects at turn start."""
        messages = []
        
        for status_effect in list(self.status_effects.values()):
            effect_messages = status_effect.process_turn_start(self)
            messages.extend(effect_messages)
        
        self._update_legacy_status()
        
        return messages
    
    def process_turn_end_effects(self) -> list:
        """Process all status effects at turn end."""
        messages = []
        
        for status_effect in list(self.status_effects.values()):
            effect_messages = status_effect.process_turn_end(self)
            messages.extend(effect_messages)
        
        self._update_legacy_status()
        
        return messages
    
    def can_use_move(self) -> tuple:
        """Check if pokemon can use a move this turn."""
        if getattr(self, 'is_flinched', False):
            return False, f"{self.name} flinched and couldn't move!"
            
        for status_effect in self.status_effects.values():
            prevents_move, message = status_effect.affects_move_usage(self)
            if prevents_move:
                return False, message
        
        return True, ""
    
    def _add_status_change_event(self, event_type: str, status_type: str, status_name: str):
        """Add a status change event to track for this turn."""
        event = {
            'type': event_type,
            'status_type': status_type,
            'status_name': status_name,
            'pokemon_name': self.name
        }
        self.status_change_events.append(event)
    
    def get_status_change_events(self) -> list:
        """Get and clear status change events for this turn."""
        events = self.status_change_events.copy()
        self.status_change_events.clear()
        return events
    
    def _update_legacy_status(self):
        """Update legacy status attributes for backward compatibility."""
        if self.major_status:
            self.status_condition = self.major_status
            if self.major_status in self.status_effects:
                status_effect = self.status_effects[self.major_status]
                if hasattr(status_effect, 'duration') and status_effect.duration > 0:
                    self.status_counter = status_effect.duration
                elif hasattr(status_effect, 'counter'):
                    self.status_counter = status_effect.counter
        else:
            self.status_condition = None
            self.status_counter = 0
        
    def end_turn_status_effects(self):
        """Handle end-of-turn status effects like poison, burn, etc."""
        if hasattr(self, 'status_effects') and self.status_effects:
            messages = self.process_turn_end_effects()
            return " ".join(messages) if messages else ""
        
        if not self.status_condition or self.current_hp <= 0:
            return ""
            
        messages = []
        
        if self.status_condition == 'poison':
            damage = max(1, self.max_hp // 8)
            self.current_hp = max(1, self.current_hp - damage)
            messages.append(f"{self.name} is hurt by poison!")
            
        elif self.status_condition == 'toxic':
            damage = max(1, (self.max_hp // 16) * self.status_counter)
            self.current_hp = max(1, self.current_hp - damage)
            messages.append(f"{self.name} is hurt by poison!")
            self.status_counter += 1
            
        elif self.status_condition == 'burn':
            damage = max(1, self.max_hp // 16)
            self.current_hp = max(1, self.current_hp - damage)
            messages.append(f"{self.name} is hurt by its burn!")
            
        if self.status_condition == 'sleep':
            self.status_counter -= 1
            if self.status_counter <= 0:
                self.status_condition = None
                messages.append(f"{self.name} woke up!")
            else:
                messages.append(f"{self.name} is fast asleep.")
                
        elif self.status_condition == 'freeze':
            if random.random() < 0.2:
                self.status_condition = None
                messages.append(f"{self.name} thawed out!")
                
        return " ".join(messages) if messages else ""
        
    def is_fainted(self):
        return self.current_hp <= 0
    
    def faint(self):
        """Handle Pokemon fainting, including stat stage reset."""
        self.current_hp = 0
        self.reset_stats()
    
    def switch_out(self):
        """Handle Pokemon switching out, including stat stage reset."""
        self.reset_stats()
        
    def can_attack(self):
        """Check if the Pokémon can attack this turn."""
        if hasattr(self, 'status_effects') and self.status_effects:
            return self.can_use_move()
        
        if not hasattr(self, 'status_condition'):
            self.status_condition = None
            
        if self.status_condition == 'paralysis' and random.random() < 0.25:
            return False, f"{self.name} is paralyzed! It can't move!"
        elif self.status_condition == 'freeze':
            return False, f"{self.name} is frozen solid!"
        elif self.status_condition == 'sleep':
            return False, f"{self.name} is fast asleep."
        return True, ""
        
    def generate_stat_modification_message(self, stat_name, requested_change, actual_change):
        """Generate appropriate message for stat stage modifications.
        
        Args:
            stat_name (str): Name of the stat that was modified
            requested_change (int): The change that was requested
            actual_change (int): The actual change that occurred (may be different due to limits)
            
        Returns:
            str: Appropriate message describing the stat modification result
        """
        stat_display = stat_name.replace('_', ' ')
        
        # Handle cases where no change occurred due to limits
        if actual_change == 0:
            if requested_change >= 0:
                return f"{self.name}'s {stat_display} won't go any higher!"
            else:
                return f"{self.name}'s {stat_display} won't go any lower!"
        
        # Generate message based on the magnitude of actual change
        if actual_change > 0:
            if actual_change == 1:
                return f"{self.name}'s {stat_display} rose!"
            elif actual_change == 2:
                return f"{self.name}'s {stat_display} rose sharply!"
            else:  # 3 or more
                return f"{self.name}'s {stat_display} rose drastically!"
        else:  # actual_change < 0
            if actual_change == -1:
                return f"{self.name}'s {stat_display} fell!"
            elif actual_change == -2:
                return f"{self.name}'s {stat_display} fell harshly!"
            else:  # -3 or less
                return f"{self.name}'s {stat_display} fell severely!"

    def modify_stat_stage(self, stat_name, change):
        """Safely apply stat stage changes with validation and limit checking.
        
        Args:
            stat_name (str): Name of the stat to modify ('attack', 'defense', etc.)
            change (int): Amount to change the stat stage by (positive or negative)
            
        Returns:
            str: Message describing the result of the stat modification
        """
        if stat_name not in self.stat_stages:
            return ""
            
        current_stage = self.stat_stages[stat_name]
        new_stage = current_stage + change
        
        clamped_stage = max(-6, min(6, new_stage))
        actual_change = clamped_stage - current_stage
        
        message = self.generate_stat_modification_message(stat_name, change, actual_change)
        
        if actual_change != 0:
            self.stat_stages[stat_name] = clamped_stage
            self._recalculate_stats()
            
            # Trigger Defiant/Competitive if stat was lowered
            if change < 0 and hasattr(self, 'ability'):
                self.ability.on_stat_drop(self, stat_name)
        
        return message
    
    def get_current_stat_stages(self):
        """Return current stat stages for UI display.
        
        Returns:
            dict: Copy of current stat stages dictionary
        """
        return self.stat_stages.copy()

    def reset_stats(self):
        """Reset stat stages and recalculate stats."""
        for stat in self.stat_stages:
            self.stat_stages[stat] = 0
        self._recalculate_stats()
        
    def _recalculate_stats(self):
        """Recalculate all stats based on current stat stages and status."""
        self.attack = self._calculate_stat('attack')
        self.defense = self._calculate_stat('defense')
        self.special_attack = self._calculate_stat('special_attack')
        self.special_defense = self._calculate_stat('special_defense')
        self.speed = self._calculate_stat('speed')
        
    def to_dict(self):
        """Convert the Pokemon object to a dictionary for JSON serialization."""
        return {
            'name': self.name,
            'type': self.type,
            'types': self.types,
            'sprite_url': self.sprite_url,
            'sprite': self.sprite_url,  # Keep both for backward compatibility
            'level': self.level,
            'current_hp': self.current_hp,
            'max_hp': self.max_hp,
            'attack': self.attack,
            'defense': self.defense,
            'special_attack': self.special_attack,
            'special_defense': self.special_defense,
            'speed': self.speed,
            'ability': {
                'name': self.ability.name,
                'description': self.ability.description,
                'id': self.ability.id
            },
            'moves': {name: move.to_dict() for name, move in self.moves.items()},
            'status_effects': self.get_status_display(),
            'major_status': self.major_status,
            'status_condition': self.status_condition,  # For backward compatibility
            'stat_stages': self.get_current_stat_stages(),
            'substitute_hp': self.substitute_hp
        }

    def on_switch_in(self, opponent) -> List[Dict[str, Any]]:
        """Trigger ability effects when entering battle."""
        if hasattr(self, 'ability'):
            return self.ability.on_switch_in(self, opponent)
        return []

    def on_faint(self, opponent) -> List[Dict[str, Any]]:
        """Trigger ability effects when fainted."""
        if hasattr(self, 'ability'):
            return self.ability.on_faint(self, opponent)
        return []

    def on_turn_end(self, opponent) -> List[Dict[str, Any]]:
        """Trigger ability effects at turn end."""
        if hasattr(self, 'ability'):
            return self.ability.on_turn_end(self, opponent)
        return []

    def on_victory(self, opponent) -> List[Dict[str, Any]]:
        """Trigger ability effects when this Pokemon defeats an opponent."""
        if hasattr(self, 'ability') and hasattr(self.ability, 'on_source_after_faint'):
            return self.ability.on_source_after_faint(self, opponent)
        return []

    def on_any_faint(self) -> List[Dict[str, Any]]:
        """Trigger ability effects when any Pokemon faints."""
        if hasattr(self, 'ability') and hasattr(self.ability, 'on_any_faint'):
            return self.ability.on_any_faint(self)
        return []

    def get_best_stat(self, ignore_boosts=True, ignore_modifiers=True) -> str:
        """Returns the name of the highest stat (excluding HP)."""
        stats_to_check = ['attack', 'defense', 'special_attack', 'special_defense', 'speed']
        best_val = -1
        best_stat = 'attack'
        
        for stat_name in stats_to_check:
            # For Beast Boost, it typically uses the value BEFORE in-battle boosts?
            # Actually Showdown says source.getBestStat(true, true) ignores boosts and modifiers.
            val = self.base_stats.get(stat_name, 0)
            
            # If we were to use current values:
            if not ignore_boosts:
                val = getattr(self, stat_name, val)
                
            if val > best_val:
                best_val = val
                best_stat = stat_name
            elif val == best_val:
                # Tie-breaker order in Showdown: atk, def, spa, spd, spe
                pass 
                
        # Map to internal names if needed
        mapping = {
            'attack': 'atk',
            'defense': 'def',
            'special_attack': 'spa',
            'special_defense': 'spd',
            'speed': 'spe'
        }
        return mapping.get(best_stat, best_stat)
