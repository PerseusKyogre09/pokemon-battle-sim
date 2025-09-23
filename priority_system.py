"""
Priority System Module

This module provides comprehensive priority resolution for Pokemon battle moves,
including support for priority counters like Sucker Punch and extensible priority mechanics.
"""

from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import random


# Priority level constants based on official Pokemon mechanics
class PriorityLevels:
    """Standard Pokemon priority levels"""
    HELPING_HAND = 5        # Helping Hand (not implemented yet)
    PROTECT = 4             # Protect, Detect, Baneful Bunker
    FAKE_OUT = 3            # Fake Out, Quick Guard (not implemented yet)
    EXTREME_SPEED = 2       # Extreme Speed, Feint
    QUICK_ATTACK = 1        # Quick Attack, Aqua Jet, Sucker Punch, Baby-Doll Eyes
    NORMAL = 0              # Normal moves
    VITAL_THROW = -1        # Vital Throw (not implemented yet)
    BEAK_BLAST = -3         # Beak Blast
    AVALANCHE = -4          # Avalanche, Revenge
    ROAR = -6               # Roar, Whirlwind (not implemented yet)
    
    # Valid priority range
    MIN_PRIORITY = -6
    MAX_PRIORITY = 5
    
    @classmethod
    def validate_priority(cls, priority: int) -> int:
        """Validate and clamp priority value to valid range"""
        return max(cls.MIN_PRIORITY, min(cls.MAX_PRIORITY, priority))


@dataclass
class BattleAction:
    """Represents a move action with priority information for battle processing"""
    pokemon: Any  # Pokemon object
    move: Any     # Move object
    target: Any   # Target Pokemon object
    effective_priority: int
    is_priority_counter: bool = False
    counter_target_move: Optional[Any] = None
    
    def __post_init__(self):
        """Validate priority after initialization"""
        self.effective_priority = PriorityLevels.validate_priority(self.effective_priority)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert BattleAction to dictionary for serialization"""
        return {
            'pokemon_name': getattr(self.pokemon, 'name', 'Unknown'),
            'move_name': getattr(self.move, 'name', 'Unknown'),
            'target_name': getattr(self.target, 'name', 'Unknown'),
            'effective_priority': self.effective_priority,
            'is_priority_counter': self.is_priority_counter,
            'counter_target_move_name': getattr(self.counter_target_move, 'name', None) if self.counter_target_move else None
        }
    
    def can_execute(self) -> bool:
        """Check if this action can be executed (Pokemon not fainted, move has PP, etc.)"""
        # Check if Pokemon is fainted
        if hasattr(self.pokemon, 'is_fainted') and self.pokemon.is_fainted():
            return False
        
        # Check if Pokemon has current_hp <= 0
        if hasattr(self.pokemon, 'current_hp') and self.pokemon.current_hp <= 0:
            return False
        
        # Check if move has PP
        if hasattr(self.move, 'pp') and self.move.pp <= 0:
            return False
        
        # Check if this is a failed priority counter
        if self.effective_priority == -999:
            return False
        
        return True
    
    def get_speed_for_tiebreaker(self) -> int:
        """Get Pokemon speed for priority tiebreaking"""
        return getattr(self.pokemon, 'speed', 0)


class PriorityResolver:
    """
    Core priority resolution engine for Pokemon battles.
    
    Handles priority calculation, priority counter mechanics, and turn order determination.
    """
    
    def __init__(self):
        """Initialize the priority resolver"""
        self.debug_enabled = True
        self.sucker_punch_handler = SuckerPunchHandler()
    
    def resolve_turn_order(self, player_action: BattleAction, opponent_action: BattleAction) -> List[BattleAction]:
        """
        Resolve the turn order for two battle actions based on priority and speed.
        
        Args:
            player_action: The player's battle action
            opponent_action: The opponent's battle action
            
        Returns:
            List[BattleAction]: Actions ordered by execution priority (first to last)
        """
        if self.debug_enabled:
            print(f"DEBUG: Resolving turn order - Player: {player_action.move.name} (priority {player_action.effective_priority}), "
                  f"Opponent: {opponent_action.move.name} (priority {opponent_action.effective_priority})")
        
        # Check for priority counters first
        actions_with_counters = self.check_priority_counters([player_action, opponent_action])
        
        # Sort actions by effective priority (descending) and speed (descending)
        sorted_actions = sorted(actions_with_counters, key=self._get_sort_key, reverse=True)
        
        if self.debug_enabled:
            for i, action in enumerate(sorted_actions):
                print(f"DEBUG: Turn order {i+1}: {action.pokemon.name}'s {action.move.name} "
                      f"(priority: {action.effective_priority}, speed: {action.pokemon.speed})")
        
        return sorted_actions
    
    def check_priority_counters(self, actions: List[BattleAction]) -> List[BattleAction]:
        """
        Check and apply priority counter mechanics to battle actions.
        
        Args:
            actions: List of battle actions to check for priority counters
            
        Returns:
            List[BattleAction]: Actions with priority counter effects applied
        """
        if len(actions) != 2:
            return actions
        
        action1, action2 = actions
        
        # Check if either move is a priority counter
        action1_is_counter = self._is_priority_counter_move(action1.move)
        action2_is_counter = self._is_priority_counter_move(action2.move)
        
        if not action1_is_counter and not action2_is_counter:
            return actions
        
        # Handle priority counter logic
        updated_actions = []
        
        for action in actions:
            other_action = action2 if action == action1 else action1
            
            if self._is_priority_counter_move(action.move):
                # Check if the priority counter can succeed
                if self._can_priority_counter_succeed(action.move, other_action.move):
                    # Priority counter succeeds - gets highest priority
                    action.is_priority_counter = True
                    action.counter_target_move = other_action.move
                    action.effective_priority = self._get_counter_priority(action.move)
                    
                    if self.debug_enabled:
                        print(f"DEBUG: {action.pokemon.name}'s {action.move.name} priority counter succeeded! "
                              f"New priority: {action.effective_priority}")
                else:
                    # Priority counter fails - move fails completely
                    action.effective_priority = -999  # Ensure it goes last and fails
                    
                    if self.debug_enabled:
                        print(f"DEBUG: {action.pokemon.name}'s {action.move.name} priority counter failed!")
            
            updated_actions.append(action)
        
        return updated_actions
    
    def calculate_effective_priority(self, pokemon: Any, move: Any) -> int:
        """
        Calculate the effective priority for a Pokemon's move.
        
        Args:
            pokemon: The Pokemon using the move
            move: The move being used
            
        Returns:
            int: The effective priority value
        """
        base_priority = getattr(move, 'priority', 0)
        
        # Apply any priority modifiers from abilities, items, etc. (future extensibility)
        effective_priority = base_priority
        
        # Validate and clamp priority
        effective_priority = PriorityLevels.validate_priority(effective_priority)
        
        if self.debug_enabled:
            print(f"DEBUG: {pokemon.name}'s {move.name} effective priority: {effective_priority}")
        
        return effective_priority
    
    def _get_sort_key(self, action: BattleAction) -> Tuple[int, int, float]:
        """
        Get sorting key for battle actions.
        
        Returns tuple of (priority, speed, random_tiebreaker) for sorting.
        Higher values sort first when reverse=True.
        """
        return (
            action.effective_priority,
            getattr(action.pokemon, 'speed', 0),
            random.random()  # Random tiebreaker for equal priority and speed
        )
    
    def _is_priority_counter_move(self, move: Any) -> bool:
        """
        Check if a move is a priority counter move.
        
        Args:
            move: The move to check
            
        Returns:
            bool: True if the move is a priority counter
        """
        # Use SuckerPunchHandler to check for Sucker Punch
        return self.sucker_punch_handler.is_sucker_punch(move)
    
    def _can_priority_counter_succeed(self, counter_move: Any, target_move: Any) -> bool:
        """
        Check if a priority counter move can succeed against the target move.
        
        Args:
            counter_move: The priority counter move
            target_move: The target move being countered
            
        Returns:
            bool: True if the counter can succeed
        """
        if self.sucker_punch_handler.is_sucker_punch(counter_move):
            return self.sucker_punch_handler.check_success_condition(target_move)
        
        # Future priority counters can be added here
        return False
    

    
    def _get_counter_priority(self, counter_move: Any) -> int:
        """
        Get the priority value for a successful priority counter.
        
        Args:
            counter_move: The priority counter move
            
        Returns:
            int: The priority value when the counter succeeds
        """
        if self.sucker_punch_handler.is_sucker_punch(counter_move):
            return self.sucker_punch_handler.priority_when_successful
        
        # Default to normal priority for unknown counters
        return PriorityLevels.NORMAL
    
    def get_priority_counter_failure_message(self, counter_move: Any) -> str:
        """
        Get the failure message for a priority counter move.
        
        Args:
            counter_move: The priority counter move that failed
            
        Returns:
            str: The failure message
        """
        if self.sucker_punch_handler.is_sucker_punch(counter_move):
            return self.sucker_punch_handler.get_failure_message()
        
        return "The move failed!"
    
    def get_priority_counter_success_message(self, counter_move: Any, attacker_name: str, target_name: str, target_move_name: str) -> str:
        """
        Get the success message for a priority counter move.
        
        Args:
            counter_move: The priority counter move that succeeded
            attacker_name: Name of the Pokemon using the counter move
            target_name: Name of the target Pokemon
            target_move_name: Name of the move being countered
            
        Returns:
            str: The success message
        """
        if self.sucker_punch_handler.is_sucker_punch(counter_move):
            return self.sucker_punch_handler.get_success_message(attacker_name, target_name, target_move_name)
        
        return f"{attacker_name} intercepted {target_name}'s {target_move_name}!"
    
    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug logging"""
        self.debug_enabled = enabled


class PriorityCounterConditions:
    """
    Configuration for priority counter conditions.
    
    This class defines the conditions under which priority counter moves
    succeed or fail, making it easy to extend with new priority counters.
    """
    
    SUCKER_PUNCH = {
        'name': 'sucker_punch',
        'counters': ['physical', 'special'],  # Move categories that can be countered
        'fails_against': ['status'],          # Move categories that cause failure
        'priority_when_successful': PriorityLevels.QUICK_ATTACK,
        'failure_message': "But it failed!"
    }
    
    # Future priority counters can be added here
    # FAKE_OUT = {
    #     'name': 'fake_out',
    #     'counters': ['physical', 'special', 'status'],
    #     'fails_against': [],
    #     'priority_when_successful': PriorityLevels.FAKE_OUT,
    #     'failure_message': "But it failed!"
    # }
    
    @classmethod
    def get_counter_config(cls, move_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for a priority counter move.
        
        Args:
            move_name: The name of the move
            
        Returns:
            Optional[Dict]: The counter configuration, or None if not a counter
        """
        move_name_normalized = move_name.lower().replace(' ', '_').replace('-', '_')
        
        # Check all defined counter configurations
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and attr_name.isupper():
                config = getattr(cls, attr_name)
                if isinstance(config, dict) and config.get('name') == move_name_normalized:
                    return config
        
        return None


class SuckerPunchHandler:
    """
    Specialized handler for Sucker Punch priority counter logic.
    
    This class manages the specific logic for Sucker Punch, including success condition
    checking, failure condition handling, and appropriate messaging.
    """
    
    def __init__(self):
        """Initialize the Sucker Punch handler"""
        self.move_name = "sucker punch"
        self.priority_when_successful = PriorityLevels.QUICK_ATTACK
        self.failure_message = "But it failed!"
        self.success_message_template = "{attacker} intercepted {target}'s {target_move}!"
    
    def check_success_condition(self, target_move: Any) -> bool:
        """
        Check if Sucker Punch can successfully counter the target move.
        
        Sucker Punch succeeds when the target uses an attacking move (physical or special).
        It fails when the target uses a status move or switches.
        
        Args:
            target_move: The move that the target Pokemon is using
            
        Returns:
            bool: True if Sucker Punch can succeed, False otherwise
        """
        if not target_move:
            return False
        
        # Get the target move's category
        target_category = getattr(target_move, 'category', '').lower()
        
        # Sucker Punch succeeds against attacking moves (physical and special)
        return target_category in ['physical', 'special']
    
    def check_failure_condition(self, target_move: Any) -> bool:
        """
        Check if Sucker Punch should fail against the target move.
        
        Sucker Punch fails when the target uses a status move or switches.
        
        Args:
            target_move: The move that the target Pokemon is using
            
        Returns:
            bool: True if Sucker Punch should fail, False otherwise
        """
        if not target_move:
            return True  # Fail if no target move (e.g., switching)
        
        # Get the target move's category
        target_category = getattr(target_move, 'category', '').lower()
        
        # Sucker Punch fails against status moves
        return target_category == 'status'
    
    def get_success_message(self, attacker_name: str, target_name: str, target_move_name: str) -> str:
        """
        Get the success message when Sucker Punch successfully counters a move.
        
        Args:
            attacker_name: Name of the Pokemon using Sucker Punch
            target_name: Name of the target Pokemon
            target_move_name: Name of the move being countered
            
        Returns:
            str: The success message for the battle log
        """
        # Capitalize Pokémon names and provide more detailed success messages based on the target move
        attacker_name = attacker_name.capitalize()
        target_name = target_name.capitalize()
        
        if target_move_name.lower() in ['quick-attack', 'aqua-jet', 'bullet-punch', 'mach-punch']:
            return f"{attacker_name} anticipated {target_name}'s priority move and struck first with Sucker Punch!"
        elif target_move_name.lower() in ['extreme-speed']:
            return f"{attacker_name} intercepted {target_name}'s Extreme Speed with a perfectly timed Sucker Punch!"
        else:
            return f"{attacker_name} read {target_name}'s attack and countered with Sucker Punch!"
    
    def get_failure_message(self) -> str:
        """
        Get the failure message when Sucker Punch fails.
        
        Returns:
            str: The failure message for the battle log
        """
        return self.failure_message
    
    def get_effective_priority(self, target_move: Any) -> int:
        """
        Get the effective priority for Sucker Punch based on the target move.
        
        Args:
            target_move: The move that the target Pokemon is using
            
        Returns:
            int: The effective priority value (high priority if successful, very low if failed)
        """
        if self.check_success_condition(target_move):
            return self.priority_when_successful
        else:
            # Return very low priority to ensure failed Sucker Punch goes last
            return -999
    
    def validate_target_move_category(self, target_move: Any) -> Tuple[bool, str]:
        """
        Validate the target move's category for Sucker Punch success/failure.
        
        Args:
            target_move: The move that the target Pokemon is using
            
        Returns:
            Tuple[bool, str]: (success, message) where success indicates if Sucker Punch
                             succeeds and message provides appropriate feedback
        """
        if not target_move:
            return False, self.get_failure_message()
        
        if self.check_success_condition(target_move):
            # Don't return success message here - it will be handled during move execution
            return True, ""
        else:
            return False, self.get_failure_message()
    
    def is_sucker_punch(self, move: Any) -> bool:
        """
        Check if the given move is Sucker Punch.
        
        Args:
            move: The move to check
            
        Returns:
            bool: True if the move is Sucker Punch, False otherwise
        """
        if not move:
            return False
        
        move_name = getattr(move, 'name', '').lower()
        return move_name == self.move_name


class ActionQueue:
    """
    Manages a queue of battle actions with priority-aware ordering and execution.
    
    This class handles the conversion of Pokemon moves to battle actions,
    priority-based sorting, and sequential execution of actions.
    """
    
    def __init__(self, priority_resolver: PriorityResolver):
        """
        Initialize the action queue.
        
        Args:
            priority_resolver: The priority resolver to use for action processing
        """
        self.priority_resolver = priority_resolver
        self.actions: List[BattleAction] = []
        self.executed_actions: List[BattleAction] = []
        self.debug_enabled = True
    
    def add_action(self, pokemon: Any, move: Any, target: Any) -> BattleAction:
        """
        Add a battle action to the queue.
        
        Args:
            pokemon: The Pokemon using the move
            move: The move being used
            target: The target Pokemon
            
        Returns:
            BattleAction: The created battle action
        """
        action = create_battle_action(pokemon, move, target, self.priority_resolver)
        self.actions.append(action)
        
        if self.debug_enabled:
            print(f"DEBUG: Added action - {pokemon.name}'s {move.name} (priority: {action.effective_priority})")
        
        return action
    
    def add_actions_from_moves(self, move_pairs: List[Tuple[Any, Any, Any]]) -> List[BattleAction]:
        """
        Add multiple battle actions from a list of (pokemon, move, target) tuples.
        
        Args:
            move_pairs: List of (pokemon, move, target) tuples
            
        Returns:
            List[BattleAction]: The created battle actions
        """
        created_actions = []
        for pokemon, move, target in move_pairs:
            action = self.add_action(pokemon, move, target)
            created_actions.append(action)
        
        return created_actions
    
    def sort_by_priority(self) -> List[BattleAction]:
        """
        Sort actions by priority and speed, applying priority counter logic.
        
        Returns:
            List[BattleAction]: Actions sorted by execution order (first to last)
        """
        if len(self.actions) == 0:
            return []
        
        # Apply priority counter logic if there are exactly 2 actions
        if len(self.actions) == 2:
            processed_actions = self.priority_resolver.check_priority_counters(self.actions.copy())
        else:
            processed_actions = self.actions.copy()
        
        # Sort actions by priority (descending), then speed (descending), then random tiebreaker
        sorted_actions = sorted(
            processed_actions, 
            key=lambda action: (
                action.effective_priority,
                action.get_speed_for_tiebreaker(),
                random.random()
            ), 
            reverse=True
        )
        
        if self.debug_enabled:
            print("DEBUG: Action queue sorted by priority:")
            for i, action in enumerate(sorted_actions):
                print(f"  {i+1}. {action.pokemon.name}'s {action.move.name} "
                      f"(priority: {action.effective_priority}, speed: {action.get_speed_for_tiebreaker()})")
        
        return sorted_actions
    
    def get_executable_actions(self) -> List[BattleAction]:
        """
        Get actions that can be executed (Pokemon not fainted, move has PP, etc.).
        
        Returns:
            List[BattleAction]: Actions that can be executed
        """
        executable = []
        for action in self.actions:
            if action.can_execute():
                executable.append(action)
            elif self.debug_enabled:
                print(f"DEBUG: Action {action.pokemon.name}'s {action.move.name} cannot be executed")
        
        return executable
    
    def execute_next_action(self) -> Optional[BattleAction]:
        """
        Execute the next action in priority order.
        
        Returns:
            Optional[BattleAction]: The executed action, or None if no actions available
        """
        if not self.actions:
            return None
        
        # Get sorted actions
        sorted_actions = self.sort_by_priority()
        
        # Find the first executable action
        for action in sorted_actions:
            if action.can_execute() and action not in self.executed_actions:
                self.executed_actions.append(action)
                
                if self.debug_enabled:
                    print(f"DEBUG: Executing action - {action.pokemon.name}'s {action.move.name}")
                
                return action
        
        return None
    
    def execute_all_actions(self) -> List[BattleAction]:
        """
        Execute all actions in priority order.
        
        Returns:
            List[BattleAction]: List of executed actions in execution order
        """
        executed = []
        
        while True:
            action = self.execute_next_action()
            if action is None:
                break
            executed.append(action)
        
        return executed
    
    def clear(self):
        """Clear all actions from the queue"""
        self.actions.clear()
        self.executed_actions.clear()
        
        if self.debug_enabled:
            print("DEBUG: Action queue cleared")
    
    def get_action_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current action queue state.
        
        Returns:
            Dict: Summary information about the queue
        """
        return {
            'total_actions': len(self.actions),
            'executed_actions': len(self.executed_actions),
            'remaining_actions': len(self.actions) - len(self.executed_actions),
            'actions': [action.to_dict() for action in self.actions],
            'executed': [action.to_dict() for action in self.executed_actions]
        }
    
    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug logging"""
        self.debug_enabled = enabled


def create_battle_action(pokemon: Any, move: Any, target: Any, priority_resolver: PriorityResolver) -> BattleAction:
    """
    Factory function to create a BattleAction with calculated priority.
    
    Args:
        pokemon: The Pokemon using the move
        move: The move being used
        target: The target Pokemon
        priority_resolver: The priority resolver to use for calculations
        
    Returns:
        BattleAction: A battle action with calculated effective priority
    """
    effective_priority = priority_resolver.calculate_effective_priority(pokemon, move)
    
    return BattleAction(
        pokemon=pokemon,
        move=move,
        target=target,
        effective_priority=effective_priority
    )


def create_battle_actions_from_pokemon_moves(
    pokemon_move_pairs: List[Tuple[Any, str, Any]], 
    priority_resolver: PriorityResolver
) -> List[BattleAction]:
    """
    Create battle actions from a list of Pokemon and move name pairs.
    
    Args:
        pokemon_move_pairs: List of (pokemon, move_name, target) tuples
        priority_resolver: The priority resolver to use for calculations
        
    Returns:
        List[BattleAction]: List of created battle actions
    """
    actions = []
    
    for pokemon, move_name, target in pokemon_move_pairs:
        # Get the move object from the Pokemon's moveset
        move = None
        if hasattr(pokemon, 'moves') and isinstance(pokemon.moves, dict):
            move = pokemon.moves.get(move_name)
        
        if move is None:
            print(f"WARNING: Move '{move_name}' not found for {getattr(pokemon, 'name', 'Unknown')}")
            continue
        
        # Create the battle action
        action = create_battle_action(pokemon, move, target, priority_resolver)
        actions.append(action)
    
    return actions


def sort_actions_by_priority(actions: List[BattleAction]) -> List[BattleAction]:
    """
    Sort battle actions by priority and speed.
    
    Args:
        actions: List of battle actions to sort
        
    Returns:
        List[BattleAction]: Actions sorted by execution order (first to last)
    """
    return sorted(
        actions,
        key=lambda action: (
            action.effective_priority,
            action.get_speed_for_tiebreaker(),
            random.random()  # Random tiebreaker
        ),
        reverse=True
    )


def filter_executable_actions(actions: List[BattleAction]) -> List[BattleAction]:
    """
    Filter battle actions to only include those that can be executed.
    
    Args:
        actions: List of battle actions to filter
        
    Returns:
        List[BattleAction]: Actions that can be executed
    """
    return [action for action in actions if action.can_execute()]


def create_action_queue_for_turn(
    player_pokemon: Any, 
    player_move_name: str, 
    opponent_pokemon: Any, 
    opponent_move_name: str,
    priority_resolver: PriorityResolver
) -> ActionQueue:
    """
    Create an action queue for a battle turn with player and opponent moves.
    
    Args:
        player_pokemon: The player's Pokemon
        player_move_name: Name of the player's selected move
        opponent_pokemon: The opponent's Pokemon
        opponent_move_name: Name of the opponent's selected move
        priority_resolver: The priority resolver to use
        
    Returns:
        ActionQueue: Configured action queue for the turn
    """
    queue = ActionQueue(priority_resolver)
    
    # Add player action
    player_move = player_pokemon.moves.get(player_move_name) if hasattr(player_pokemon, 'moves') else None
    if player_move:
        queue.add_action(player_pokemon, player_move, opponent_pokemon)
    
    # Add opponent action
    opponent_move = opponent_pokemon.moves.get(opponent_move_name) if hasattr(opponent_pokemon, 'moves') else None
    if opponent_move:
        queue.add_action(opponent_pokemon, opponent_move, player_pokemon)
    
    return queue