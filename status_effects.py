import random
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class StatusType(Enum):
    BURN = "burn"
    PARALYSIS = "paralysis"
    FREEZE = "freeze"
    SLEEP = "sleep"
    POISON = "poison"
    TOXIC = "toxic"


class StatusEffect:
    def __init__(self, status_type: str, duration: int = -1, counter: int = 0):
        self.status_type = status_type
        self.duration = duration
        self.counter = counter
        self.config = STATUS_EFFECTS_CONFIG.get(status_type, {})
        self.name = self.config.get('name', status_type.title())
        self.is_major = self.config.get('is_major', False)
        
        # Initialize sleep duration if this is a sleep status
        if status_type == StatusType.SLEEP.value and duration == -1:
            duration_range = self.config.get('duration_range', (1, 3))
            self.duration = random.randint(*duration_range)
    
    def can_apply(self, pokemon) -> bool:
        # Major status conditions cannot be applied if Pokemon already has one
        if self.is_major and hasattr(pokemon, 'major_status') and pokemon.major_status:
            return False
            
        # Cannot apply the same status twice
        if hasattr(pokemon, 'status_effects') and self.status_type in pokemon.status_effects:
            return False
            
        return True
    
    def apply(self, pokemon) -> str:
        if not self.can_apply(pokemon):
            return ""
            
        # Apply the status effect
        if not hasattr(pokemon, 'status_effects'):
            pokemon.status_effects = {}
        if not hasattr(pokemon, 'major_status'):
            pokemon.major_status = None
            
        pokemon.status_effects[self.status_type] = self
        
        if self.is_major:
            pokemon.major_status = self.status_type
            
        # Return application message
        message_template = self.config.get('messages', {}).get('apply', "{pokemon} was affected by {status}!")
        return message_template.format(pokemon=pokemon.name, status=self.name)
    
    def process_turn_start(self, pokemon) -> List[str]:
        messages = []
        
        # Handle freeze thaw chance
        if self.status_type == StatusType.FREEZE.value:
            recovery_chance = self.config.get('recovery_chance', 0)
            if random.random() < recovery_chance:
                messages.append(self._recover_status(pokemon))
                return messages
        
        # Handle sleep wake up
        if self.status_type == StatusType.SLEEP.value:
            if self.duration > 0:
                self.duration -= 1
                if self.duration <= 0:
                    messages.append(self._recover_status(pokemon))
                    return messages
        
        return messages
    
    def process_turn_end(self, pokemon) -> List[str]:
        messages = []
        
        # Handle damage-dealing status effects
        turn_damage = self.config.get('turn_damage', 0)
        if turn_damage == 'escalating' or (isinstance(turn_damage, (int, float)) and turn_damage > 0):
            if self.status_type == StatusType.TOXIC.value:
                # Toxic damage increases each turn
                self.counter += 1
                damage = int(pokemon.max_hp * (self.counter / 16))
            else:
                # Regular damage (burn, poison)
                damage = int(pokemon.max_hp * turn_damage)
            
            # Apply damage (but don't let poison kill the Pokemon)
            if self.status_type == StatusType.POISON.value and pokemon.current_hp <= damage:
                damage = max(0, pokemon.current_hp - 1)
            
            if damage > 0:
                pokemon.current_hp = max(0, pokemon.current_hp - damage)
                damage_message = self.config.get('messages', {}).get('damage', "{pokemon} is hurt by {status}!")
                messages.append(damage_message.format(pokemon=pokemon.name, status=self.name))
        
        return messages
    
    def affects_move_usage(self, pokemon) -> Tuple[bool, str]:
        prevents_move = self.config.get('prevents_move', False)
        
        if not prevents_move:
            return False, ""
        
        # Handle chance-based move prevention (paralysis)
        if self.status_type == StatusType.PARALYSIS.value:
            prevention_chance = self.config.get('move_prevention_chance', 0)
            if random.random() < prevention_chance:
                message = self.config.get('messages', {}).get('prevent_move', "{pokemon} can't move!")
                return True, message.format(pokemon=pokemon.name)
            return False, ""
        
        # Handle guaranteed move prevention (freeze, sleep)
        if self.status_type in [StatusType.FREEZE.value, StatusType.SLEEP.value]:
            message = self.config.get('messages', {}).get('prevent_move', "{pokemon} can't move!")
            return True, message.format(pokemon=pokemon.name)
        
        return False, ""
    
    def modify_stat(self, pokemon, stat_name: str, stat_value: int) -> int:
        stat_modifiers = self.config.get('stat_modifiers', {})
        
        if stat_name in stat_modifiers:
            modifier = stat_modifiers[stat_name]
            return int(stat_value * modifier)
        
        return stat_value
    
    def _recover_status(self, pokemon) -> str:
        # Remove status from Pokemon
        if hasattr(pokemon, 'status_effects') and self.status_type in pokemon.status_effects:
            del pokemon.status_effects[self.status_type]
        
        if hasattr(pokemon, 'major_status') and pokemon.major_status == self.status_type:
            pokemon.major_status = None
        
        # Return recovery message
        message_template = self.config.get('messages', {}).get('recover', "{pokemon} recovered from {status}!")
        return message_template.format(pokemon=pokemon.name, status=self.name)


# Status Effects Configuration Dictionary
STATUS_EFFECTS_CONFIG = {
    StatusType.BURN.value: {
        'name': 'Burn',
        'is_major': True,
        'turn_damage': 1/16,  # 1/16 of max HP per turn
        'stat_modifiers': {'attack': 0.5},  # Physical attack halved
        'prevents_move': False,
        'recovery_chance': 0,  # Never recovers naturally
        'messages': {
            'apply': "{pokemon} was burned!",
            'damage': "{pokemon} is hurt by its burn!",
        }
    },
    StatusType.PARALYSIS.value: {
        'name': 'Paralysis',
        'is_major': True,
        'turn_damage': 0,
        'stat_modifiers': {'speed': 0.5},  # Speed halved
        'prevents_move': True,
        'move_prevention_chance': 0.25,  # 25% chance to be unable to move
        'recovery_chance': 0,
        'messages': {
            'apply': "{pokemon} is paralyzed! It may be unable to move!",
            'prevent_move': "{pokemon} is paralyzed! It can't move!",
        }
    },
    StatusType.FREEZE.value: {
        'name': 'Freeze',
        'is_major': True,
        'turn_damage': 0,
        'prevents_move': True,
        'move_prevention_chance': 1.0,  # Always prevents moves
        'recovery_chance': 0.2,  # 20% chance to thaw each turn
        'messages': {
            'apply': "{pokemon} was frozen solid!",
            'prevent_move': "{pokemon} is frozen solid!",
            'recover': "{pokemon} thawed out!"
        }
    },
    StatusType.SLEEP.value: {
        'name': 'Sleep',
        'is_major': True,
        'turn_damage': 0,
        'prevents_move': True,
        'move_prevention_chance': 1.0,  # Always prevents moves
        'duration_range': (1, 3),  # Sleep for 1-3 turns
        'messages': {
            'apply': "{pokemon} fell asleep!",
            'prevent_move': "{pokemon} is fast asleep.",
            'recover': "{pokemon} woke up!"
        }
    },
    StatusType.POISON.value: {
        'name': 'Poison',
        'is_major': True,
        'turn_damage': 1/8,  # 1/8 max HP per turn
        'prevents_move': False,
        'recovery_chance': 0,
        'messages': {
            'apply': "{pokemon} was poisoned!",
            'damage': "{pokemon} is hurt by poison!"
        }
    },
    StatusType.TOXIC.value: {
        'name': 'Badly Poisoned',
        'is_major': True,
        'turn_damage': 'escalating',  # Handled specially in process_turn_end
        'prevents_move': False,
        'recovery_chance': 0,
        'messages': {
            'apply': "{pokemon} was badly poisoned!",
            'damage': "{pokemon} is hurt by poison!"
        }
    }
}


class BurnStatusEffect(StatusEffect):
    def __init__(self, **kwargs):
        super().__init__(StatusType.BURN.value, **kwargs)
    
    def process_turn_end(self, pokemon) -> List[str]:
        messages = []
        
        # Calculate burn damage (1/16 of max HP)
        damage = int(pokemon.max_hp * (1/16))
        
        if damage > 0:
            pokemon.current_hp = max(0, pokemon.current_hp - damage)
            damage_message = self.config.get('messages', {}).get('damage', "{pokemon} is hurt by its burn!")
            messages.append(damage_message.format(pokemon=pokemon.name))
        
        return messages
    
    def modify_stat(self, pokemon, stat_name: str, stat_value: int) -> int:
        if stat_name == 'attack':
            return int(stat_value * 0.5)
        
        return stat_value
    
    def can_apply(self, pokemon) -> bool:
        # Check for existing major status
        if hasattr(pokemon, 'major_status') and pokemon.major_status:
            return False
            
        # Check for existing burn
        if hasattr(pokemon, 'status_effects') and StatusType.BURN.value in pokemon.status_effects:
            return False
            
        return True
    
    def apply(self, pokemon) -> str:
        if not self.can_apply(pokemon):
            return ""
            
        # Initialize status tracking if needed
        if not hasattr(pokemon, 'status_effects'):
            pokemon.status_effects = {}
        if not hasattr(pokemon, 'major_status'):
            pokemon.major_status = None
            
        # Apply burn status
        pokemon.status_effects[StatusType.BURN.value] = self
        pokemon.major_status = StatusType.BURN.value
            
        # Return application message
        return "{pokemon} was burned!".format(pokemon=pokemon.name)


class ParalysisStatusEffect(StatusEffect):
    def __init__(self, **kwargs):
        """Initialize paralysis status effect."""
        super().__init__(StatusType.PARALYSIS.value, **kwargs)
    
    def affects_move_usage(self, pokemon) -> Tuple[bool, str]:
        # 25% chance to prevent move usage
        prevention_chance = 0.25
        if random.random() < prevention_chance:
            message = "{pokemon} is paralyzed! It can't move!".format(pokemon=pokemon.name)
            return True, message
        
        return False, ""
    
    def modify_stat(self, pokemon, stat_name: str, stat_value: int) -> int:
        if stat_name == 'speed':
            return int(stat_value * 0.5)
        
        return stat_value
    
    def can_apply(self, pokemon) -> bool:
        # Check for existing major status
        if hasattr(pokemon, 'major_status') and pokemon.major_status:
            return False
            
        # Check for existing paralysis
        if hasattr(pokemon, 'status_effects') and StatusType.PARALYSIS.value in pokemon.status_effects:
            return False
            
        return True
    
    def apply(self, pokemon) -> str:
        if not self.can_apply(pokemon):
            return ""
            
        # Initialize status tracking if needed
        if not hasattr(pokemon, 'status_effects'):
            pokemon.status_effects = {}
        if not hasattr(pokemon, 'major_status'):
            pokemon.major_status = None
            
        # Apply paralysis status
        pokemon.status_effects[StatusType.PARALYSIS.value] = self
        pokemon.major_status = StatusType.PARALYSIS.value
            
        # Return application message
        return "{pokemon} is paralyzed! It may be unable to move!".format(pokemon=pokemon.name)
    
    def process_turn_start(self, pokemon) -> List[str]:
        return []
    
    def process_turn_end(self, pokemon) -> List[str]:
        return []


class FreezeStatusEffect(StatusEffect):
    def __init__(self, **kwargs):
        super().__init__(StatusType.FREEZE.value, **kwargs)
    
    def affects_move_usage(self, pokemon) -> Tuple[bool, str]:
        message = "{pokemon} is frozen solid!".format(pokemon=pokemon.name)
        return True, message
    
    def process_turn_start(self, pokemon) -> List[str]:
        messages = []
        
        # 20% chance to thaw out
        recovery_chance = 0.2
        if random.random() < recovery_chance:
            messages.append(self._recover_status(pokemon))
        
        return messages
    
    def process_turn_end(self, pokemon) -> List[str]:
        return []
    
    def can_apply(self, pokemon) -> bool:
        # Check for existing major status
        if hasattr(pokemon, 'major_status') and pokemon.major_status:
            return False
            
        # Check for existing freeze
        if hasattr(pokemon, 'status_effects') and StatusType.FREEZE.value in pokemon.status_effects:
            return False
            
        return True
    
    def apply(self, pokemon) -> str:
        if not self.can_apply(pokemon):
            return ""
            
        # Initialize status tracking if needed
        if not hasattr(pokemon, 'status_effects'):
            pokemon.status_effects = {}
        if not hasattr(pokemon, 'major_status'):
            pokemon.major_status = None
            
        # Apply freeze status
        pokemon.status_effects[StatusType.FREEZE.value] = self
        pokemon.major_status = StatusType.FREEZE.value
            
        # Return application message
        return "{pokemon} was frozen solid!".format(pokemon=pokemon.name)
    
    def _recover_status(self, pokemon) -> str:
        # Remove freeze status from Pokemon
        if hasattr(pokemon, 'status_effects') and StatusType.FREEZE.value in pokemon.status_effects:
            del pokemon.status_effects[StatusType.FREEZE.value]
        
        if hasattr(pokemon, 'major_status') and pokemon.major_status == StatusType.FREEZE.value:
            pokemon.major_status = None
        
        # Return thaw message
        return "{pokemon} thawed out!".format(pokemon=pokemon.name)


class SleepStatusEffect(StatusEffect):
    def __init__(self, **kwargs):
        """Initialize sleep status effect with random duration."""
        # Set random duration if not provided
        if 'duration' not in kwargs or kwargs['duration'] == -1:
            duration_range = STATUS_EFFECTS_CONFIG[StatusType.SLEEP.value].get('duration_range', (1, 3))
            kwargs['duration'] = random.randint(*duration_range)
        
        super().__init__(StatusType.SLEEP.value, **kwargs)
    
    def affects_move_usage(self, pokemon) -> Tuple[bool, str]:
        message = "{pokemon} is fast asleep.".format(pokemon=pokemon.name)
        return True, message
    
    def process_turn_start(self, pokemon) -> List[str]:
        messages = []
        
        # Decrease sleep duration
        if self.duration > 0:
            self.duration -= 1
            
            # Check if Pokemon should wake up
            if self.duration <= 0:
                messages.append(self._recover_status(pokemon))
        
        return messages
    
    def process_turn_end(self, pokemon) -> List[str]:
        return []
    
    def can_apply(self, pokemon) -> bool:
        # Check for existing major status
        if hasattr(pokemon, 'major_status') and pokemon.major_status:
            return False
            
        # Check for existing sleep
        if hasattr(pokemon, 'status_effects') and StatusType.SLEEP.value in pokemon.status_effects:
            return False
            
        return True
    
    def apply(self, pokemon) -> str:
        if not self.can_apply(pokemon):
            return ""
            
        # Initialize status tracking if needed
        if not hasattr(pokemon, 'status_effects'):
            pokemon.status_effects = {}
        if not hasattr(pokemon, 'major_status'):
            pokemon.major_status = None
            
        # Apply sleep status
        pokemon.status_effects[StatusType.SLEEP.value] = self
        pokemon.major_status = StatusType.SLEEP.value
            
        # Return application message
        return "{pokemon} fell asleep!".format(pokemon=pokemon.name)
    
    def _recover_status(self, pokemon) -> str:
        # Remove sleep status from Pokemon
        if hasattr(pokemon, 'status_effects') and StatusType.SLEEP.value in pokemon.status_effects:
            del pokemon.status_effects[StatusType.SLEEP.value]
        
        if hasattr(pokemon, 'major_status') and pokemon.major_status == StatusType.SLEEP.value:
            pokemon.major_status = None
        
        # Return wake up message
        return "{pokemon} woke up!".format(pokemon=pokemon.name)


class PoisonStatusEffect(StatusEffect):
    def __init__(self, **kwargs):
        super().__init__(StatusType.POISON.value, **kwargs)
    
    def process_turn_end(self, pokemon) -> List[str]:
        messages = []
        
        # Calculate poison damage (1/8 of max HP)
        damage = int(pokemon.max_hp * (1/8))
        
        # Prevent poison from reducing HP below 1
        if pokemon.current_hp <= damage:
            damage = max(0, pokemon.current_hp - 1)
        
        if damage > 0:
            pokemon.current_hp = max(1, pokemon.current_hp - damage)
            damage_message = self.config.get('messages', {}).get('damage', "{pokemon} is hurt by poison!")
            messages.append(damage_message.format(pokemon=pokemon.name))
        
        return messages
    
    def process_turn_start(self, pokemon) -> List[str]:
        return []
    
    def affects_move_usage(self, pokemon) -> Tuple[bool, str]:
        return False, ""
    
    def modify_stat(self, pokemon, stat_name: str, stat_value: int) -> int:
        return stat_value
    
    def can_apply(self, pokemon) -> bool:
        # Check for existing major status
        if hasattr(pokemon, 'major_status') and pokemon.major_status:
            return False
            
        # Check for existing poison
        if hasattr(pokemon, 'status_effects') and StatusType.POISON.value in pokemon.status_effects:
            return False
            
        return True
    
    def apply(self, pokemon) -> str:
        if not self.can_apply(pokemon):
            return ""
            
        # Initialize status tracking if needed
        if not hasattr(pokemon, 'status_effects'):
            pokemon.status_effects = {}
        if not hasattr(pokemon, 'major_status'):
            pokemon.major_status = None
            
        # Apply poison status
        pokemon.status_effects[StatusType.POISON.value] = self
        pokemon.major_status = StatusType.POISON.value
            
        # Return application message
        return "{pokemon} was poisoned!".format(pokemon=pokemon.name)


class ToxicStatusEffect(StatusEffect):
    def __init__(self, **kwargs):
        """Initialize toxic status effect."""
        super().__init__(StatusType.TOXIC.value, **kwargs)
        self.counter = 0  # Track turns for escalating damage
    
    def process_turn_end(self, pokemon) -> List[str]:
        messages = []
        
        # Increment counter for escalating damage
        self.counter += 1
        
        # Calculate toxic damage (counter/16 of max HP)
        damage = int(pokemon.max_hp * (self.counter / 16))
        
        # Prevent toxic from reducing HP below 1
        if pokemon.current_hp <= damage:
            damage = max(0, pokemon.current_hp - 1)
        
        if damage > 0:
            pokemon.current_hp = max(1, pokemon.current_hp - damage)
            damage_message = self.config.get('messages', {}).get('damage', "{pokemon} is hurt by poison!")
            messages.append(damage_message.format(pokemon=pokemon.name))
        
        return messages
    
    def process_turn_start(self, pokemon) -> List[str]:
        return []
    
    def affects_move_usage(self, pokemon) -> Tuple[bool, str]:
        return False, ""
    
    def modify_stat(self, pokemon, stat_name: str, stat_value: int) -> int:
        return stat_value
    
    def can_apply(self, pokemon) -> bool:
        # Check for existing major status
        if hasattr(pokemon, 'major_status') and pokemon.major_status:
            return False
            
        # Check for existing poison or toxic
        if hasattr(pokemon, 'status_effects'):
            if StatusType.POISON.value in pokemon.status_effects or StatusType.TOXIC.value in pokemon.status_effects:
                return False
            
        return True
    
    def apply(self, pokemon) -> str:
        if not self.can_apply(pokemon):
            return ""
            
        # Initialize status tracking if needed
        if not hasattr(pokemon, 'status_effects'):
            pokemon.status_effects = {}
        if not hasattr(pokemon, 'major_status'):
            pokemon.major_status = None
            
        # Apply toxic status
        pokemon.status_effects[StatusType.TOXIC.value] = self
        pokemon.major_status = StatusType.TOXIC.value
            
        # Return application message
        return "{pokemon} was badly poisoned!".format(pokemon=pokemon.name)


def create_status_effect(status_type: str, **kwargs) -> Optional[StatusEffect]:
    if status_type not in STATUS_EFFECTS_CONFIG:
        return None
    
    # Create specific status effect classes
    if status_type == StatusType.BURN.value:
        return BurnStatusEffect(**kwargs)
    elif status_type == StatusType.PARALYSIS.value:
        return ParalysisStatusEffect(**kwargs)
    elif status_type == StatusType.FREEZE.value:
        return FreezeStatusEffect(**kwargs)
    elif status_type == StatusType.SLEEP.value:
        return SleepStatusEffect(**kwargs)
    elif status_type == StatusType.POISON.value:
        return PoisonStatusEffect(**kwargs)
    elif status_type == StatusType.TOXIC.value:
        return ToxicStatusEffect(**kwargs)
    
    # Default to base StatusEffect for other types
    return StatusEffect(status_type, **kwargs)