from data_loader import data_loader
from typing import Optional, Tuple, Dict, Any, Union, List
import random

class Move:
    def __init__(self, name: str, power: int, pp: int, move_type: str = 'normal', 
                 accuracy: Union[int, bool] = 100, category: str = 'physical',
                 status_effect: Optional[Dict[str, Any]] = None):
        self.name = name
        self.power = power
        self.pp = pp
        self.max_pp = pp
        self.type = move_type.lower()
        self.accuracy = accuracy
        self.category = category.lower()
        self.is_status_move = category.lower() == 'status' or power == 0
        
        # Parse status effects from move data if not provided
        if status_effect is None:
            self.primary_status, self.secondary_status, self.status_chance = self._parse_move_data()
        else:
            # Use provided status effect (for backward compatibility)
            self.primary_status = status_effect if self.is_status_move else None
            self.secondary_status = status_effect if not self.is_status_move else None
            self.status_chance = status_effect.get('chance', 100) if status_effect else 0
        
        # Keep old status_effect for backward compatibility
        self.status_effect = status_effect

    def _parse_move_data(self) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], int]:
        # Get move data from the dataset
        move_data = data_loader.get_move(self.name)
        if not move_data:
            return None, None, 0
        
        primary_status = None
        secondary_status = None
        status_chance = 0
        
        # Check if data_loader already parsed status_effect
        if 'status_effect' in move_data and move_data['status_effect']:
            status_info = move_data['status_effect']
            status_type = self._normalize_status_type(status_info.get('type', ''))
            if status_type:
                # Determine if this is primary (status move) or secondary (damaging move)
                if self.is_status_move:
                    primary_status = {
                        'type': status_type,
                        'chance': status_info.get('chance', 100)
                    }
                else:
                    secondary_status = {
                        'type': status_type,
                        'chance': status_info.get('chance', 100)
                    }
                status_chance = status_info.get('chance', 100)
        
        return primary_status, secondary_status, status_chance
    
    def _normalize_status_type(self, status_code: str) -> Optional[str]:
        if not status_code:
            return None
            
        # Map dataset status codes to standard status names
        status_mapping = {
            'par': 'paralysis',
            'paralyze': 'paralysis',
            'paralyzed': 'paralysis',
            'brn': 'burn',
            'burn': 'burn',
            'frz': 'freeze',
            'freeze': 'freeze',
            'frozen': 'freeze',
            'psn': 'poison',
            'poison': 'poison',
            'tox': 'toxic',
            'toxic': 'toxic',
            'slp': 'sleep',
            'sleep': 'sleep',
            'asleep': 'sleep'
        }
        
        return status_mapping.get(status_code.lower())

    def _check_accuracy(self) -> bool:
        if self.accuracy is True:  # Moves that never miss (e.g., Aerial Ace)
            return True
            
        if isinstance(self.accuracy, (int, float)):
            return random.randint(1, 100) <= self.accuracy
            
        return True  # Default to True if accuracy is somehow invalid

    def _apply_status_effects(self, user, target) -> List[str]:
        messages = []
        
        # Apply primary status effect (for status moves)
        if self.primary_status:
            message = self._apply_single_status_effect(target, self.primary_status)
            if message:
                messages.append(message)
        
        # Apply secondary status effect (for damaging moves with status chance)
        if self.secondary_status:
            message = self._apply_single_status_effect(target, self.secondary_status)
            if message:
                messages.append(message)
        
        return messages
    
    def _apply_single_status_effect(self, target, status_effect: Dict[str, Any]) -> str:
        if not status_effect:
            return ""
        
        # Validate status effect data
        if not isinstance(status_effect, dict):
            return ""
        
        # Check if target has apply_status_effect method
        if not hasattr(target, 'apply_status_effect') or not callable(getattr(target, 'apply_status_effect', None)):
            return ""
        
        # Check if the status effect applies based on chance
        chance = status_effect.get('chance', 100)
        if not isinstance(chance, (int, float)) or chance < 0 or chance > 100:
            chance = 100
        
        if random.randint(1, 100) > chance:
            return ""
        
        status_type = status_effect.get('type', '')
        if not status_type or not isinstance(status_type, str):
            return ""
        
        # Map abbreviated status types to full names
        status_type_mapping = {
            'par': 'paralysis',
            'brn': 'burn',
            'frz': 'freeze',
            'slp': 'sleep',
            'psn': 'poison',
            'tox': 'toxic'
        }
        
        # Convert abbreviated status type to full name if needed
        status_type = status_type_mapping.get(status_type.lower(), status_type.lower())
        
        # Apply the status effect using the new status system
        try:
            return target.apply_status_effect(status_type)
        except Exception as e:
            print(f"ERROR: Failed to apply status effect {status_type} to {getattr(target, 'name', 'unknown')}: {e}")
            return ""

    def use_move(self, attacking_pokemon=None, defending_pokemon=None) -> Tuple[int, str, Optional[str]]:
        # Debug log for move usage
        debug_msg = f"{attacking_pokemon.name}'s {self.name} (power: {self.power}, category: {self.category}, type: {self.type})"
        if defending_pokemon:
            debug_msg += f" vs {defending_pokemon.name} ({', '.join(defending_pokemon.types) if hasattr(defending_pokemon, 'types') else 'unknown'})"
        print(f"DEBUG: {debug_msg}")
        
        # Validate that the Pokemon can actually use moves (safety check)
        if attacking_pokemon and hasattr(attacking_pokemon, 'can_use_move'):
            can_move, reason = attacking_pokemon.can_use_move()
            if not can_move:
                print(f"WARNING: Move {self.name} called on {attacking_pokemon.name} who cannot move: {reason}")
                # Still continue with the move for backward compatibility, but log the issue
        
        # Check if the move hits
        if not self._check_accuracy():
            return 0, f"{attacking_pokemon.name}'s {self.name} missed!", None
        
        # Handle status moves and 0-power moves - they deal no damage
        if self.is_status_move or self.power == 0:
            status_messages = []
            if defending_pokemon:
                status_messages = self._apply_status_effects(attacking_pokemon, defending_pokemon)
            
            # Combine status messages into a single string
            status_message = " ".join(status_messages) if status_messages else None
            return 0, f"{attacking_pokemon.name} used {self.name}!", status_message
        
        # If we get here, it's a damaging move
        base_damage = self.power
        effectiveness_message = ""
        
        # If it's a status move, it shouldn't have any damage calculation
        if self.is_status_move or self.power == 0:
            return 0, f"{attacking_pokemon.name} used {self.name}!", ""
        
        # Apply type effectiveness if both Pokemon are provided
        if attacking_pokemon and defending_pokemon:
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
            
            # Debug logging
            print(f"DEBUG: {attacking_pokemon.name}'s {self.name} ({move_type}) vs {defending_pokemon.name} ({', '.join(defending_types)}):")
            for t, eff in effectiveness_breakdown.items():
                print(f"  - Against {t}: {eff}x")
            print(f"  Total effectiveness: {effectiveness}x")
            
            # Determine attack and defense stats based on move category
            if self.category == 'physical':
                attack_stat = getattr(attacking_pokemon, 'attack', 1)
                defense_stat = getattr(defending_pokemon, 'defense', 1)
                attack_name = 'Attack'
                defense_name = 'Defense'
            else:  # 'special' or 'status' (though status moves are handled earlier)
                attack_stat = getattr(attacking_pokemon, 'spa', 1)  # Special Attack
                defense_stat = getattr(defending_pokemon, 'spd', 1)  # Special Defense
                attack_name = 'Special Attack'
                defense_name = 'Special Defense'
            
            # Base damage formula: (((2 * Level / 5 + 2) * Power * A/D) / 50 + 2) * Modifiers
            # Where A is the attacker's Attack/Sp. Atk and D is the defender's Defense/Sp. Def
            # Using level 100 for standard competitive play
            level = 100
            
            # Calculate base damage
            # At level 100, the formula simplifies to: (Power * A * 42 / D / 50 + 2) * Modifiers
            damage = ((2 * level / 5 + 2) * base_damage * attack_stat / defense_stat) / 50 + 2
            damage = int(damage)
            
            # Apply effectiveness
            damage = int(damage * effectiveness)
            
            if effectiveness == 0:
                effectiveness_message = "It had no effect..."
                return 0, effectiveness_message, None
            elif effectiveness < 1:
                effectiveness_message = "It's not very effective..."
            elif effectiveness > 1:
                effectiveness_message = "It's super effective!"
            
            # Apply STAB (Same Type Attack Bonus) - 1.5x if move type matches any of user's types
            if hasattr(attacking_pokemon, 'types') and attacking_pokemon.types:
                attacker_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in attacking_pokemon.types]
                if move_type in attacker_types:
                    damage = int(damage * 1.5)
                    print(f"DEBUG: STAB applied for {attacking_pokemon.name}'s {self.name}")
            
            # Check for critical hit (6.25% chance by default)
            crit_chance = 1/16  # Default crit chance
            is_critical = random.random() < crit_chance
            
            if is_critical:
                damage = int(damage * 1.5)
                print(f"DEBUG: Critical hit! {attacking_pokemon.name}'s {self.name} did 1.5x damage!")
                if effectiveness_message:
                    effectiveness_message = "A critical hit! " + effectiveness_message
                else:
                    effectiveness_message = "A critical hit!"
            
            # Apply random damage variation (85% to 100% of calculated damage)
            damage_multiplier = random.uniform(0.85, 1.0)
            damage = max(1, int(damage * damage_multiplier))
            print(f"DEBUG: Damage roll: {damage_multiplier*100:.1f}% of max damage")
            print(f"DEBUG: {attack_name}: {attack_stat}, {defense_name}: {defense_stat}, Base Power: {base_damage}, Final Damage: {damage}")
            
            base_damage = damage  # Update base_damage with the calculated damage
        
        # Apply status effects after damage calculation
        status_messages = []
        if defending_pokemon:
            status_messages = self._apply_status_effects(attacking_pokemon, defending_pokemon)
        
        # Combine status messages into a single string
        status_message = " ".join(status_messages) if status_messages else None
        
        return base_damage, effectiveness_message, status_message
            
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'power': self.power,
            'pp': self.pp,
            'max_pp': self.max_pp,
            'type': self.type,
            'accuracy': self.accuracy,
            'category': self.category,
            'status_effect': self.status_effect,  # Keep for backward compatibility
            'primary_status': self.primary_status,
            'secondary_status': self.secondary_status,
            'status_chance': self.status_chance,
            'is_status_move': self.is_status_move
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Move':
        move = cls(
            name=data['name'],
            power=data['power'],
            pp=data['pp'],
            move_type=data['type'],
            accuracy=data.get('accuracy', 100),
            category=data.get('category', 'physical'),
            status_effect=data.get('status_effect')
        )
        
        # Restore parsed status data if available
        if 'primary_status' in data:
            move.primary_status = data['primary_status']
        if 'secondary_status' in data:
            move.secondary_status = data['secondary_status']
        if 'status_chance' in data:
            move.status_chance = data['status_chance']
            
        return move
