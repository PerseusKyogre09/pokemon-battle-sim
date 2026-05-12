from typing import Dict, List, Any, Optional, Tuple
import json
import os
import re

LOGIC_PATH = os.path.join(os.path.dirname(__file__), "../../data/datasets/items_logic.json")

def load_items_config():
    config = {}
    if os.path.exists(LOGIC_PATH):
        with open(LOGIC_PATH, 'r') as f:
            config = json.load(f)
    return config

ITEMS_CONFIG = load_items_config()

class Item:
    def __init__(self, name: str):
        self.id = name.lower().replace(" ", "").replace("-", "").replace("'", "").replace("(", "").replace(")", "")
        self.config = ITEMS_CONFIG.get(self.id, {})
        self.name = self.config.get("name", name)
        self.description = self.config.get("desc", "No effect.")
        
        # State for specific items (e.g. choice lock)
        self.state = {}
        
    def _parse_chain_modify(self, logic_str: str) -> float:
        if not logic_str or "chainModify" not in logic_str:
            return 1.0
        match = re.search(r'chainModify\(\[?([\d., ]+)\]?\)', logic_str)
        if match:
            parts = [p.strip() for p in match.group(1).split(',')]
            if len(parts) >= 2:
                try: return float(parts[0]) / float(parts[1])
                except: return 1.0
            else:
                try: return float(parts[0])
                except: return 1.0
        return 1.0

    def modify_damage_dealt(self, pokemon, opponent, move, damage: int) -> int:
        final_damage = damage
        
        # Choice Band / Specs / Scarf are stat modifiers, not final damage modifiers.
        if self.id == 'lifeorb':
            final_damage = int(final_damage * 1.3)
        elif self.id == 'expertbelt' and getattr(move, 'effectiveness', 1.0) > 1:
            final_damage = int(final_damage * 1.2)
        elif self.id == 'muscleband' and move.category == 'physical':
            final_damage = int(final_damage * 1.1)
        elif self.id == 'wiseglasses' and move.category == 'special':
            final_damage = int(final_damage * 1.1)
            
        # Parse onBasePower from logic
        logic = self.config.get("onBasePower")
        if logic:
            # Simple check for multiplier
            multiplier = self._parse_chain_modify(logic)
            if multiplier != 1.0:
                # Check for type-specific boosts (e.g. Charcoal)
                type_match = re.search(r"move\.type === '([^']+)'", logic)
                if type_match:
                    if move.type.lower() == type_match.group(1).lower():
                        final_damage = int(final_damage * multiplier)
                else:
                    final_damage = int(final_damage * multiplier)
                    
        return final_damage

    def modify_damage_taken(self, pokemon, opponent, move, damage: int) -> int:
        final_damage = damage
        
        # Berries (Simplified)
        if 'berry' in self.id:
            # We'll handle berry consumption in a separate method
            pass
            
        # Assault Vest
        if self.id == 'assaultvest' and move.category == 'special':
            # This should be handled in stats calculation, but can be here too
            pass

        # Parse onSourceModifyDamage
        logic = self.config.get("onSourceModifyDamage")
        if logic:
            multiplier = self._parse_chain_modify(logic)
            if multiplier != 1.0:
                # Check for super-effective reduction (Solid Rock pattern)
                if "typeMod > 0" in logic and getattr(move, 'effectiveness', 1.0) > 1:
                    final_damage = int(final_damage * multiplier)
                else:
                    final_damage = int(final_damage * multiplier)

        return final_damage

    def on_residual(self, pokemon) -> List[Dict[str, Any]]:
        results = []
        is_p = hasattr(pokemon, "is_player") and pokemon.is_player
        
        # Leftovers / Black Sludge
        if self.id == 'leftovers' and pokemon.current_hp > 0:
            heal_amt = pokemon.max_hp // 16
            if pokemon.current_hp < pokemon.max_hp:
                pokemon.heal(heal_amt)
                results.append({
                    "type": "item",
                    "item_name": self.name,
                    "pokemon_name": pokemon.name,
                    "message": f"{pokemon.name} restored a little HP using its {self.name}!",
                    "is_player": is_p
                })
        elif self.id == 'blacksludge' and pokemon.current_hp > 0:
            if 'poison' in pokemon.types:
                heal_amt = pokemon.max_hp // 16
                if pokemon.current_hp < pokemon.max_hp:
                    pokemon.heal(heal_amt)
                    results.append({"type": "item", "item_name": self.name, "pokemon_name": pokemon.name, "message": f"{pokemon.name} restored a little HP using its {self.name}!", "is_player": is_p})
            else:
                damage = pokemon.max_hp // 8
                pokemon.take_damage(damage)
                results.append({"type": "item", "item_name": self.name, "pokemon_name": pokemon.name, "message": f"{pokemon.name} was hurt by its {self.name}!", "is_player": is_p})
        
        # Flame Orb / Toxic Orb
        elif self.id == 'flameorb' and not pokemon.major_status:
            msg = pokemon.apply_status_effect('brn')
            if msg: results.append({"type": "item", "item_name": self.name, "pokemon_name": pokemon.name, "message": f"{pokemon.name}'s {self.name} burned it!", "is_player": is_p})
        elif self.id == 'toxicorb' and not pokemon.major_status:
            msg = pokemon.apply_status_effect('tox')
            if msg: results.append({"type": "item", "item_name": self.name, "pokemon_name": pokemon.name, "message": f"{pokemon.name}'s {self.name} badly poisoned it!", "is_player": is_p})
            
        return results

    def on_after_move(self, pokemon, move_result) -> List[Dict[str, Any]]:
        results = []
        is_p = hasattr(pokemon, "is_player") and pokemon.is_player
        
        # Life Orb recoil
        if self.id == 'lifeorb' and move_result.get('damage_dealt', 0) > 0:
            recoil = pokemon.max_hp // 10
            pokemon.take_damage(recoil)
            results.append({
                "type": "item",
                "item_name": self.name,
                "pokemon_name": pokemon.name,
                "message": f"{pokemon.name} was hurt by its Life Orb!",
                "is_player": is_p
            })
            
        return results

    def on_damage(self, pokemon, damage: int) -> List[Dict[str, Any]]:
        results = []
        is_p = hasattr(pokemon, "is_player") and pokemon.is_player
        
        # Focus Sash
        if self.id == 'focussash' and pokemon.current_hp == 0 and (pokemon.current_hp + damage == pokemon.max_hp):
            pokemon.current_hp = 1
            results.append({
                "type": "item",
                "item_name": self.name,
                "pokemon_name": pokemon.name,
                "message": f"{pokemon.name} hung on using its Focus Sash!",
                "is_player": is_p
            })
            pokemon.item = None # Consume it
            pokemon.item_obj = None
            
        # Berries (Healing) - Must be alive to eat a berry
        elif self.id == 'sitrusberry' and 0 < pokemon.current_hp <= pokemon.max_hp // 2:
            pokemon.heal(pokemon.max_hp // 4)
            results.append({"type": "item", "item_name": self.name, "pokemon_name": pokemon.name, "message": f"{pokemon.name} ate its {self.name} and restored HP!", "is_player": is_p})
            pokemon.item = None
            pokemon.item_obj = None
            
        return results

    def modify_stat(self, pokemon, stat_name: str, val: int) -> int:
        if self.id == 'choiceband' and stat_name == 'attack':
            return int(val * 1.5)
        if self.id == 'choicespecs' and stat_name == 'special_attack':
            return int(val * 1.5)
        if self.id == 'choicescarf' and stat_name == 'speed':
            return int(val * 1.5)
        if self.id == 'assaultvest' and stat_name == 'special_defense':
            return int(val * 1.5)
        if self.id == 'eviolite' and (stat_name == 'defense' or stat_name == 'special_defense'):
            # Simplified check for evolution
            return int(val * 1.5)
            
        return val

def create_item(name: str) -> Optional[Item]:
    if not name:
        return None
    return Item(name)
