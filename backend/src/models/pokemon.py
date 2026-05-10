from .move import Move
from ..utils.data_loader import data_loader
from ..systems.status_effects import StatusEffect, BurnStatusEffect, ParalysisStatusEffect, FreezeStatusEffect, SleepStatusEffect, PoisonStatusEffect, StatusType
from ..systems.ability_system import create_ability
from ..systems.item_system import create_item
from typing import Dict, List, Any
import random

class Pokemon:
    def __init__(self, name, type_, sprite_url, stats, moves=None, level=100, **kwargs):
        self.name = self._format_pokemon_name(name) if isinstance(name, str) else name
        self.types = [t.lower() for t in type_] if isinstance(type_, list) else [type_.lower()]
        self.type = self.types[0]
        self.sprite_url = sprite_url
        self.level = level
        self.ability = create_ability(kwargs.get('ability', 'noability'))
        
        self.evs = kwargs.get('evs', {s: 0 for s in ['hp', 'atk', 'def', 'spa', 'spd', 'spe']})
        self.ivs = kwargs.get('ivs', {s: 31 for s in ['hp', 'atk', 'def', 'spa', 'spd', 'spe']})
        self.nature = kwargs.get('nature', 'Hardy')
        self.item = kwargs.get('item', '')
        self.item_obj = create_item(self.item)
        
        self.status_effects = {}
        self.major_status = None
        self.volatile_statuses = set()
        self.status_change_events = []
        self.is_flinched = False
        self.substitute_hp = 0
        self.consecutive_stalling_moves = 0
        
        if isinstance(stats, list):
            keys = ['hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed']
            self.base_stats = {k: (s['base_stat'] if isinstance(s, dict) else s) for k, s in zip(keys, stats)}
        else:
            self.base_stats = stats
        
        self.stat_stages = {s: 0 for s in ['attack', 'defense', 'special_attack', 'special_defense', 'speed', 'accuracy', 'evasion']}
        self._recalculate_stats()
        self.current_hp = self.max_hp
        
        if moves:
            self.moves = {}
            for move_data in moves:
                m_name = move_data if isinstance(move_data, str) else move_data.get('name')
                if m_name:
                    self.moves[m_name] = Move(m_name)
                    if isinstance(move_data, dict):
                        self.moves[m_name].pp = move_data.get('pp', self.moves[m_name].pp)
                        self.moves[m_name].max_pp = move_data.get('max_pp', self.moves[m_name].max_pp)
        else:
            self.moves = {n: Move(n) for n in data_loader.get_pokemon_moves(self.name.lower(), 4)}

    def has_ability(self, ability_name: str) -> bool:
        if not self.ability: return False
        clean = lambda s: s.lower().replace(" ", "").replace("-", "")
        return clean(ability_name) == clean(self.ability.name)

    def on_switch_in(self, opponent) -> List[Dict[str, Any]]:
        if hasattr(self, 'ability'):
            return self.ability.on_switch_in(self, opponent)
        return []

    def on_damage(self, damage: int) -> List[Dict[str, Any]]:
        if hasattr(self, 'ability'):
            return self.ability.on_damage(self, damage)
        return []

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
        if not name: return name
        nl = name.lower()
        special = {'ho-oh': 'Ho-Oh', 'mr-mime': 'Mr. Mime', 'mime-jr': 'Mime Jr.', 
                   'nidoran-m': 'Nidoran♂', 'nidoran-f': 'Nidoran♀', 
                   'farfetch\'d': 'Farfetch\'d', 'sirfetch\'d': 'Sirfetch\'d'}
        if nl in special: return special[nl]
        if '-' in name: return '-'.join(p.capitalize() for p in name.split('-'))
        if '\'' in name: return '\''.join(p.capitalize() for p in name.split('\''))
        return name.capitalize() if name.islower() or name.isupper() else name

    def is_fainted(self):
        return self.current_hp <= 0

    def take_damage(self, damage, from_move=False):
        if damage >= self.current_hp:
            if 'endure' in self.volatile_statuses:
                self.current_hp = 1
            elif from_move and self.current_hp == self.max_hp and hasattr(self, 'ability') and self.ability.id == 'sturdy':
                self.current_hp = 1
            else:
                self.current_hp = 0
        else:
            self.current_hp -= damage
            
        if self.current_hp <= 0: self.reset_stats()
        
    def heal(self, amount):
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    @property
    def is_at_full_hp(self):
        return self.current_hp >= self.max_hp

    def get_stat_stage_multiplier(self, stage):
        stage = max(-6, min(6, stage))
        return (2 + stage) / 2 if stage >= 0 else 2 / (2 - stage)

    def _calculate_stat(self, stat_name):
        base, level = self.base_stats.get(stat_name, 10), self.level
        mapping = {'attack': 'atk', 'defense': 'def', 'special_attack': 'spa', 'special_defense': 'spd', 'speed': 'spe', 'hp': 'hp'}
        key = mapping.get(stat_name, stat_name)
        iv, ev = self.ivs.get(key, 31), self.evs.get(key, 0)
        
        if stat_name == 'hp':
            if self.name.lower() == 'shedinja': return 1
            stat = int(((2 * base + iv + int(ev / 4)) * level) / 100) + level + 10
            self.max_hp = stat
            return stat
            
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
        plus, minus = natures.get(self.nature, (None, None))
        if plus == stat_name: stat = int(stat * 1.1)
        elif minus == stat_name: stat = int(stat * 0.9)
            
        stat = int(stat * self.get_stat_stage_multiplier(self.stat_stages.get(stat_name, 0)))
        return max(1, self.get_modified_stat_value(stat_name, stat))
    
    def get_modified_stat_value(self, stat_name: str, base_value: int) -> int:
        val = base_value
        for effect in self.status_effects.values():
            val = effect.modify_stat(self, stat_name, val)
        if hasattr(self, 'ability'):
            val = self.ability.modify_stat(self, stat_name, val)
        if self.item_obj:
            val = self.item_obj.modify_stat(self, stat_name, val)
        return val
        
    def apply_status_effect(self, status_type: str, **kwargs) -> str:
        if not status_type: return ""
        st = status_type.lower().strip()
        norm = {'par': 'paralysis', 'psn': 'poison', 'brn': 'burn', 'slp': 'sleep', 'frz': 'freeze', 'tox': 'toxic'}
        st = norm.get(st, st)
        
        try:
            if st == StatusType.BURN.value: eff = BurnStatusEffect(**kwargs)
            elif st == StatusType.PARALYSIS.value: eff = ParalysisStatusEffect(**kwargs)
            elif st == StatusType.FREEZE.value: eff = FreezeStatusEffect(**kwargs)
            elif st == StatusType.SLEEP.value: eff = SleepStatusEffect(**kwargs)
            elif st == StatusType.POISON.value: eff = PoisonStatusEffect(**kwargs)
            elif st == StatusType.TOXIC.value:
                try:
                    from ..systems.status_effects import ToxicStatusEffect
                    eff = ToxicStatusEffect(**kwargs)
                except ImportError: eff = StatusEffect(st, **kwargs)
            else: eff = StatusEffect(st, **kwargs)
            
            can_apply = eff.can_apply(self)
            msg = eff.apply(self)
            if can_apply and msg:
                self._update_legacy_status()
                self._recalculate_stats()
            return msg
        except Exception as e:
            print(f"Error applying status {st}: {e}")
            return ""
    
    def remove_status_effect(self, status_type: str) -> str:
        if status_type in self.status_effects:
            eff = self.status_effects.pop(status_type)
            if self.major_status == status_type: self.major_status = None
            self._add_status_change_event('status_removed', status_type, eff.name)
            self._update_legacy_status()
            self._recalculate_stats()
            return f"{self.name} recovered from {eff.name}!"
        return ""
    
    def has_status(self, status_type: str) -> bool:
        return status_type in self.status_effects
    
    def get_status_display(self) -> list:
        return [{'type': t, 'name': e.name, 'is_major': e.is_major, 
                 'duration': getattr(e, 'duration', -1), 'counter': getattr(e, 'counter', 0)} 
                for t, e in self.status_effects.items()]
    
    def process_turn_start_effects(self) -> list:
        if self.current_hp <= 0: return []
        msgs = []
        for e in list(self.status_effects.values()):
            msgs.extend(e.process_turn_start(self))
        self._update_legacy_status()
        return msgs
    
    def process_turn_end_effects(self) -> list:
        if self.current_hp <= 0: return []
        msgs = []
        for e in list(self.status_effects.values()):
            msgs.extend(e.process_turn_end(self))
        self._update_legacy_status()
        return msgs
    
    def can_use_move(self) -> tuple:
        if getattr(self, 'is_flinched', False):
            return False, f"{self.name} flinched!"
        for e in self.status_effects.values():
            prevents, msg = e.affects_move_usage(self)
            if prevents: return False, msg
        
        # Check ability constraints (e.g. Truant)
        if hasattr(self, 'ability') and hasattr(self.ability, 'can_use_move'):
            can_use, msg = self.ability.can_use_move(self)
            if not can_use: return False, msg
            
        return True, ""
    
    def _add_status_change_event(self, etype, stype, sname):
        self.status_change_events.append({'type': etype, 'status_type': stype, 'status_name': sname, 'pokemon_name': self.name})
    
    def get_status_change_events(self) -> list:
        events = self.status_change_events.copy()
        self.status_change_events.clear()
        return events
    
    def _update_legacy_status(self):
        if self.major_status:
            self.status_condition = self.major_status
            eff = self.status_effects.get(self.major_status)
            self.status_counter = getattr(eff, 'duration', getattr(eff, 'counter', 0)) if eff else 0
        else:
            self.status_condition, self.status_counter = None, 0
        
    def end_turn_status_effects(self):
        if self.status_effects: return " ".join(self.process_turn_end_effects())
        return ""
        
    def is_fainted(self): return self.current_hp <= 0
    def faint(self): self.current_hp = 0; self.reset_stats()
    def switch_out(self): self.reset_stats()
        
    def can_attack(self):
        if self.status_effects: return self.can_use_move()
        return True, ""
        
    def generate_stat_modification_message(self, stat_name, requested, actual):
        display = stat_name.replace('_', ' ')
        if actual == 0:
            return f"{self.name}'s {display} won't go {'higher' if requested >= 0 else 'lower'}!"
        
        if actual > 0:
            suffixes = {1: "rose!", 2: "rose sharply!", 3: "rose drastically!"}
            return f"{self.name}'s {display} {suffixes.get(actual, 'rose drastically!')}"
        else:
            suffixes = {-1: "fell!", -2: "fell harshly!", -3: "fell severely!"}
            return f"{self.name}'s {display} {suffixes.get(actual, 'fell severely!')}"

    def modify_stat_stage(self, stat_name, change):
        if stat_name not in self.stat_stages: return ""
        curr = self.stat_stages[stat_name]
        clamped = max(-6, min(6, curr + change))
        actual = clamped - curr
        
        msg = self.generate_stat_modification_message(stat_name, change, actual)
        if actual != 0:
            self.stat_stages[stat_name] = clamped
            self._recalculate_stats()
            if change < 0 and hasattr(self, 'ability'):
                self.ability.on_stat_drop(self, stat_name)
        return msg
    
    def get_current_stat_stages(self): return self.stat_stages.copy()
    def reset_stats(self):
        for s in self.stat_stages: self.stat_stages[s] = 0
        self._recalculate_stats()
        
    def _recalculate_stats(self):
        self.max_hp = self._calculate_stat('hp')
        self.attack = self._calculate_stat('attack')
        self.defense = self._calculate_stat('defense')
        self.special_attack = self._calculate_stat('special_attack')
        self.special_defense = self._calculate_stat('special_defense')
        self.speed = self._calculate_stat('speed')
        
    def to_dict(self):
        return {
            'name': self.name, 'type': self.type, 'types': self.types,
            'sprite': self.sprite_url, 'level': self.level,
            'current_hp': self.current_hp, 'max_hp': self.max_hp,
            'attack': self.attack, 'defense': self.defense,
            'special_attack': self.special_attack, 'special_defense': self.special_defense,
            'speed': self.speed,
            'ability': {'name': self.ability.name, 'description': self.ability.description, 'id': self.ability.id},
            'item': self.item,
            'moves': {n: m.to_dict() for n, m in self.moves.items()},
            'status_effects': self.get_status_display(),
            'stat_stages': self.stat_stages, 'substitute_hp': self.substitute_hp
        }

    def on_switch_in(self, opponent): return self.ability.on_switch_in(self, opponent) if hasattr(self, 'ability') else []
    def on_faint(self, opponent): return self.ability.on_faint(self, opponent) if hasattr(self, 'ability') else []
    def on_turn_end(self, opponent): return self.ability.on_turn_end(self, opponent) if hasattr(self, 'ability') else []
    def on_victory(self, opponent): return self.ability.on_source_after_faint(self, opponent) if hasattr(self, 'ability') and hasattr(self.ability, 'on_source_after_faint') else []
    def on_any_faint(self): return self.ability.on_any_faint(self) if hasattr(self, 'ability') and hasattr(self.ability, 'on_any_faint') else []

    def get_best_stat(self, ignore_boosts=True, ignore_modifiers=True) -> str:
        stats = ['attack', 'defense', 'special_attack', 'special_defense', 'speed']
        best_v, best_s = -1, 'attack'
        for s in stats:
            v = self.base_stats.get(s, 0) if ignore_boosts else getattr(self, s, 0)
            if v > best_v: best_v, best_s = v, s
        return {'attack': 'atk', 'defense': 'def', 'special_attack': 'spa', 'special_defense': 'spd', 'speed': 'spe'}.get(best_s, best_s)

