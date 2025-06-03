from data_loader import data_loader
from typing import Optional, Tuple, Dict, Any, Union, List
import random

class Move:
    def __init__(self, name: str, power: int, pp: int, move_type: str = 'normal', 
                 accuracy: Union[int, bool] = 100, category: str = 'physical',
                 status_effect: Optional[Dict[str, Any]] = None):
        """
        Initialize a Move.
        
        Args:
            name: Name of the move
            power: Base power of the move (0 for status moves)
            pp: Current PP of the move
            move_type: Type of the move (e.g., 'fire', 'water')
            accuracy: Accuracy of the move (0-100 or True for never-miss moves)
            category: Move category ('physical', 'special', or 'status')
            status_effect: Optional dictionary containing status effect information
        """
        self.name = name
        self.power = power
        self.pp = pp
        self.max_pp = pp
        self.type = move_type.lower()
        self.accuracy = accuracy
        self.category = category.lower()
        self.status_effect = status_effect
        self.is_status_move = category.lower() == 'status' or power == 0

    def _check_accuracy(self) -> bool:
        """
        Check if the move hits based on its accuracy.
        
        Returns:
            bool: True if the move hits, False otherwise
        """
        if self.accuracy is True:  # Moves that never miss (e.g., Aerial Ace)
            return True
            
        if isinstance(self.accuracy, (int, float)):
            return random.randint(1, 100) <= self.accuracy
            
        return True  # Default to True if accuracy is somehow invalid

    def _apply_status_effect(self, target, status_effect: Dict[str, Any]) -> str:
        """
        Apply status effect to the target Pokémon.
        
        Args:
            target: The Pokémon to apply the status effect to
            status_effect: Dictionary containing status effect information
            
        Returns:
            str: Message describing the status effect application
        """
        if not hasattr(target, 'apply_status_effect'):
            return ""
            
        # Check if the status effect applies based on chance
        if random.randint(1, 100) > status_effect.get('chance', 100):
            return ""
            
        status_type = status_effect['type'].lower()
        return target.apply_status_effect(status_type)

    def use_move(self, attacking_pokemon=None, defending_pokemon=None) -> Tuple[int, str, Optional[str]]:
        """
        Use the move and calculate its damage and effectiveness.
        
        Args:
            attacking_pokemon: The Pokémon using the move
            defending_pokemon: The Pokémon being targeted
            
        Returns:
            tuple: (damage: int, effectiveness_message: str, status_message: Optional[str])
        """
        # Check if the move hits
        if not self._check_accuracy():
            return 0, f"{attacking_pokemon.name}'s {self.name} missed!", None
        
        # Handle status moves separately - they deal no damage
        if self.is_status_move:
            status_message = ""
            if self.status_effect and defending_pokemon:
                status_message = self._apply_status_effect(defending_pokemon, self.status_effect)
            return 0, f"{attacking_pokemon.name} used {self.name}!", status_message
        
        base_damage = self.power
        effectiveness_message = ""
        
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
        
        # Apply status effect if the move has one
        status_message = None
        if self.status_effect and defending_pokemon:
            status_message = self._apply_status_effect(defending_pokemon, self.status_effect)
        
        return base_damage, effectiveness_message, status_message
            
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Move object to a dictionary for JSON serialization.
        
        Returns:
            dict: A dictionary containing all move data
        """
        return {
            'name': self.name,
            'power': self.power,
            'pp': self.pp,
            'max_pp': self.max_pp,
            'type': self.type,
            'accuracy': self.accuracy,
            'category': self.category,
            'status_effect': self.status_effect,
            'is_status_move': self.is_status_move
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Move':
        """Create a Move instance from a dictionary."""
        return cls(
            name=data['name'],
            power=data['power'],
            pp=data['pp'],
            move_type=data['type'],
            accuracy=data.get('accuracy', 100),
            category=data.get('category', 'physical'),
            status_effect=data.get('status_effect')
        )
