from data_loader import data_loader
from typing import Optional, Tuple, Dict, Any, Union, List
import random

class Move:
    def __init__(self, name: str, move_data: Optional[Dict[str, Any]] = None):
        self.name = name
        self.data = move_data if move_data else data_loader.get_move(name)
        
        if not self.data:
            self.power = 0
            self.pp = 10
            self.max_pp = 10
            self.type = 'normal'
            self.accuracy = 100
            self.category = 'physical'
            self.priority = 0
            self.is_status_move = True
        else:
            self.power = self.data.get('basePower', 0)
            self.pp = self.data.get('pp', 10)
            self.max_pp = self.pp
            self.type = self.data.get('type', 'normal').lower()
            self.accuracy = self.data.get('accuracy', 100)
            self.category = self.data.get('category', 'physical').lower()
            self.priority = self.data.get('priority', 0)
            self.is_status_move = self.category == 'status' or self.power == 0
        
        self.is_healing_move, self.heal_amount, self.drain_ratio = self._parse_healing_data()
        self.is_multihit_move, self.multihit_data = self._parse_multihit_data()
        self.stat_modifications, self.targets_self = self._parse_stat_modifications()
        self.is_recoil_move, self.recoil_ratio = self._parse_recoil_data()

    
    def _parse_healing_data(self) -> Tuple[bool, Optional[List[int]], Optional[List[int]]]:
        if not self.data:
            return False, None, None
        
        is_healing = False
        heal_amount = None
        drain_ratio = None
        
        if 'heal' in self.data and isinstance(self.data['heal'], list):
            is_healing = True
            heal_amount = self.data['heal']
        
        if 'drain' in self.data and isinstance(self.data['drain'], list):
            is_healing = True
            drain_ratio = self.data['drain']
        
        if 'flags' in self.data and isinstance(self.data['flags'], dict):
            if self.data['flags'].get('heal') == 1:
                is_healing = True
        
        return is_healing, heal_amount, drain_ratio
    
    def _parse_multihit_data(self) -> Tuple[bool, Optional[Union[int, List[int]]]]:
        if not self.data:
            return False, None
        
        if 'multihit' in self.data:
            multihit_data = self.data['multihit']
            if isinstance(multihit_data, int):
                return True, multihit_data
            elif isinstance(multihit_data, list) and len(multihit_data) == 2:
                return True, multihit_data
            elif multihit_data is not None:
                return False, None
        
        return False, None
    
    def _apply_boosts(self, pokemon, boosts: Dict[str, int]) -> List[str]:
        if not boosts or not pokemon:
            return []
            
        stat_name_mapping = {
            'atk': 'attack',
            'def': 'defense',
            'spa': 'special_attack',
            'spd': 'special_defense',
            'spe': 'speed',
            'accuracy': 'accuracy',
            'evasion': 'evasion'
        }
        
        messages = []
        for stat_abbrev, stages in boosts.items():
            full_stat_name = stat_name_mapping.get(stat_abbrev)
            if full_stat_name and hasattr(pokemon, 'change_stat_stage'):
                msg = pokemon.change_stat_stage(full_stat_name, stages)
                if msg:
                    messages.append(msg)
                    
        return messages

    def _parse_stat_modifications(self) -> Tuple[Optional[Dict[str, int]], bool]:
        if not self.data:
            return None, False
        
        stat_modifications = self.data.get('boosts')
        targets_self = False
        
        if 'target' in self.data:
            target = self.data['target']
            if target in ['self']:
                targets_self = True
        
        return stat_modifications, targets_self
    
    def _parse_recoil_data(self) -> Tuple[bool, Optional[List[int]]]:
        if not self.data:
            return False, None
        
        if 'recoil' in self.data and isinstance(self.data['recoil'], list):
            recoil_data = self.data['recoil']
            if len(recoil_data) == 2 and all(isinstance(x, (int, float)) for x in recoil_data):
                return True, recoil_data
            else:
                return False, None
        
        return False, None
    
    def _determine_hit_count(self) -> int:
        if not self.is_multihit_move or not self.multihit_data:
            return 1
        
        if isinstance(self.multihit_data, int):
            return self.multihit_data
        elif isinstance(self.multihit_data, list) and len(self.multihit_data) == 2:
            min_hits, max_hits = self.multihit_data
            
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
                return random.randint(min_hits, max_hits)
        
        return 1
    
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


    def _check_accuracy(self) -> bool:
        if self.accuracy is True:  # Moves that never miss (e.g., Aerial Ace)
            return True
            
        if isinstance(self.accuracy, (int, float)):
            return random.randint(1, 100) <= self.accuracy
            
        return True  # Default to True if accuracy is somehow invalid

    def _apply_effect_block(self, target, effect_block: Dict[str, Any], chance_override: Optional[int] = None) -> List[str]:
        """Apply an effect block (secondary or self) to a target Pokemon."""
        if not effect_block or not target:
            return []
            
        chance = chance_override if chance_override is not None else effect_block.get('chance', 100)
        if random.randint(1, 100) > chance:
            return []
            
        messages = []
        
        # 1. Apply Status
        if 'status' in effect_block:
            status_type = effect_block['status']
            msg = target.apply_status_effect(status_type)
            if msg:
                messages.append(msg)
                
        # 2. Apply Volatile Status
        if 'volatileStatus' in effect_block:
            v_status = effect_block['volatileStatus']
            if hasattr(target, 'apply_volatile_status'):
                msg = target.apply_volatile_status(v_status)
                if msg:
                    messages.append(msg)
                
        # 3. Apply Boosts
        if 'boosts' in effect_block:
            boost_msgs = self._apply_boosts(target, effect_block['boosts'])
            messages.extend(boost_msgs)
            
        return messages

    def _apply_secondary_effects(self, user, target) -> List[str]:
        """Apply secondary effects of the move (chance-based on target)."""
        messages = []
        
        # Handle 'secondary' field (standard)
        if 'secondary' in self.data and self.data['secondary']:
            msgs = self._apply_effect_block(target, self.data['secondary'])
            messages.extend(msgs)
            
        # Handle 'secondaries' field (multiple possible effects)
        if 'secondaries' in self.data and self.data['secondaries']:
            for effect in self.data['secondaries']:
                msgs = self._apply_effect_block(target, effect)
                messages.extend(msgs)
                
        return messages

    def _apply_self_effects(self, user, target) -> List[str]:
        """Apply effects on the user (like stat drops after Overheat)."""
        messages = []
        
        # Handle 'self' field
        if 'self' in self.data and self.data['self']:
            msgs = self._apply_effect_block(user, self.data['self'])
            messages.extend(msgs)
            
        # Also handle standard 'boosts' if they target self (parsed in __init__)
        if self.stat_modifications and self.targets_self:
            boost_msgs = self._apply_boosts(user, self.stat_modifications)
            messages.extend(boost_msgs)
            
        return messages

    def _apply_status_effects(self, user, target) -> List[str]:
        """Apply primary status effects for status moves."""
        if not self.is_status_move or not self.data or not target:
            return []
            
        messages = []
        
        # Status moves usually have 'status' directly in move_data
        if 'status' in self.data:
            msg = target.apply_status_effect(self.data['status'])
            if msg:
                messages.append(msg)
                    
        # Also apply any secondary effects that status moves might have
        secondary_msgs = self._apply_secondary_effects(user, target)
        messages.extend(secondary_msgs)
            
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

    def _calculate_recoil_damage(self, user, damage_dealt: int) -> int:
        """
        Calculate the amount of recoil damage the user should take.
        
        Args:
            user: The Pokemon using the recoil move
            damage_dealt: Amount of damage dealt to the target
            
        Returns:
            int: Amount of recoil damage to apply (0 if no recoil should occur)
        """
        try:
            # Validate inputs
            if not user or not hasattr(user, 'max_hp'):
                print(f"ERROR: Invalid user Pokemon for recoil calculation")
                return 0
            
            if damage_dealt <= 0:
                # No recoil if no damage was dealt
                return 0
            
            # Check if this is actually a recoil move
            if not self.is_recoil_move or not self.recoil_ratio:
                return 0
            
            # Validate recoil ratio format
            if not isinstance(self.recoil_ratio, list) or len(self.recoil_ratio) != 2:
                print(f"ERROR: Invalid recoil_ratio format for {self.name}: {self.recoil_ratio}")
                return 0
            
            numerator, denominator = self.recoil_ratio
            if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
                print(f"ERROR: Non-numeric recoil_ratio values for {self.name}: {self.recoil_ratio}")
                return 0
            
            if denominator == 0:
                print(f"ERROR: Zero denominator in recoil_ratio for {self.name}")
                return 0
            
            # Calculate recoil as fraction of damage dealt
            recoil_fraction = numerator / denominator
            recoil_damage = int(damage_dealt * recoil_fraction)
            
            # Ensure recoil damage is at least 1 if fraction is positive and damage was dealt
            if recoil_fraction > 0 and damage_dealt > 0 and recoil_damage == 0:
                recoil_damage = 1
            
            return max(0, recoil_damage)
            
        except Exception as e:
            print(f"ERROR: Unexpected error in _calculate_recoil_damage for {self.name}: {e}")
            return 0

    def _apply_recoil_effects(self, user, damage_dealt: int) -> List[str]:
        """
        Apply recoil effects and return battle messages.
        
        Args:
            user: The Pokemon using the recoil move
            damage_dealt: Amount of damage dealt to the target
            
        Returns:
            List[str]: List of battle messages describing recoil effects
        """
        messages = []
        
        try:
            # Validate inputs
            if not user or not hasattr(user, 'current_hp') or not hasattr(user, 'max_hp'):
                print(f"ERROR: Invalid user Pokemon for recoil effects")
                return messages
            
            # Check if this is actually a recoil move
            if not self.is_recoil_move:
                return messages
            
            # Calculate the amount of recoil damage
            recoil_damage = self._calculate_recoil_damage(user, damage_dealt)
            
            if recoil_damage <= 0:
                return messages
            
            # Apply recoil damage using Pokemon's take_damage method
            user.take_damage(recoil_damage)
            
            # Generate recoil message
            messages.append(f"{user.name} is hurt by recoil!")
            
        except Exception as e:
            print(f"ERROR: Failed to apply recoil effects for {self.name}: {e}")
            import traceback
            traceback.print_exc()
        
        return messages

    def _handle_special_moves(self, attacking_pokemon, defending_pokemon):
        """Handle special moves with unique mechanics like Belly Drum."""
        move_name_lower = self.name.lower()
        
        # Handle Belly Drum
        if move_name_lower == 'belly drum':
            return self._handle_belly_drum(attacking_pokemon)
        
        # Add other special moves here as needed
        # elif move_name_lower == 'other_special_move':
        #     return self._handle_other_special_move(attacking_pokemon, defending_pokemon)
        
        return None  # No special handling needed
    
    def _handle_belly_drum(self, user):
        """Handle Belly Drum: Maximize Attack at the cost of 50% max HP."""
        # Check if Attack is already at maximum (+6)
        if user.stat_stages.get('attack', 0) >= 6:
            return 0, f"{user.name} used {self.name}!", f"{user.name}'s Attack won't go any higher!"
        
        # Calculate HP cost (50% of max HP, rounded down)
        hp_cost = user.max_hp // 2
        
        # Check if user has enough HP (must have more than 50% to use)
        if user.current_hp <= hp_cost:
            return 0, f"{user.name} used {self.name}!", f"But it failed!"
        
        # Apply the effects
        # 1. Reduce HP by 50%
        user.current_hp -= hp_cost
        
        # 2. Set Attack to maximum (+6 stages)
        old_attack_stage = user.stat_stages.get('attack', 0)
        user.stat_stages['attack'] = 6
        user._recalculate_stats()  # Recalculate stats with new stage
        
        # Generate the message
        move_desc = data_loader.get_move_description(self.name)
        if move_desc and 'boost' in move_desc:
            # Use the official message from the dataset
            boost_message = move_desc['boost'].replace('[POKEMON]', user.name)
        else:
            # Fallback message
            boost_message = f"{user.name} cut its own HP and maximized its Attack!"
        
        return 0, f"{user.name} used {self.name}!", boost_message

    def _apply_stat_modifications(self, user, target) -> List[str]:
        """
        Apply stat modifications to appropriate targets and return battle messages.
        
        Args:
            user: The Pokemon using the move
            target: The target Pokemon (may be None for self-targeting moves)
            
        Returns:
            List[str]: List of battle messages describing stat modifications
        """
        messages = []
        
        try:
            # Check if this move has stat modifications
            if not self.stat_modifications or not isinstance(self.stat_modifications, dict):
                return messages
            
            # Determine the target Pokemon for stat modifications
            if self.targets_self:
                modification_target = user
            else:
                modification_target = target
            
            # Validate that we have a valid target
            if not modification_target or not hasattr(modification_target, 'modify_stat_stage'):
                return messages
            
            # Apply each stat modification
            for stat_name, change in self.stat_modifications.items():
                if isinstance(change, int) and change != 0:
                    # Apply the stat stage change and get the result message
                    message = modification_target.modify_stat_stage(stat_name, change)
                    if message:  # Only add non-empty messages
                        messages.append(message)
            
        except Exception as e:
            print(f"ERROR: Failed to apply stat modifications for {self.name}: {e}")
            import traceback
            traceback.print_exc()
        
        return messages


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
            # Check for special moves first (like Belly Drum)
            special_move_result = self._handle_special_moves(attacking_pokemon, defending_pokemon)
            if special_move_result:
                return special_move_result
            
            status_messages = []
            if defending_pokemon:
                status_messages = self._apply_status_effects(attacking_pokemon, defending_pokemon)
            
            # Apply healing effects for status moves (like Recover)
            healing_messages = []
            if attacking_pokemon:
                healing_messages = self._apply_healing_effects(attacking_pokemon, defending_pokemon, 0)
            
            # Apply stat modifications for status moves
            stat_modification_messages = []
            if self.stat_modifications:
                stat_modification_messages = self._apply_stat_modifications(attacking_pokemon, defending_pokemon)
            
            # Combine status, healing, and stat modification messages
            all_messages = status_messages + healing_messages + stat_modification_messages
            combined_message = " ".join(all_messages) if all_messages else None
            return 0, "", combined_message
        
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
            # Calculate effectiveness against each of the target's types
            effectiveness = 1.0
            
            for target_type in defending_types:
                effectiveness *= data_loader.get_type_effectiveness(move_type, target_type)
                
            effectiveness = round(effectiveness, 2)
            
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
            
            # Check for critical hit
            crit_ratio = self.data.get('critRatio', 1)
            will_crit = self.data.get('willCrit', False)
            
            crit_chances = {1: 1/16, 2: 1/8, 3: 1/2, 4: 1.0}
            crit_chance = crit_chances.get(crit_ratio, 1.0) if crit_ratio in crit_chances else (1.0 if crit_ratio > 4 else 1/16)
            
            is_critical = will_crit or random.random() < crit_chance
            
            if is_critical:
                damage = int(damage * 1.5)
                if effectiveness_message:
                    effectiveness_message = "A critical hit! " + effectiveness_message
                else:
                    effectiveness_message = "A critical hit!"
            
            damage_multiplier = random.uniform(0.85, 1.0)
            damage = max(1, int(damage * damage_multiplier))
            
            base_damage = damage
        
        # Apply status effects after damage calculation
        # Apply secondary effects, self effects, healing, and recoil
        secondary_messages = []
        self_messages = []
        healing_messages = []
        recoil_messages = []
        
        if defending_pokemon and not self.is_status_move:
            secondary_messages = self._apply_secondary_effects(attacking_pokemon, defending_pokemon)
            
        if attacking_pokemon:
            # Self-effects (stat drops/boosts on user)
            self_messages = self._apply_self_effects(attacking_pokemon, defending_pokemon)
            
            # Healing/Drain effects
            healing_messages = self._apply_healing_effects(attacking_pokemon, defending_pokemon, base_damage)
            
            # Recoil effects
            recoil_messages = self._apply_recoil_effects(attacking_pokemon, base_damage)
        
        # Apply legacy status effects for status moves
        status_messages = []
        if self.is_status_move and defending_pokemon:
            status_messages = self._apply_status_effects(attacking_pokemon, defending_pokemon)
        
        # Combine all messages
        all_messages = status_messages + secondary_messages + self_messages + healing_messages + recoil_messages
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
            
            # Check for critical hit
            crit_ratio = self.data.get('critRatio', 1)
            will_crit = self.data.get('willCrit', False)
            
            crit_chances = {1: 1/16, 2: 1/8, 3: 1/2, 4: 1.0}
            crit_chance = crit_chances.get(crit_ratio, 1.0) if crit_ratio in crit_chances else (1.0 if crit_ratio > 4 else 1/16)
            
            is_critical = will_crit or random.random() < crit_chance
            
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
        
        # Apply secondary effects, self effects, healing, and recoil
        secondary_messages = []
        self_messages = []
        healing_messages = []
        recoil_messages = []
        
        if defending_pokemon:
            secondary_messages = self._apply_secondary_effects(attacking_pokemon, defending_pokemon)
            
        if attacking_pokemon:
            self_messages = self._apply_self_effects(attacking_pokemon, defending_pokemon)
            healing_messages = self._apply_healing_effects(attacking_pokemon, defending_pokemon, total_damage)
            recoil_messages = self._apply_recoil_effects(attacking_pokemon, total_damage)
        
        # Combine all messages
        all_messages = secondary_messages + self_messages + healing_messages + recoil_messages
        if all_messages:
            combined_message = f"{combined_message} {' '.join(all_messages)}".strip()
        
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
            'is_status_move': self.is_status_move,
            'is_healing_move': self.is_healing_move,
            'heal_amount': self.heal_amount,
            'drain_ratio': self.drain_ratio,
            'is_multihit_move': self.is_multihit_move,
            'multihit_data': self.multihit_data,
            'stat_modifications': self.stat_modifications,
            'targets_self': self.targets_self
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Move':
        # Create move using the new data-driven constructor
        move = cls(name=data['name'])
        
        # Override fields that might have been changed/saved
        move.pp = data.get('pp', move.pp)
        move.max_pp = data.get('max_pp', move.max_pp)
        
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
        
        # Restore stat modification data if available
        if 'stat_modifications' in data:
            move.stat_modifications = data['stat_modifications']
        if 'targets_self' in data:
            move.targets_self = data['targets_self']
            
        return move
