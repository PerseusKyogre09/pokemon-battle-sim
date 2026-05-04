from typing import Dict, List, Any, Optional
import json
import os
import re

LOGIC_PATH = os.path.join(os.path.dirname(__file__), "datasets/abilities_logic.json")
METADATA_PATH = os.path.join(os.path.dirname(__file__), "datasets/abilities.json")

def load_abilities_config():
    config = {}
    
    if os.path.exists(LOGIC_PATH):
        with open(LOGIC_PATH, 'r') as f:
            config = json.load(f)
            
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            metadata = json.load(f)
            for id, data in metadata.items():
                if id in config:
                    config[id]["desc"] = data.get("desc", config[id].get("desc", ""))
                    config[id]["shortDesc"] = data.get("shortDesc", config[id].get("shortDesc", ""))
                else:
                    config[id] = {
                        "id": id,
                        "name": data.get("name", id),
                        "desc": data.get("desc", ""),
                        "shortDesc": data.get("shortDesc", "")
                    }
    
    if "levitate" in config:
        config["levitate"]["immunities"] = {"types": ["ground"]}
        
    return config

ABILITIES_CONFIG = load_abilities_config()

class Ability:
    def __init__(self, name: str):
        self.id = name.lower().replace(" ", "").replace("-", "")
        self.config = ABILITIES_CONFIG.get(self.id, {})
        self.name = self.config.get("name", name)
        self.description = self.config.get("desc", "No effect.")
        
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
            
        # Pattern: pokemon.hp <= pokemon.maxhp / 3
        if "hp <= pokemon.maxhp / 3" in logic_str or "hp <= attacker.maxhp / 3" in logic_str:
            if pokemon.current_hp <= pokemon.max_hp / 3:
                return True
            return False
            
        if "hp <= pokemon.maxhp / 2" in logic_str:
            if pokemon.current_hp <= pokemon.max_hp / 2:
                return True
            return False

        # Pattern: pokemon.status
        if "pokemon.status" in logic_str or "attacker.status" in logic_str:
            if pokemon.major_status:
                return True
            return False
            
        # Pattern: move.type === 'Fire'
        match = re.search(r"move\.type === '([^']+)'", logic_str)
        if match:
            target_type = match.group(1).lower()
            if move and move.type.lower() == target_type:
                return True
            return False

        # Pattern: this.field.isTerrain('electricterrain')
        match = re.search(r"isTerrain\('([^']+)'\)", logic_str)
        if match:
            target_terrain = match.group(1).lower()
            # Simple check for now - would need terrain system in game.py
            return False # Fallback until terrain is implemented
            
        # Handle basePowerAfterMultiplier <= 60 or move.power <= 60
        if "power <= 60" in logic_str or "basePowerAfterMultiplier <= 60" in logic_str:
            if move and 0 < move.power <= 60:
                return True
            return False
        
        # Generic power check
        match = re.search(r"power <= (\d+)", logic_str)
        if match:
            threshold = int(match.group(1))
            if move and 0 < move.power <= threshold:
                return True
            return False

        # 6. Specific moves
        match = re.search(r"move\.id === '([^']+)'", logic_str)
        if match:
            target_move = match.group(1).lower()
            if move and move.name.lower().replace(" ", "").replace("-", "") == target_move:
                return True
            return False

        # If no obvious condition, assume it applies
        return True

    def modify_stat(self, pokemon, stat_name: str, value: int) -> int:
        """Applies stat multipliers based on the ability."""
        # 1. Check direct config (legacy/simple)
        condition = self.config.get("condition")
        if condition == "has_status":
            if not pokemon.major_status:
                return value
        
        stat_modifiers = self.config.get("stat_modifiers", {})
        multiplier = stat_modifiers.get(stat_name, 1.0)
        
        if multiplier != 1.0:
            value = int(value * multiplier)
            
        # 2. Check dynamic logic from JSON
        stat_map = {
            'attack': 'onModifyAtk',
            'defense': 'onModifyDef',
            'special_attack': 'onModifySpA',
            'special_defense': 'onModifySpD',
            'speed': 'onModifySpe'
        }
        
        hook = stat_map.get(stat_name)
        if hook and hook in self.config:
            logic = self.config[hook]
            if self._check_condition(logic, pokemon, None):
                multiplier = self._parse_chain_modify(logic)
                value = int(value * multiplier)
        
        # 3. Hardcoded special cases - Only for things that cannot be parsed
        # Guts Attack boost is handled by generic onModifyAtk in JSON
        # Huge Power is handled by generic onModifyAtk in JSON
        
        return value

    def _parse_boost_amounts(self, logic_str: str) -> Dict[str, int]:
        """Extract boost amounts from ability logic strings."""
        boosts = {}
        
        if not logic_str:
            return boosts
        
        # Pattern: this.boost({ atk: 2, spa: 1 }, target, ...)
        match = re.search(r"this\.boost\(\{\s*([^}]+)\s*\}", logic_str)
        if match:
            boost_str = match.group(1)
            # Extract individual stats: atk: 1, def: -1, etc.
            stat_pairs = re.findall(r"(\w+):\s*(-?\d+)", boost_str)
            for stat_abbr, value in stat_pairs:
                stat_name = self._abbr_to_stat_name(stat_abbr)
                if stat_name:
                    boosts[stat_name] = int(value)
        
        return boosts
    
    def _abbr_to_stat_name(self, abbr: str) -> Optional[str]:
        """Convert stat abbreviations to full names."""
        abbr_map = {
            'hp': 'hp',
            'atk': 'attack',
            'def': 'defense',
            'spa': 'special_attack',
            'spd': 'special_defense',
            'spe': 'speed'
        }
        return abbr_map.get(abbr.lower())

    def on_switch_in(self, pokemon, opponent) -> List[Dict[str, Any]]:
        results = []
        is_p = hasattr(pokemon, "is_player") and pokemon.is_player
        
        # Priority handlers for common switch-in mechanics
        MECHANICS = {
            "intimidate": ("attack", -1, "{user}'s Intimidate cuts {target}'s attack!"),
            "download": None, # Complex logic below
            "unnerve": ("unnerve", 0, "{user}'s Unnerve prevents {target} from using berries!"),
            "drizzle": ("weather", 0, "{user}'s Drizzle made it rain!"),
            "drought": ("weather", 0, "{user}'s Drought made the sunlight harsh!"),
            "sandstream": ("weather", 0, "{user}'s Sand Stream whipped up a sandstorm!"),
            "snowwarning": ("weather", 0, "{user}'s Snow Warning whipped up a hailstorm!"),
            "pressure": ("pressure", 0, "{user}'s Pressure is bearing down on {target}!"),
            "electricsurge": ("terrain", 0, "{user}'s Electric Surge set the Electric Terrain!"),
            "grassysurge": ("terrain", 0, "{user}'s Grassy Surge set the Grassy Terrain!"),
            "mistsurge": ("terrain", 0, "{user}'s Misty Surge set the Misty Terrain!"),
            "psychicsurge": ("terrain", 0, "{user}'s Psychic Surge set the Psychic Terrain!")
        }
        
        if self.id in MECHANICS:
            if self.id == "download":
                if hasattr(opponent, "defense") and hasattr(opponent, "special_defense"):
                    stat = "attack" if opponent.defense < opponent.special_defense else "special_attack"
                    msg = pokemon.modify_stat_stage(stat, 1)
                    if msg: results.append({"type": "ability", "ability_name": self.name, "pokemon_name": pokemon.name, "message": f"{pokemon.name}'s Download boosted its {stat.replace('_', ' ').title()}!", "is_player": is_p})
            else:
                stat, stages, template = MECHANICS[self.id]
                msg = template.format(user=pokemon.name, target=opponent.name)
                if stages != 0 and hasattr(opponent, "modify_stat_stage"):
                    res_msg = opponent.modify_stat_stage(stat, stages)
                    if res_msg: msg = res_msg
                results.append({"type": "ability", "ability_name": self.name, "pokemon_name": pokemon.name, "message": msg, "is_player": is_p})

        # Process dynamic hooks (onStart, onSwitchIn)
        for hook in ["onStart", "onSwitchIn"]:
            logic = self.config.get(hook)
            if not logic: continue
            
            # Weather/Terrain
            if "setWeather" in logic or "setTerrain" in logic:
                results.append({"type": "ability", "ability_name": self.name, "pokemon_name": pokemon.name, "message": f"{pokemon.name}'s {self.name} changed the field!", "is_player": is_p})
            
            # Boosts
            boosts = self._parse_boost_amounts(logic)
            if boosts:
                target = opponent if "target" in logic else pokemon
                for s_name, stages in boosts.items():
                    if hasattr(target, "modify_stat_stage"):
                        msg = target.modify_stat_stage(s_name, stages)
                        if msg: results.append({"type": "ability", "ability_name": self.name, "pokemon_name": pokemon.name, "message": msg if isinstance(msg, str) else f"{pokemon.name}'s {self.name} activated!", "is_player": is_p})

        # Process effect list
        for effect in self.config.get("on_switch_in", []):
            target = opponent if effect.get("target") == "opponent" else pokemon
            if effect.get("action") == "boost":
                for s_name, stages in effect.get("stats", {}).items():
                    if hasattr(target, "modify_stat_stage"):
                        msg = target.modify_stat_stage(s_name, stages)
                        if msg:
                            f_msg = effect.get("message", msg).format(user=pokemon.name, target=target.name)
                            results.append({"type": "ability", "ability_name": self.name, "pokemon_name": pokemon.name, "message": f_msg, "is_player": is_p})
        
        return results

    def on_turn_end(self, pokemon, opponent) -> List[Dict[str, Any]]:
        """Trigger end-of-turn effects (e.g. Speed Boost)."""
        results = []
        
        # Common turn-end abilities
        if self.id == "speedboost":
            msg = pokemon.modify_stat_stage("speed", 1)
            if msg:
                results.append({
                    "type": "ability",
                    "ability_name": self.name,
                    "pokemon_name": pokemon.name,
                    "message": f"{pokemon.name}'s Speed Boost increased its Speed!",
                    "is_player": hasattr(pokemon, "is_player") and pokemon.is_player
                })
        elif self.id == "losteye":
            msg = pokemon.modify_stat_stage("accuracy", -1)
            if msg:
                results.append({
                    "type": "ability",
                    "ability_name": self.name,
                    "pokemon_name": pokemon.name,
                    "message": f"{pokemon.name}'s Lost Eye lowered its Accuracy!",
                    "is_player": hasattr(pokemon, "is_player") and pokemon.is_player
                })
        elif self.id == "powerspotboost":
            msg = pokemon.modify_stat_stage("special_attack", 1)
            if msg:
                results.append({
                    "type": "ability",
                    "ability_name": self.name,
                    "pokemon_name": pokemon.name,
                    "message": f"{pokemon.name}'s ability boosted its Special Attack!",
                    "is_player": hasattr(pokemon, "is_player") and pokemon.is_player
                })
        elif self.id == "contrariness":
            # Flips stat changes
            msg = pokemon.modify_stat_stage("attack", 1)  # Placeholder - actual logic would flip boosts
            if msg:
                results.append({
                    "type": "ability",
                    "ability_name": self.name,
                    "pokemon_name": pokemon.name,
                    "message": f"{pokemon.name}'s Contrariness flipped the stat changes!",
                    "is_player": hasattr(pokemon, "is_player") and pokemon.is_player
                })
        
        # Parse onResidual for passive damage/healing
        residual_logic = self.config.get("onResidual")
        if residual_logic:
            if "damage" in residual_logic.lower():
                results.append({
                    "type": "ability",
                    "ability_name": self.name,
                    "pokemon_name": pokemon.name,
                    "message": f"{pokemon.name}'s {self.name} activated!",
                    "is_player": hasattr(pokemon, "is_player") and pokemon.is_player
                })
        
        return results

    def on_faint(self, pokemon, opponent) -> List[Dict[str, Any]]:
        """Trigger effects when the Pokemon faints (e.g. Aftermath)."""
        results = []
        if self.id == "aftermath":
            damage = opponent.max_hp // 4
            opponent.current_hp = max(0, opponent.current_hp - damage)
            results.append({
                "type": "ability",
                "ability_name": self.name,
                "pokemon_name": pokemon.name,
                "message": f"{pokemon.name}'s Aftermath hurt {opponent.name}!",
                "is_player": hasattr(pokemon, "is_player") and pokemon.is_player
            })
        return results

    def on_source_after_faint(self, pokemon, opponent) -> List[Dict[str, Any]]:
        """Trigger effects when this Pokemon faints an opponent (e.g. Moxie)."""
        results = []
        
        # Generic parsing for boost patterns in onSourceAfterFaint hook
        logic = self.config.get("onSourceAfterFaint")
        if logic:
            # Check for bestStat call (Beast Boost)
            if "getBestStat" in logic:
                if hasattr(pokemon, "get_best_stat"):
                    best_stat_abbr = pokemon.get_best_stat(True, True)
                    # Convert to full name for modify_stat_stage
                    stat_map = {'atk': 'attack', 'def': 'defense', 'spa': 'special_attack', 'spd': 'special_defense', 'spe': 'speed'}
                    stat_name = stat_map.get(best_stat_abbr, best_stat_abbr)
                    
                    if hasattr(pokemon, "modify_stat_stage"):
                        msg = pokemon.modify_stat_stage(stat_name, 1)
                        if msg:
                            results.append({
                                "type": "ability",
                                "ability_name": self.name,
                                "pokemon_name": pokemon.name,
                                "message": f"{pokemon.name}'s {self.name} boosted its {stat_name}!",
                                "is_player": hasattr(pokemon, "is_player") and pokemon.is_player
                            })
                return results

            boosts = self._parse_boost_amounts(logic)
            if boosts:
                for stat_name, stages in boosts.items():
                    # In onSourceAfterFaint, 'length' is usually used for boost amount (usually 1)
                    # We'll use the parsed value or default to 1
                    amount = stages if stages != 0 else 1
                    if hasattr(pokemon, "modify_stat_stage"):
                        msg = pokemon.modify_stat_stage(stat_name, amount)
                        if msg:
                            results.append({
                                "type": "ability",
                                "ability_name": self.name,
                                "pokemon_name": pokemon.name,
                                "message": f"{pokemon.name}'s {self.name} boosted its {stat_name}!",
                                "is_player": hasattr(pokemon, "is_player") and pokemon.is_player
                            })
                            
        return results

    def on_any_faint(self, pokemon) -> List[Dict[str, Any]]:
        """Trigger effects when any Pokemon faints (e.g. Soul-Heart)."""
        results = []
        
        logic = self.config.get("onAnyFaint")
        if logic:
            boosts = self._parse_boost_amounts(logic)
            if boosts:
                for stat_name, stages in boosts.items():
                    if hasattr(pokemon, "modify_stat_stage"):
                        msg = pokemon.modify_stat_stage(stat_name, stages)
                        if msg:
                            results.append({
                                "type": "ability",
                                "ability_name": self.name,
                                "pokemon_name": pokemon.name,
                                "message": f"{pokemon.name}'s {self.name} boosted its {stat_name}!",
                                "is_player": hasattr(pokemon, "is_player") and pokemon.is_player
                            })
                            
        return results

    def on_stat_drop(self, pokemon, stat_name: str) -> List[Dict[str, Any]]:
        """Trigger effects when a stat is lowered (e.g. Defiant)."""
        results = []
        
        if self.id == "defiant":
            # Defiant: +2 Atk when any stat is lowered
            if hasattr(pokemon, "modify_stat_stage"):
                pokemon.modify_stat_stage("attack", 2)
        elif self.id == "competitive":
            # Competitive: +2 SpA when any stat is lowered
            if hasattr(pokemon, "modify_stat_stage"):
                pokemon.modify_stat_stage("special_attack", 2)
                
        return results

    def modify_damage_taken(self, pokemon, opponent, move, damage: int) -> int:
        """Modifies damage taken by the Pokemon."""
        final_damage = damage
        
        # Abilities that reduce damage
        if self.id == "filter" or self.id == "solidrock":
            # Reduces super-effective damage to 1/4x (6/8 = 0.75)
            if hasattr(move, 'effectiveness'):
                if move.effectiveness > 1:
                    final_damage = int(final_damage * 0.75)
        elif self.id == "thickfat":
            # Reduces Fire and Ice type moves by 50%
            if hasattr(move, 'type') and move.type.lower() in ['fire', 'ice']:
                final_damage = int(final_damage * 0.5)
        elif self.id == "waterabsorb" or self.id == "dryskin":
            # Heals from Water type moves instead of taking damage
            if hasattr(move, 'type') and move.type.lower() == 'water':
                return 0
        elif self.id == "flashfire":
            # Absorbs Fire type moves
            if hasattr(move, 'type') and move.type.lower() == 'fire':
                return 0
        elif self.id == "voltabsorb":
            # Absorbs Electric type moves
            if hasattr(move, 'type') and move.type.lower() == 'electric':
                return 0
        elif self.id == "sapsipper":
            # Absorbs Grass type moves
            if hasattr(move, 'type') and move.type.lower() == 'grass':
                return 0
        elif self.id == "furcoat":
            # Halves physical damage
            if hasattr(move, 'category') and move.category == 'physical':
                final_damage = int(final_damage * 0.5)
        elif self.id == "marvelscale":
            # Reduces all damage to 50% when having status
            if pokemon.major_status:
                final_damage = int(final_damage * 0.5)
        elif self.id == "unaware":
            # Ignores opponent stat boosts (reduce damage)
            final_damage = int(final_damage * 0.8)  # Simplified
        elif self.id == "regenerator":
            # Heals 1/3 HP per turn (handled elsewhere)
            pass
        
        # Generic damage reduction from onDamage hooks
        on_damage = self.config.get("onDamage")
        if on_damage:
            if "damage * 0.5" in on_damage or "chainModify(0.5)" in on_damage:
                final_damage = int(final_damage * 0.5)
            elif "damage * 0.75" in on_damage or "chainModify(0.75)" in on_damage:
                final_damage = int(final_damage * 0.75)
        
        return final_damage

    def modify_damage_dealt(self, pokemon, opponent, move, damage: int) -> int:
        """Modifies damage dealt by the Pokemon."""
        final_damage = damage
        
        # Hardcoded abilities with damage modifiers
        if self.id == "technician":
            # 1.5x damage for moves with 60 or less base power
            if hasattr(move, 'power') and 0 < move.power <= 60:
                final_damage = int(final_damage * 1.5)
        elif self.id == "adaptability":
            # 2.25x STAB instead of 1.5x (handled in STAB calculation)
            pass
        elif self.id == "sheerforce":
            # 1.3125x (1.3x boost) for moves with secondary effects
            if hasattr(move, 'secondary') and move.secondary:
                final_damage = int(final_damage * 1.3125)
        elif self.id == "hugepower" or self.id == "purplepower":
            # Doubles attack (handled in modify_stat)
            pass
        elif self.id == "ironbarbs":
            # Reflects 1/8 damage back (handled separately)
            pass
        elif self.id == "roughskin":
            # Reflects 1/8 damage back (handled separately)
            pass
        elif self.id == "effectspore":
            # 30% chance to cause status on contact (handled separately)
            pass
        elif self.id == "sandstream":
            # Weakens water moves (handled with weather)
            pass
        elif self.id == "swordofruin":
            # Reduces opponent Special Defense (handled separately)
            final_damage = int(final_damage * 0.8)  # Simplified
        elif self.id == "beadsofruin":
            # Reduces opponent Special Defense (handled separately)
            final_damage = int(final_damage * 0.8)  # Simplified
        elif self.id == "tabletsofruin":
            # Reduces opponent Special Defense (handled separately)
            final_damage = int(final_damage * 0.8)  # Simplified
        elif self.id == "vesselofruin":
            # Reduces opponent Special Defense (handled separately)
            final_damage = int(final_damage * 0.8)  # Simplified
        
        # 1. Check direct modifiers list (legacy/simple)
        modifiers = self.config.get("damage_modifiers", [])
        for mod in modifiers:
            condition = mod.get("condition")
            multiplier = mod.get("multiplier", 1.0)
            
            if condition == "hp_threshold":
                threshold = mod.get("threshold", 0.33)
                required_type = mod.get("move_type")
                if pokemon.current_hp / pokemon.max_hp <= threshold:
                    if not required_type or move.type.lower() == required_type.lower():
                        final_damage = int(final_damage * multiplier)
            elif condition == "base_power_below":
                threshold = mod.get("threshold", 60)
                if move.power <= threshold and move.power > 0:
                    final_damage = int(final_damage * multiplier)
                    
        # 2. Check raw logic for multipliers (Technician, Aerilate, etc.)
        for hook in ["onBasePower", "onModifyAtk", "onModifySpA"]:
            # Only apply Atk/SpA hooks if they match the move category
            if hook == "onModifyAtk" and move.category != 'physical':
                continue
            if hook == "onModifySpA" and move.category != 'special':
                continue
                
            logic = self.config.get(hook)
            if not logic: continue
            
            if self._check_condition(logic, pokemon, opponent, move):
                multiplier = self._parse_chain_modify(logic)
                final_damage = int(final_damage * multiplier)
                            
        return final_damage

    def is_immune(self, move_type: str, move_category: str) -> bool:
        """Checks if the ability provides immunity to a certain move type/category."""
        immunities = self.config.get("immunities", {})
        
        # 1. Check direct immunities (e.g. Levitate)
        if move_type.lower() in [t.lower() for t in immunities.get("types", [])]:
            return True
        
        # 2. Hardcoded type immunities
        type_immunities = {
            'levitate': ['ground'],
            'waterabsorb': ['water'],
            'voltabsorb': ['electric'],
            'dryskin': ['water'],
            'flashfire': ['fire'],
            'sapsipper': ['grass'],
            'lightningrod': ['electric'],
            'motordrive': ['electric'],
            'magnetpull': [],  # No immunity, just attracts steel
            'static': [],  # No immunity, just chance to paralyze
            'immunity': ['poison'],
            'comatose': [],  # No type immunity, just sleep immunity
            'waterveil': ['fire'],
            'heatproof': ['fire'],
            'thickfat': ['fire', 'ice'],
            'wonderguard': [],  # Only takes super-effective damage
            'goodasgold': ['item-based'],
        }
        
        if self.id in type_immunities:
            if move_type.lower() in type_immunities[self.id]:
                return True
            
        # 3. Check raw logic for immunity (onTryHit)
        on_try_hit = self.config.get("onTryHit")
        if on_try_hit:
            # Check if this move type is mentioned as being blocked
            if f"move.type === '{move_type.capitalize()}'" in on_try_hit or f"move.type === '{move_type.lower()}'" in on_try_hit:
                if "return null" in on_try_hit or "return false" in on_try_hit:
                    return True

        return False

    def get_type_change(self, move) -> Optional[str]:
        """Returns the type a move is changed to by this ability (e.g. Aerilate)."""
        type_changes = {
            'aerilate': 'flying',
            'pixilate': 'fairy',
            'refrigerate': 'ice',
            'iondeluge': 'electric',
            'normalize': 'normal',
        }
        
        if self.id in type_changes and hasattr(move, 'type') and move.type.lower() == 'normal':
            return type_changes[self.id]
        
        return None

    def get_weather_boost(self, move_type: str, weather: Optional[str]) -> float:
        """Returns damage multiplier based on weather and this ability."""
        if not weather:
            return 1.0
        
        weather_boosts = {
            'drizzle': {'water': 1.5, 'fire': 0.5},
            'drought': {'fire': 1.5, 'water': 0.5},
            'sandstream': {'rock': 1.5, 'steel': 1.5, 'ground': 1.5, 'fire': 0.5},
            'snowwarning': {'ice': 1.5, 'fire': 0.5},
            'hail': {'ice': 1.5},
        }
        
        if weather in weather_boosts:
            return weather_boosts[weather].get(move_type.lower(), 1.0)
        
        return 1.0

    def get_stab_multiplier(self) -> float:
        """Returns the STAB multiplier (usually 1.5, Adaptability makes it 2.0)."""
        # 1. Check direct config
        if "on_modify_stab" in self.config:
            return self.config["on_modify_stab"]
        
        # Hardcoded STAB multipliers
        stab_multipliers = {
            'adaptability': 2.25,  # 2.25x instead of 1.5x
        }
        
        if self.id in stab_multipliers:
            return stab_multipliers[self.id]
            
        # 2. Check raw logic for Adaptability pattern
        on_modify_stab = self.config.get("onModifySTAB")
        if on_modify_stab:
            if "return 2.25" in on_modify_stab: return 2.25
            if "return 2" in on_modify_stab: return 2.0
            
        return 1.5

    def get_secondary_multiplier(self) -> float:
        """Returns the multiplier for secondary effect chances."""
        # 1. Check direct config
        if "secondary_multiplier" in self.config:
            return self.config["secondary_multiplier"]
        
        # Hardcoded secondary multipliers
        secondary_multipliers = {
            'serenegrace': 2.0,  # 2x secondary chance
            'sheerforce': 1.3,  # 1.3x damage but removes secondary effects
        }
        
        if self.id in secondary_multipliers:
            return secondary_multipliers[self.id]
            
        # 2. Check raw logic for Serene Grace pattern
        on_modify_move = self.config.get("onModifyMove")
        if on_modify_move:
            if "* 2" in on_modify_move or "*= 2" in on_modify_move: return 2.0
            if "* 3" in on_modify_move or "*= 3" in on_modify_move: return 3.0
            
        return 1.0

    def get_accuracy_modifier(self) -> float:
        """Returns the accuracy multiplier for moves used by this ability."""
        accuracy_modifiers = {
            'compoundeyes': 1.3,  # 1.3x accuracy
            'victorystar': 1.1,  # 1.1x accuracy
            'keeneye': 1.0,  # Prevents accuracy lowering
        }
        
        if self.id in accuracy_modifiers:
            return accuracy_modifiers[self.id]
        
        return 1.0

    def get_ability_summary(self) -> Dict[str, Any]:
        """Returns a summary of what this ability does."""
        summary = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rating': self.config.get('rating', 0),
        }
        
        # Determine ability category
        hooks = list(self.config.keys())
        
        if any(h in hooks for h in ['onStart', 'onSwitchIn', 'drizzle', 'drought']):
            summary['type'] = 'Stat/Weather Setter'
        elif any(h in hooks for h in ['onBasePower', 'onModifyAtk', 'onModifySpA']):
            summary['type'] = 'Damage Modifier'
        elif any(h in hooks for h in ['onDamage', 'onTryHit']):
            summary['type'] = 'Defensive'
        elif any(h in hooks for h in ['onResidual']):
            summary['type'] = 'End-of-turn'
        elif any(h in hooks for h in ['onTryBoost']):
            summary['type'] = 'Stat Protection'
        else:
            summary['type'] = 'Special Effect'
        
        return summary

def create_ability(name: str) -> Ability:
    """Helper to create an ability instance."""
    if not name:
        return Ability("noability")
    return Ability(name)
