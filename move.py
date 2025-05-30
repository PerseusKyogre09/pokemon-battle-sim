from data_loader import data_loader

class Move:
    def __init__(self, name, power, pp, move_type='Normal'):
        self.name = name
        self.power = power
        self.pp = pp
        self.max_pp = pp  # Initialize max_pp to the initial pp value
        self.type = move_type

    #pp check and damage calculation with type effectiveness
    def use_move(self, attacking_pokemon=None, defending_pokemon=None):
        base_damage = self.power
        
        # Apply type effectiveness if both Pokemon are provided
        if attacking_pokemon and defending_pokemon:
            effectiveness = data_loader.get_type_effectiveness(self.type, defending_pokemon.type)
            base_damage = int(base_damage * effectiveness)
            
            # Apply STAB (Same Type Attack Bonus)
            if self.type.lower() == attacking_pokemon.type.lower():
                base_damage = int(base_damage * 1.5)
        
        return base_damage
            
    def to_dict(self):
        """Convert the Move object to a dictionary for JSON serialization."""
        return {
            'name': self.name,
            'power': self.power,
            'pp': self.pp,
            'max_pp': self.max_pp,
            'type': self.type
        }
