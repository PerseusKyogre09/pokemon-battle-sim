from data_loader import data_loader
from typing import Optional, Tuple, Dict, Any

class Move:
    def __init__(self, name: str, power: int, pp: int, move_type: str = 'Normal'):
        self.name = name
        self.power = power
        self.pp = pp
        self.max_pp = pp
        self.type = move_type

    def use_move(self, attacking_pokemon=None, defending_pokemon=None) -> Tuple[int, str]:
        """
        Use the move and calculate its damage and effectiveness.
        
        Args:
            attacking_pokemon: The Pokémon using the move
            defending_pokemon: The Pokémon being targeted
            
        Returns:
            tuple: (damage: int, effectiveness_message: str)
        """
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
            
            # Apply effectiveness to damage
            base_damage = int(base_damage * effectiveness)
            
            if effectiveness == 0:
                effectiveness_message = "It had no effect..."
            elif effectiveness < 1:
                effectiveness_message = "It's not very effective..."
            elif effectiveness > 1:
                effectiveness_message = "It's super effective!"
            
                # Apply STAB
            if hasattr(attacking_pokemon, 'types') and attacking_pokemon.types:
                attacker_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in attacking_pokemon.types]
                if move_type in attacker_types:
                    base_damage = int(base_damage * 1.5)
                    print(f"DEBUG: STAB applied for {attacking_pokemon.name}'s {self.name}")
            
            # Check for critical hit (6.25% chance)
            import random
            is_critical = random.randint(1, 16) == 1
            
            if is_critical:
                base_damage = int(base_damage * 1.5)
                print(f"DEBUG: Critical hit! {attacking_pokemon.name}'s {self.name} did 1.5x damage!")
                if effectiveness_message:
                    effectiveness_message = "A critical hit! " + effectiveness_message
                else:
                    effectiveness_message = "A critical hit!"
        
        # Apply random damage variation (85% to 100% of calculated damage)
        if base_damage > 0:
            damage_multiplier = random.uniform(0.85, 1.0)
            base_damage = max(1, int(base_damage * damage_multiplier))
            print(f"DEBUG: Damage roll: {damage_multiplier*100:.1f}% of max damage")
        
        return base_damage, effectiveness_message
            
    def to_dict(self):
        """Convert the Move object to a dictionary for JSON serialization."""
        return {
            'name': self.name,
            'power': self.power,
            'pp': self.pp,
            'max_pp': self.max_pp,
            'type': self.type
        }
