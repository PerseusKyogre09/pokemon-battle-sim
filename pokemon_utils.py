"""
Pokemon utility functions for enhanced battle mechanics using TypeScript datasets.
"""

from data_loader import data_loader
import random
from typing import List, Dict, Any, Tuple

class PokemonUtils:
    """Utility class for Pokemon-related operations."""
    
    @staticmethod
    def get_effective_pokemon_moves(pokemon_name: str, level: int = 100, count: int = 4) -> List[Dict[str, Any]]:
        """
        Get the most effective moves for a Pokemon based on level and power.
        
        Args:
            pokemon_name: Name of the Pokemon
            level: Level of the Pokemon (affects move availability)
            count: Number of moves to return
            
        Returns:
            List of move dictionaries with enhanced data
        """
        available_moves = data_loader.get_pokemon_moves(pokemon_name.lower(), 20)  # Get more moves to filter
        
        if not available_moves:
            # Fallback to basic moves if not found in dataset
            return [
                {'name': 'tackle', 'power': 40, 'type': 'Normal', 'accuracy': 100, 'pp': 35},
                {'name': 'growl', 'power': 0, 'type': 'Normal', 'accuracy': 100, 'pp': 40},
                {'name': 'scratch', 'power': 40, 'type': 'Normal', 'accuracy': 100, 'pp': 35},
                {'name': 'leer', 'power': 0, 'type': 'Normal', 'accuracy': 100, 'pp': 30}
            ][:count]
        
        enhanced_moves = []
        for move_name in available_moves:
            move_data = data_loader.get_move_data(move_name)
            if move_data:
                enhanced_moves.append({
                    'name': move_name,
                    'power': move_data.get('basePower', 50),
                    'type': move_data.get('type', 'Normal'),
                    'accuracy': move_data.get('accuracy', 100),
                    'pp': move_data.get('pp', 20),
                    'category': move_data.get('category', 'Physical'),
                    'priority': move_data.get('priority', 0)
                })
        
        # Sort by power (descending) and take the most powerful moves
        enhanced_moves.sort(key=lambda x: x['power'] if x['power'] else 0, reverse=True)
        
        # Ensure we have a good mix of moves (not all status moves)
        offensive_moves = [m for m in enhanced_moves if m['power'] > 0]
        status_moves = [m for m in enhanced_moves if m['power'] == 0]
        
        # Take mostly offensive moves with maybe one status move
        result = offensive_moves[:count-1] if len(offensive_moves) >= count-1 else offensive_moves
        if len(result) < count and status_moves:
            result.extend(status_moves[:count-len(result)])
        
        # Fill remaining slots if needed
        while len(result) < count:
            result.append({
                'name': 'struggle',
                'power': 50,
                'type': 'Normal',
                'accuracy': 100,
                'pp': 1
            })
        
        return result[:count]
    
    @staticmethod
    def calculate_damage(attacker_level: int, attacker_attack: int, defender_defense: int, 
                        move_power: int, type_effectiveness: float, stab: bool = False) -> int:
        """
        Calculate damage using a simplified Pokemon damage formula.
        
        Args:
            attacker_level: Level of attacking Pokemon
            attacker_attack: Attack stat of attacking Pokemon
            defender_defense: Defense stat of defending Pokemon
            move_power: Base power of the move
            type_effectiveness: Type effectiveness multiplier
            stab: Same Type Attack Bonus
            
        Returns:
            Calculated damage
        """
        if move_power <= 0:
            return 0
        
        # Simplified damage formula based on Pokemon games
        base_damage = ((((2 * attacker_level / 5 + 2) * move_power * attacker_attack / defender_defense) / 50) + 2)
        
        # Apply STAB (Same Type Attack Bonus)
        if stab:
            base_damage *= 1.5
        
        # Apply type effectiveness
        base_damage *= type_effectiveness
        
        # Add random factor (85-100% of calculated damage)
        random_factor = random.uniform(0.85, 1.0)
        final_damage = int(base_damage * random_factor)
        
        return max(1, final_damage)  # Minimum 1 damage
    
    @staticmethod
    def get_ai_move_choice(pokemon_moves: Dict[str, Any], opponent_type: str) -> str:
        """
        Simple AI for choosing moves based on type effectiveness.
        
        Args:
            pokemon_moves: Dictionary of available moves
            opponent_type: Type of the opponent Pokemon
            
        Returns:
            Name of the chosen move
        """
        if not pokemon_moves:
            return 'struggle'
        
        move_scores = {}
        for move_name, move_obj in pokemon_moves.items():
            move_type = getattr(move_obj, 'type', 'Normal')
            effectiveness = data_loader.get_type_effectiveness(move_type, opponent_type)
            power = getattr(move_obj, 'power', 50)
            
            # Score based on power and effectiveness
            score = power * effectiveness
            move_scores[move_name] = score
        
        # Choose the highest scoring move, with some randomness
        if random.random() < 0.8:  # 80% chance to pick best move
            best_move = max(move_scores, key=move_scores.get)
        else:  # 20% chance for random move
            best_move = random.choice(list(pokemon_moves.keys()))
        
        return best_move
    
    @staticmethod
    def get_type_advantages(pokemon_type: str) -> Dict[str, List[str]]:
        """
        Get what types this Pokemon is strong/weak against.
        
        Args:
            pokemon_type: Type of the Pokemon
            
        Returns:
            Dictionary with 'strong_against' and 'weak_against' lists
        """
        strong_against = []
        weak_against = []
        
        # Check against all types
        all_types = ['Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice', 'Fighting',
                    'Poison', 'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost',
                    'Dragon', 'Dark', 'Steel', 'Fairy']
        
        for defending_type in all_types:
            effectiveness = data_loader.get_type_effectiveness(pokemon_type, defending_type)
            if effectiveness > 1.0:
                strong_against.append(defending_type)
            elif effectiveness < 1.0 and effectiveness > 0:
                weak_against.append(defending_type)
        
        return {
            'strong_against': strong_against,
            'weak_against': weak_against
        }
    
    @staticmethod
    def get_random_pokemon_with_moves(level: int = 100) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Get a random Pokemon with appropriate moves.
        
        Args:
            level: Level of the Pokemon
            
        Returns:
            Tuple of (pokemon_name, moves_list)
        """
        # List of common Pokemon that should be in our dataset
        common_pokemon = [
            'pikachu', 'charmander', 'squirtle', 'bulbasaur', 'caterpie', 'weedle',
            'pidgey', 'rattata', 'spearow', 'ekans', 'sandshrew', 'nidoran-f',
            'nidoran-m', 'clefairy', 'vulpix', 'jigglypuff', 'zubat', 'oddish',
            'paras', 'venonat', 'diglett', 'meowth', 'psyduck', 'mankey',
            'growlithe', 'poliwag', 'abra', 'machop', 'bellsprout', 'tentacool'
        ]
        
        pokemon_name = random.choice(common_pokemon)
        moves = PokemonUtils.get_effective_pokemon_moves(pokemon_name, level, 4)
        
        return pokemon_name, moves

# Create a global utility instance
pokemon_utils = PokemonUtils()
