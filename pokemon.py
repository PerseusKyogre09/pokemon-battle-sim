from move import Move
from data_loader import data_loader
from status_effects import StatusEffect, BurnStatusEffect, ParalysisStatusEffect, FreezeStatusEffect, SleepStatusEffect, PoisonStatusEffect, StatusType
import random

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
        
        # Initialize new status management system
        self.status_effects = {}  # Dict of status_type -> StatusEffect
        self.major_status = None  # Reference to current major status
        self.volatile_statuses = set()  # Set of volatile status types
        self.status_change_events = []  # Track status change events for this turn
        
        # Keep old attributes for backward compatibility
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
        
        # Maintain backward compatibility with old status system
        # These will be updated by the new status management methods
        
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
                    move_accuracy = move_data.get('accuracy', 100)
                    category = move_data.get('category', 'physical')
                    status_effect = move_data.get('status_effect')
                    self.moves[move_name] = Move(
                        name=move_name,
                        power=move_power,
                        pp=move_pp,
                        move_type=move_type,
                        accuracy=move_accuracy,
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
            
        # Apply status effect modifiers using new system
        stat = self.get_modified_stat_value(stat_name, stat)
            
        return max(1, stat)  # Stats can't go below 1
    
    def get_modified_stat_value(self, stat_name: str, base_value: int) -> int:
        """Get stat value with status effect modifications applied."""
        modified_value = base_value
        
        # Apply modifications from all active status effects
        for status_effect in self.status_effects.values():
            modified_value = status_effect.modify_stat(self, stat_name, modified_value)
        
        return modified_value
        
    def apply_status_effect(self, status_type: str, **kwargs) -> str:
        """Apply a status effect using the new status system with proper validation."""
        # Validate input
        if not status_type or not isinstance(status_type, str):
            return ""
        
        status_type = status_type.lower().strip()
        
        # Create the appropriate status effect object
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
                # Import ToxicStatusEffect when it's implemented
                try:
                    from status_effects import ToxicStatusEffect
                    status_effect = ToxicStatusEffect(**kwargs)
                except ImportError:
                    status_effect = StatusEffect(status_type, **kwargs)
            else:
                # Generic status effect for unknown types
                status_effect = StatusEffect(status_type, **kwargs)
        except Exception as e:
            print(f"ERROR: Failed to create status effect {status_type}: {e}")
            import traceback
            traceback.print_exc()
            return ""
        
        if status_effect:
            if status_effect.can_apply(self):
                try:
                    message = status_effect.apply(self)
                    # Update backward compatibility attributes
                    self._update_legacy_status()
                    # Recalculate stats to apply status effect modifications
                    self._recalculate_stats()
                    return message
                except Exception as e:
                    print(f"ERROR: Failed to apply status effect {status_type} to {self.name}: {e}")
                    import traceback
                    traceback.print_exc()
                    return ""
            else:
                return ""
        
        return ""
    

    
    def remove_status_effect(self, status_type: str) -> str:
        """Remove a specific status effect."""
        if status_type in self.status_effects:
            status_effect = self.status_effects[status_type]
            del self.status_effects[status_type]
            
            # Clear major status if this was the major status
            if self.major_status == status_type:
                self.major_status = None
            
            # Generate status change event
            self._add_status_change_event('status_removed', status_type, status_effect.name)
            
            # Update backward compatibility attributes
            self._update_legacy_status()
            # Recalculate stats to remove status effect modifications
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
        
        # Process each status effect's turn start effects
        for status_effect in list(self.status_effects.values()):
            effect_messages = status_effect.process_turn_start(self)
            messages.extend(effect_messages)
        
        # Update backward compatibility attributes
        self._update_legacy_status()
        
        return messages
    
    def process_turn_end_effects(self) -> list:
        """Process all status effects at turn end."""
        messages = []
        
        # Process each status effect's turn end effects
        for status_effect in list(self.status_effects.values()):
            effect_messages = status_effect.process_turn_end(self)
            messages.extend(effect_messages)
        
        # Update backward compatibility attributes
        self._update_legacy_status()
        
        return messages
    
    def can_use_move(self) -> tuple:
        """Check if pokemon can use a move this turn."""
        # Check all status effects for move prevention
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
            # Set counter based on status effect if available
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
        # Use new status system if available
        if hasattr(self, 'status_effects') and self.status_effects:
            messages = self.process_turn_end_effects()
            return " ".join(messages) if messages else ""
        
        # Fallback to old system for backward compatibility
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
        # Use new status system if available, fall back to old system
        if hasattr(self, 'status_effects') and self.status_effects:
            return self.can_use_move()
        
        # Fallback to old system for backward compatibility
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
            'moves': {name: move.to_dict() for name, move in self.moves.items()},
            'status_effects': self.get_status_display(),
            'major_status': self.major_status,
            'status_condition': self.status_condition  # For backward compatibility
        }
