from move import Move
from data_loader import data_loader

class Pokemon:
    def __init__(self, name, type_, sprite_url, stats, moves=None, level=100):
        self.name = name
        # Handle both single type (string) and multiple types (list)
        if isinstance(type_, list):
            self.types = [t.lower() for t in type_]
            self.type = self.types[0]  # For backward compatibility
        else:
            self.types = [type_.lower()]
            self.type = type_.lower()  # For backward compatibility
            
        self.sprite_url = sprite_url
        self.sprite = sprite_url  # Add sprite alias for backward compatibility
        self.level = level
        
        # Initialize status condition attributes first
        self.status_condition = None
        self.status_counter = 0
        self.volatile_status = set()
        
        # Store base stats for status effect calculations
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
            # Handle case where stats is already a dict
            self.base_stats = stats
        
        # Calculate and store actual stats
        self.max_hp = int(((self.base_stats['hp'] * 2) * self.level / 100) + self.level + 10)
        self.current_hp = self.max_hp
        
        # Store actual stats with stat stages (default to 0 = no change)
        self.stat_stages = {
            'attack': 0,
            'defense': 0,
            'special_attack': 0,
            'special_defense': 0,
            'speed': 0,
            'accuracy': 0,
            'evasion': 0
        }
        
        # Calculate base stats
        self.attack = self._calculate_stat('attack')
        self.defense = self._calculate_stat('defense')
        self.special_attack = self._calculate_stat('special_attack')
        self.special_defense = self._calculate_stat('special_defense')
        self.speed = self._calculate_stat('speed')
        
        # Status conditions
        self.status_condition = None  # 'burn', 'paralysis', 'freeze', 'poison', 'toxic', 'sleep', 'confusion', etc.
        self.status_counter = 0  # For sleep turns, toxic counter, etc.
        self.volatile_status = set()  # For volatile status conditions
        
        # Use dataset moves if no moves provided
        if moves is None:
            available_moves = data_loader.get_pokemon_moves(self.name.lower(), 4)
            self.moves = {}
            for move_name in available_moves:
                move_data = data_loader.get_move_data(move_name)
                if move_data:
                    move_power = move_data.get('basePower', 0)
                    move_type = move_data.get('type', 'normal')
                    move_pp = move_data.get('pp', 10)
                    category = move_data.get('category', 'physical')
                    status_effect = move_data.get('status_effect')
                    self.moves[move_name] = Move(
                        name=move_name,
                        power=move_power,
                        pp=move_pp,
                        move_type=move_type,
                        category=category,
                        status_effect=status_effect
                    )
        else:
            # Use provided moves but enhance with dataset data
            self.moves = {}
            for move in moves:
                move_name = move['name']
                move_data = data_loader.get_move_data(move_name)
                if move_data:
                    move_power = move_data.get('basePower', 0)
                    move_type = move_data.get('type', 'normal')
                    move_pp = move.get('pp', 10)
                    category = move_data.get('category', 'physical')
                    status_effect = move_data.get('status_effect')
                    self.moves[move_name] = Move(
                        name=move_name,
                        power=move_power,
                        pp=move_pp,
                        move_type=move_type,
                        category=category,
                        status_effect=status_effect
                    )
                    # Also store max_pp for reference
                    self.moves[move_name].max_pp = move.get('max_pp', move_pp)
        #scaled to level 100 (since pokeapi wasnt setting pokemons to level 100 automatically for some reason)

    def take_damage(self, damage):
        """Apply damage to the Pokémon, ensuring HP doesn't go below 0."""
        self.current_hp = max(0, self.current_hp - damage)
        
    def heal(self, amount):
        """Heal the Pokémon by the specified amount, ensuring HP doesn't exceed max HP."""
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def _calculate_stat(self, stat_name):
        """Calculate a stat based on base stat, level, and stat stages."""
        if stat_name == 'hp':
            return self.max_hp
            
        base = self.base_stats[stat_name]
        level = self.level
        
        # Calculate base stat
        if stat_name in ['attack', 'defense', 'special_attack', 'special_defense', 'speed']:
            stat = int(((base * 2) * level / 100) + 5)
        else:
            stat = base
            
        # Apply stat stages
        stage = self.stat_stages.get(stat_name, 0)
        if stage > 0:
            stat = int(stat * (2 + stage) / 2)
        elif stage < 0:
            stat = int(stat * 2 / (2 - stage))
            
        # Apply status condition modifiers
        if stat_name == 'attack' and self.status_condition == 'burn':
            stat = int(stat * 0.5)
        elif stat_name == 'speed' and self.status_condition == 'paralysis':
            stat = int(stat * 0.5)
            
        return max(1, stat)  # Stats can't go below 1
        
    def apply_status_effect(self, status_effect):
        """Apply a status effect to the Pokémon."""
        # Can't change status if already statused or has a major status condition
        if self.status_condition in ['burn', 'paralysis', 'poison', 'toxic', 'freeze', 'sleep'] and \
           status_effect in ['burn', 'paralysis', 'poison', 'toxic', 'freeze', 'sleep']:
            return f"{self.name} is already affected by {self.status_condition}!"
            
        # Apply the status effect
        self.status_condition = status_effect
        
        # Reset status counter for certain conditions
        if status_effect == 'sleep':
            self.status_counter = random.randint(1, 3)  # 1-3 turns of sleep
            return f"{self.name} fell asleep!"
        elif status_effect == 'toxic':
            self.status_counter = 1  # Toxic counter starts at 1/16 and increases each turn
            return f"{self.name} was badly poisoned!"
        elif status_effect == 'poison':
            return f"{self.name} was poisoned!"
        elif status_effect == 'paralysis':
            # Reduce speed by 25%
            original_speed = self.speed
            self.speed = self._calculate_stat('speed')
            return f"{self.name} is paralyzed! It may be unable to move!"
        elif status_effect == 'burn':
            # Reduce attack by 50%
            original_attack = self.attack
            self.attack = self._calculate_stat('attack')
            return f"{self.name} was burned!"
        elif status_effect == 'freeze':
            return f"{self.name} was frozen solid!"
            
        return f"{self.name} was affected by {status_effect}!"
        
    def end_turn_status_effects(self):
        """Handle end-of-turn status effects like poison, burn, etc."""
        if not self.status_condition or self.current_hp <= 0:
            return ""
            
        messages = []
        
        # Handle damage from status conditions
        if self.status_condition == 'poison':
            damage = max(1, self.max_hp // 8)  # 1/8 max HP
            self.current_hp = max(1, self.current_hp - damage)
            messages.append(f"{self.name} is hurt by poison!")
            
        elif self.status_condition == 'toxic':
            damage = max(1, (self.max_hp // 16) * self.status_counter)  # 1/16, 2/16, 3/16, etc.
            self.current_hp = max(1, self.current_hp - damage)
            messages.append(f"{self.name} is hurt by poison!")
            self.status_counter += 1  # Increase toxic counter
            
        elif self.status_condition == 'burn':
            damage = max(1, self.max_hp // 16)  # 1/16 max HP
            self.current_hp = max(1, self.current_hp - damage)
            messages.append(f"{self.name} is hurt by its burn!")
            
        # Handle status condition recovery
        if self.status_condition == 'sleep':
            self.status_counter -= 1
            if self.status_counter <= 0:
                self.status_condition = None
                messages.append(f"{self.name} woke up!")
            else:
                messages.append(f"{self.name} is fast asleep.")
                
        elif self.status_condition == 'freeze':
            # 20% chance to thaw out each turn
            if random.random() < 0.2:
                self.status_condition = None
                messages.append(f"{self.name} thawed out!")
                
        return " ".join(messages) if messages else ""
        
    def is_fainted(self):
        return self.current_hp <= 0
        
    def can_attack(self):
        """Check if the Pokémon can attack this turn."""
        # Ensure status_condition is initialized
        if not hasattr(self, 'status_condition'):
            self.status_condition = None
            
        if self.status_condition == 'paralysis' and random.random() < 0.25:
            return False, f"{self.name} is paralyzed! It can't move!"
        elif self.status_condition == 'freeze':
            return False, f"{self.name} is frozen solid!"
        elif self.status_condition == 'sleep':
            return False, f"{self.name} is fast asleep."
        return True, ""
        
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
            'moves': {name: move.to_dict() for name, move in self.moves.items()}
        }
