from data_loader import data_loader
from typing import Optional, Tuple, Dict, Any, Union, List
import random

class Move:
    def __init__(self, name: str, power: int, pp: int, move_type: str = 'normal', 
                 accuracy: Union[int, bool] = 100, category: str = 'physical',
                 status_effect: Optional[Dict[str, Any]] = None, priority: int = 0):
        self.name = name
        self.power = power
        self.pp = pp
        self.max_pp = pp
        self.type = move_type.lower()
        self.accuracy = accuracy
        self.category = category.lower()
        self.is_status_move = category.lower() == 'status' or power == 0
        self.priority = priority  # Higher priority moves go first
        
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
        
        # Parse healing properties from move data
        self.is_healing_move, self.heal_amount, self.drain_ratio = self._parse_healing_data()
        
        # Parse multi-hit properties from move data
        self.is_multihit_move, self.multihit_data = self._parse_multihit_data()
        
        # Parse priority counter properties from move data
        self.is_priority_counter, self.priority_counter_conditions = self._parse_priority_counter_data()

    def _parse_move_data(self) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], int]:
        # Get move data from the dataset
        move_data = data_loader.get_move(self.name)
        if not move_data:
            return None, None, 0
            
        # Set priority from move data if available
        if 'priority' in move_data:
            self.priority = move_data['priority']
        
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
    
    def _parse_healing_data(self) -> Tuple[bool, Optional[List[int]], Optional[List[int]]]:
        """Parse healing and drain data from move dataset during initialization"""
        # Get move data from the dataset
        move_data = data_loader.get_move(self.name)
        if not move_data:
            return False, None, None
        
        # Get the raw move data to access heal and drain properties
        raw_move_data = self._get_raw_move_data()
        if not raw_move_data:
            return False, None, None
        
        is_healing = False
        heal_amount = None
        drain_ratio = None
        
        # Check for direct healing moves (heal property)
        if 'heal' in raw_move_data and isinstance(raw_move_data['heal'], list):
            is_healing = True
            heal_amount = raw_move_data['heal']
        
        # Check for HP-draining moves (drain property)
        if 'drain' in raw_move_data and isinstance(raw_move_data['drain'], list):
            is_healing = True
            drain_ratio = raw_move_data['drain']
        
        # Also check flags for heal flag
        if 'flags' in raw_move_data and isinstance(raw_move_data['flags'], dict):
            if raw_move_data['flags'].get('heal') == 1:
                is_healing = True
        
        return is_healing, heal_amount, drain_ratio
    
    def _parse_multihit_data(self) -> Tuple[bool, Optional[Union[int, List[int]]]]:
        """Parse multi-hit data from move dataset during initialization"""
        # Get move data from the dataset
        move_data = data_loader.get_move(self.name)
        if not move_data:
            return False, None
        
        # Get the raw move data to access multihit property
        raw_move_data = self._get_raw_move_data()
        if not raw_move_data:
            return False, None
        
        # Check for multihit property
        if 'multihit' in raw_move_data:
            multihit_data = raw_move_data['multihit']
            if isinstance(multihit_data, int):
                # Fixed number of hits (e.g., Triple Kick = 3)
                return True, multihit_data
            elif isinstance(multihit_data, list) and len(multihit_data) == 2:
                # Range of hits (e.g., Spike Cannon = [2,5])
                return True, multihit_data
            else:
                print(f"WARNING: Invalid multihit data format for {self.name}: {multihit_data}")
                return False, None
        
        return False, None
    
    def _parse_priority_counter_data(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Parse priority counter data from move dataset during initialization"""
        # Get the raw move data to access description and other properties
        raw_move_data = self._get_raw_move_data()
        if not raw_move_data:
            return False, None
        
        # Check if this move is a priority counter based on its description
        desc = raw_move_data.get('desc', '').lower()
        short_desc = raw_move_data.get('shortDesc', '').lower()
        
        # Define priority counter conditions based on known moves
        priority_counter_conditions = {
            'sucker punch': {
                'counters': ['physical', 'special'],  # Move categories that can be countered
                'fails_against': ['status'],
                'priority_when_successful': 1,
                'failure_message': "But it failed!",
                'success_condition': 'target_uses_attacking_move'
            }
        }
        
        move_name_lower = self.name.lower()
        
        # Check if this is a known priority counter move
        if move_name_lower in priority_counter_conditions:
            return True, priority_counter_conditions[move_name_lower]
        
        # Check for priority counter patterns in description
        # Sucker Punch pattern: "Fails if the target did not select a physical attack, special attack"
        if ('fails if' in desc and 'attack' in desc and 'target' in desc) or \
           ('fails if target is not attacking' in short_desc):
            # This appears to be a priority counter move
            return True, {
                'counters': ['physical', 'special'],
                'fails_against': ['status'],
                'priority_when_successful': self.priority,
                'failure_message': "But it failed!",
                'success_condition': 'target_uses_attacking_move'
            }
        
        return False, None
    
    def _determine_hit_count(self) -> int:
        """Determine how many times a multi-hit move should hit"""
        if not self.is_multihit_move or not self.multihit_data:
            return 1
        
        if isinstance(self.multihit_data, int):
            # Fixed number of hits
            return self.multihit_data
        elif isinstance(self.multihit_data, list) and len(self.multihit_data) == 2:
            # Range of hits - use Pokemon's standard probability distribution
            min_hits, max_hits = self.multihit_data
            
            # Standard multi-hit move probability distribution:
            # 2 hits: 35% chance
            # 3 hits: 35% chance  
            # 4 hits: 15% chance
            # 5 hits: 15% chance
            if max_hits == 5:
                rand = random.randint(1, 100)
                if rand <= 35:
                    return 2
                elif rand <= 70:
                    return 3
                elif rand <= 85:
                    return 4
                else:
                    return 5
            else:
                # For other ranges, use uniform distribution
                return random.randint(min_hits, max_hits)
        
        return 1
    
    def _get_raw_move_data(self) -> Optional[Dict[str, Any]]:
        """Get raw move data directly from the JSON dataset"""
        try:
            import json
            with open('datasets/moves.json', 'r', encoding='utf-8') as f:
                moves_data = json.load(f)
            
            # Try different variations of the move name
            move_key = self.name.lower().replace(' ', '').replace('-', '')
            
            # Direct lookup
            if move_key in moves_data:
                return moves_data[move_key]
            
            # Search by name field
            for key, data in moves_data.items():
                if data.get('name', '').lower() == self.name.lower():
                    return data
            
            return None
        except Exception as e:
            print(f"ERROR: Failed to get raw move data for {self.name}: {e}")
            return None
    
    def is_priority_counter_move(self) -> bool:
        """
        Determine if this move is a priority counter move.
        
        Returns:
            bool: True if this move is a priority counter (like Sucker Punch), False otherwise
        """
        return self.is_priority_counter
    
    def can_counter_move(self, target_move: 'Move') -> bool:
        """
        Determine if this priority counter move can successfully counter the target move.
        
        Args:
            target_move: The move that the target Pokemon is using
            
        Returns:
            bool: True if this move can counter the target move, False otherwise
        """
        if not self.is_priority_counter:
            return False
        
        if not target_move:
            return False
        
        # Import here to avoid circular imports
        from priority_system import SuckerPunchHandler
        
        # Use SuckerPunchHandler for Sucker Punch logic
        if self.name.lower() == 'sucker punch':
            handler = SuckerPunchHandler()
            return handler.check_success_condition(target_move)
        
        # Fallback to original logic for other priority counters
        if self.priority_counter_conditions:
            # Get the categories this move can counter
            counters = self.priority_counter_conditions.get('counters', [])
            fails_against = self.priority_counter_conditions.get('fails_against', [])
            
            # Check if target move category is in the list of categories this move counters
            target_category = target_move.category.lower()
            
            # Priority counter succeeds if target uses a move in the 'counters' list
            if target_category in counters:
                return True
            
            # Priority counter fails if target uses a move in the 'fails_against' list
            if target_category in fails_against:
                return False
        
        # Default behavior: counter succeeds against attacking moves, fails against status moves
        return not target_move.is_status_move
    
    def get_priority_counter_failure_message(self) -> str:
        """
        Get the failure message for when this priority counter move fails.
        
        Returns:
            str: The failure message to display when the priority counter fails
        """
        if not self.is_priority_counter:
            return ""
        
        # Import here to avoid circular imports
        from priority_system import SuckerPunchHandler
        
        # Use SuckerPunchHandler for Sucker Punch logic
        if self.name.lower() == 'sucker punch':
            handler = SuckerPunchHandler()
            return handler.get_failure_message()
        
        # Fallback to original logic for other priority counters
        if self.priority_counter_conditions:
            return self.priority_counter_conditions.get('failure_message', "But it failed!")
        
        return "But it failed!"
    
    def validate_move_category_for_counter(self, target_move: 'Move') -> Tuple[bool, str]:
        """
        Validate if the target move's category allows this priority counter to succeed.
        
        Args:
            target_move: The move that the target Pokemon is using
            
        Returns:
            Tuple[bool, str]: (success, message) where success indicates if counter succeeds
                             and message provides explanation
        """
        if not self.is_priority_counter:
            return True, ""  # Not a priority counter, no validation needed
        
        if not target_move:
            return False, self.get_priority_counter_failure_message()
        
        # Import here to avoid circular imports
        from priority_system import SuckerPunchHandler
        
        # Use SuckerPunchHandler for Sucker Punch logic
        if self.name.lower() == 'sucker punch':
            handler = SuckerPunchHandler()
            return handler.validate_target_move_category(target_move)
        
        # Fallback to original logic for other priority counters
        can_counter = self.can_counter_move(target_move)
        
        if can_counter:
            return True, f"{self.name} intercepted {target_move.name}!"
        else:
            return False, self.get_priority_counter_failure_message()
    
    def get_effective_priority_against_move(self, target_move: Optional['Move']) -> int:
        """
        Get the effective priority of this move when used against a specific target move.
        For priority counters, this may be different from the base priority.
        
        Args:
            target_move: The move that the target Pokemon is using
            
        Returns:
            int: The effective priority value for this move
        """
        if not self.is_priority_counter or not target_move:
            return self.priority
        
        # Import here to avoid circular imports
        from priority_system import SuckerPunchHandler
        
        # Use SuckerPunchHandler for Sucker Punch logic
        if self.name.lower() == 'sucker punch':
            handler = SuckerPunchHandler()
            return handler.get_effective_priority(target_move)
        
        # Fallback to original logic for other priority counters
        # If this is a priority counter and it can counter the target move,
        # it gets its counter priority
        if self.can_counter_move(target_move):
            if self.priority_counter_conditions:
                return self.priority_counter_conditions.get('priority_when_successful', self.priority)
        
        # If it can't counter, it might fail entirely (handled elsewhere)
        return self.priority

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
    
    def _calculate_heal_amount(self, user, damage_dealt: int = 0) -> int:
        """
        Calculate the amount of HP to heal based on move type.
        
        Args:
            user: The Pokemon using the healing move
            damage_dealt: Amount of damage dealt (for HP-draining moves)
            
        Returns:
            int: Amount of HP to heal (0 if no healing should occur)
        """
        try:
            # Validate inputs
            if not user or not hasattr(user, 'max_hp'):
                print(f"ERROR: Invalid user Pokemon for healing calculation")
                return 0
            
            if damage_dealt < 0:
                print(f"WARNING: Negative damage_dealt ({damage_dealt}) provided, using 0")
                damage_dealt = 0
            
            # Check if this is actually a healing move
            if not self.is_healing_move:
                return 0
            
            # Handle direct healing moves (heal property)
            if self.heal_amount is not None:
                try:
                    if not isinstance(self.heal_amount, list) or len(self.heal_amount) != 2:
                        print(f"ERROR: Invalid heal_amount format for {self.name}: {self.heal_amount}")
                        return 0
                    
                    numerator, denominator = self.heal_amount
                    if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
                        print(f"ERROR: Non-numeric heal_amount values for {self.name}: {self.heal_amount}")
                        return 0
                    
                    if denominator == 0:
                        print(f"ERROR: Zero denominator in heal_amount for {self.name}")
                        return 0
                    
                    # Calculate healing as fraction of max HP
                    heal_fraction = numerator / denominator
                    heal_amount = int(user.max_hp * heal_fraction)
                    
                    # Ensure healing amount is at least 1 if fraction is positive
                    if heal_fraction > 0 and heal_amount == 0:
                        heal_amount = 1
                    
                    return max(0, heal_amount)
                    
                except (TypeError, ValueError, ZeroDivisionError) as e:
                    print(f"ERROR: Failed to calculate direct healing for {self.name}: {e}")
                    return 0
            
            # Handle HP-draining moves (drain property)
            elif self.drain_ratio is not None:
                try:
                    if not isinstance(self.drain_ratio, list) or len(self.drain_ratio) != 2:
                        print(f"ERROR: Invalid drain_ratio format for {self.name}: {self.drain_ratio}")
                        return 0
                    
                    numerator, denominator = self.drain_ratio
                    if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
                        print(f"ERROR: Non-numeric drain_ratio values for {self.name}: {self.drain_ratio}")
                        return 0
                    
                    if denominator == 0:
                        print(f"ERROR: Zero denominator in drain_ratio for {self.name}")
                        return 0
                    
                    # Only heal if damage was actually dealt
                    if damage_dealt <= 0:
                        return 0
                    
                    # Calculate healing as fraction of damage dealt
                    drain_fraction = numerator / denominator
                    heal_amount = int(damage_dealt * drain_fraction)
                    
                    # Ensure healing amount is at least 1 if fraction is positive and damage was dealt
                    if drain_fraction > 0 and damage_dealt > 0 and heal_amount == 0:
                        heal_amount = 1
                    
                    return max(0, heal_amount)
                    
                except (TypeError, ValueError, ZeroDivisionError) as e:
                    print(f"ERROR: Failed to calculate drain healing for {self.name}: {e}")
                    return 0
            
            # If marked as healing move but no heal_amount or drain_ratio, return 0
            else:
                print(f"WARNING: {self.name} marked as healing move but no heal_amount or drain_ratio found")
                return 0
                
        except Exception as e:
            print(f"ERROR: Unexpected error in _calculate_heal_amount for {self.name}: {e}")
            return 0

    def _apply_healing_effects(self, user, target, damage_dealt: int = 0) -> List[str]:
        """
        Apply healing effects and return battle messages.
        
        Args:
            user: The Pokemon using the healing move
            target: The target Pokemon (may be None for self-targeting moves)
            damage_dealt: Amount of damage dealt (for HP-draining moves)
            
        Returns:
            List[str]: List of battle messages describing healing effects
        """
        messages = []
        
        try:
            # Validate inputs
            if not user or not hasattr(user, 'current_hp') or not hasattr(user, 'max_hp'):
                print(f"ERROR: Invalid user Pokemon for healing effects")
                return messages
            
            # Check if this is actually a healing move
            if not self.is_healing_move:
                return messages
            
            # Calculate the amount to heal
            heal_amount = self._calculate_heal_amount(user, damage_dealt)
            
            if heal_amount <= 0:
                # For draining moves that miss or deal no damage, no healing occurs
                if self.drain_ratio is not None and damage_dealt <= 0:
                    return messages  # No message needed for failed draining moves
                
                # For direct healing moves, show message even if no healing occurs
                if self.heal_amount is not None:
                    if user.current_hp >= user.max_hp:
                        messages.append(f"{user.name} is already at full health!")
                    return messages
                
                return messages
            
            # Store HP before healing for message generation
            hp_before = user.current_hp
            
            # Apply healing using Pokemon's heal method
            user.heal(heal_amount)
            
            # Calculate actual healing that occurred (in case of full HP cap)
            actual_heal = user.current_hp - hp_before
            
            # Generate appropriate battle messages
            if actual_heal <= 0:
                # Pokemon was already at full HP
                messages.append(f"{user.name} is already at full health!")
            else:
                # Generate healing message based on move type
                if self.heal_amount is not None:
                    # Direct healing move
                    messages.append(f"{user.name} recovered {actual_heal} HP!")
                elif self.drain_ratio is not None:
                    # HP-draining move
                    messages.append(f"{user.name} drained {actual_heal} HP from {target.name if target else 'the target'}!")
                else:
                    # Generic healing message
                    messages.append(f"{user.name} recovered {actual_heal} HP!")
            
        except Exception as e:
            print(f"ERROR: Failed to apply healing effects for {self.name}: {e}")
            import traceback
            traceback.print_exc()
        
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
            
            # Apply healing effects for status moves (like Recover)
            healing_messages = []
            if attacking_pokemon:
                healing_messages = self._apply_healing_effects(attacking_pokemon, defending_pokemon, 0)
            
            # Combine status and healing messages
            all_messages = status_messages + healing_messages
            combined_message = " ".join(all_messages) if all_messages else None
            return 0, f"{attacking_pokemon.name} used {self.name}!", combined_message
        
        # Handle multi-hit moves
        if self.is_multihit_move:
            return self._use_multihit_move(attacking_pokemon, defending_pokemon)
        
        # If we get here, it's a single-hit damaging move
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
                attack_stat = getattr(attacking_pokemon, 'special_attack', 1)  # Special Attack
                defense_stat = getattr(defending_pokemon, 'special_defense', 1)  # Special Defense
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
        
        # Apply healing effects after damage calculation
        healing_messages = []
        if attacking_pokemon:
            healing_messages = self._apply_healing_effects(attacking_pokemon, defending_pokemon, base_damage)
        
        # Combine status and healing messages
        all_messages = status_messages + healing_messages
        combined_message = " ".join(all_messages) if all_messages else None
        
        return base_damage, effectiveness_message, combined_message
    
    def _use_multihit_move(self, attacking_pokemon, defending_pokemon) -> Tuple[int, str, Optional[str]]:
        """Handle multi-hit moves like Pin Missile, Rock Blast, etc."""
        if not attacking_pokemon or not defending_pokemon:
            return 0, f"{attacking_pokemon.name} used {self.name}!", None
        
        # Determine number of hits
        hit_count = self._determine_hit_count()
        print(f"DEBUG: {self.name} will hit {hit_count} times")
        
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
        
        if effectiveness == 0:
            return 0, "It had no effect...", None
        
        # Determine attack and defense stats based on move category
        if self.category == 'physical':
            attack_stat = getattr(attacking_pokemon, 'attack', 1)
            defense_stat = getattr(defending_pokemon, 'defense', 1)
        else:  # 'special'
            attack_stat = getattr(attacking_pokemon, 'special_attack', 1)
            defense_stat = getattr(defending_pokemon, 'special_defense', 1)
        
        # Calculate damage for each hit
        total_damage = 0
        level = 100
        
        for hit_num in range(1, hit_count + 1):
            # Check accuracy for each hit (some moves check accuracy per hit)
            if not self._check_accuracy():
                print(f"DEBUG: Hit {hit_num} missed!")
                continue
            
            # Calculate base damage for this hit
            damage = ((2 * level / 5 + 2) * self.power * attack_stat / defense_stat) / 50 + 2
            damage = int(damage)
            
            # Apply effectiveness
            damage = int(damage * effectiveness)
            
            # Apply STAB (Same Type Attack Bonus)
            if hasattr(attacking_pokemon, 'types') and attacking_pokemon.types:
                attacker_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in attacking_pokemon.types]
                if move_type in attacker_types:
                    damage = int(damage * 1.5)
            
            # Check for critical hit (6.25% chance by default)
            crit_chance = 1/16
            is_critical = random.random() < crit_chance
            
            if is_critical:
                damage = int(damage * 1.5)
                print(f"DEBUG: Critical hit on hit {hit_num}!")
            
            # Apply random damage variation (85% to 100% of calculated damage)
            damage_multiplier = random.uniform(0.85, 1.0)
            damage = max(1, int(damage * damage_multiplier))
            
            print(f"DEBUG: Hit {hit_num}: {damage} damage")
            total_damage += damage
        
        # Generate effectiveness message
        effectiveness_message = ""
        if effectiveness < 1:
            effectiveness_message = "It's not very effective..."
        elif effectiveness > 1:
            effectiveness_message = "It's super effective!"
        
        # Generate hit count message
        hit_message = f"Hit {hit_count} time{'s' if hit_count != 1 else ''}!"
        
        # Combine messages
        combined_message = f"{hit_message} {effectiveness_message}".strip()
        
        # Apply status effects after damage calculation
        status_messages = []
        if defending_pokemon:
            status_messages = self._apply_status_effects(attacking_pokemon, defending_pokemon)
        
        # Apply healing effects after damage calculation
        healing_messages = []
        if attacking_pokemon:
            healing_messages = self._apply_healing_effects(attacking_pokemon, defending_pokemon, total_damage)
        
        # Combine all messages
        all_messages = status_messages + healing_messages
        if all_messages:
            combined_message = f"{combined_message} {' '.join(all_messages)}"
        
        return total_damage, combined_message, None
    
    def get_multihit_hits(self, attacking_pokemon, defending_pokemon) -> List[Dict[str, Any]]:
        """Get individual hit information for multi-hit moves (for progressive damage display)"""
        if not self.is_multihit_move or not attacking_pokemon or not defending_pokemon:
            return []
        
        # Determine number of hits
        hit_count = self._determine_hit_count()
        
        # Get the move type in lowercase for comparison
        move_type = self.type.lower()
        
        # Get defending Pokémon's types
        if hasattr(defending_pokemon, 'types') and isinstance(defending_pokemon.types, list) and defending_pokemon.types:
            defending_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in defending_pokemon.types]
        else:
            defending_types = [getattr(defending_pokemon, 'type', 'normal').lower()]
        
        # Calculate effectiveness
        effectiveness = 1.0
        for target_type in defending_types:
            type_effectiveness = data_loader.get_type_effectiveness(move_type, target_type)
            effectiveness *= type_effectiveness
        effectiveness = round(effectiveness, 2)
        
        if effectiveness == 0:
            return []
        
        # Determine attack and defense stats
        if self.category == 'physical':
            attack_stat = getattr(attacking_pokemon, 'attack', 1)
            defense_stat = getattr(defending_pokemon, 'defense', 1)
        else:
            attack_stat = getattr(attacking_pokemon, 'special_attack', 1)
            defense_stat = getattr(defending_pokemon, 'special_defense', 1)
        
        # Calculate each hit
        hits = []
        level = 100
        
        for hit_num in range(1, hit_count + 1):
            # Check accuracy for each hit
            if not self._check_accuracy():
                hits.append({
                    'hit_number': hit_num,
                    'damage': 0,
                    'missed': True,
                    'critical': False
                })
                continue
            
            # Calculate base damage for this hit
            damage = ((2 * level / 5 + 2) * self.power * attack_stat / defense_stat) / 50 + 2
            damage = int(damage)
            
            # Apply effectiveness
            damage = int(damage * effectiveness)
            
            # Apply STAB
            if hasattr(attacking_pokemon, 'types') and attacking_pokemon.types:
                attacker_types = [t.lower() if isinstance(t, str) else str(t).lower() for t in attacking_pokemon.types]
                if move_type in attacker_types:
                    damage = int(damage * 1.5)
            
            # Check for critical hit
            crit_chance = 1/16
            is_critical = random.random() < crit_chance
            
            if is_critical:
                damage = int(damage * 1.5)
            
            # Apply random damage variation
            damage_multiplier = random.uniform(0.85, 1.0)
            damage = max(1, int(damage * damage_multiplier))
            
            hits.append({
                'hit_number': hit_num,
                'damage': damage,
                'missed': False,
                'critical': is_critical
            })
        
        return hits
            
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'power': self.power,
            'pp': self.pp,
            'max_pp': self.max_pp,
            'type': self.type,
            'accuracy': self.accuracy,
            'category': self.category,
            'priority': self.priority,
            'status_effect': self.status_effect,  # Keep for backward compatibility
            'primary_status': self.primary_status,
            'secondary_status': self.secondary_status,
            'status_chance': self.status_chance,
            'is_status_move': self.is_status_move,
            'is_healing_move': self.is_healing_move,
            'heal_amount': self.heal_amount,
            'drain_ratio': self.drain_ratio,
            'is_multihit_move': self.is_multihit_move,
            'multihit_data': self.multihit_data,
            'is_priority_counter': self.is_priority_counter,
            'priority_counter_conditions': self.priority_counter_conditions
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
        
        # Restore healing data if available
        if 'is_healing_move' in data:
            move.is_healing_move = data['is_healing_move']
        if 'heal_amount' in data:
            move.heal_amount = data['heal_amount']
        if 'drain_ratio' in data:
            move.drain_ratio = data['drain_ratio']
        
        # Restore multi-hit data if available
        if 'is_multihit_move' in data:
            move.is_multihit_move = data['is_multihit_move']
        if 'multihit_data' in data:
            move.multihit_data = data['multihit_data']
        
        # Restore priority counter data if available
        if 'is_priority_counter' in data:
            move.is_priority_counter = data['is_priority_counter']
        if 'priority_counter_conditions' in data:
            move.priority_counter_conditions = data['priority_counter_conditions']
            
        return move
