import re
import json
from typing import Dict, Any, List, Optional

class DataLoader:
    def __init__(self):
        self.moves_data = {}
        self.learnsets_data = {}
        self.typechart_data = {}
        self._load_all_data()
    
    def _load_all_data(self):
        self._load_moves()
        self._load_learnsets()
        self._load_typechart()
    
    def _extract_status_effect(self, move_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Check for direct status effect
        if 'status' in move_data and move_data['status']:
            return {
                'type': move_data['status'],
                'chance': 100  # If status is directly in move_data, it's 100% chance
            }
            
        # Check for secondary effect
        if 'secondary' in move_data and move_data['secondary'] and 'status' in move_data['secondary']:
            return {
                'type': move_data['secondary']['status'],
                'chance': move_data['secondary'].get('chance', 100)
            }
            
        # Check for secondary effects in secondary array (some moves have multiple effects)
        if 'secondaries' in move_data and move_data['secondaries']:
            for effect in move_data['secondaries']:
                if 'status' in effect:
                    return {
                        'type': effect['status'],
                        'chance': effect.get('chance', 100)
                    }
        
        return None

    def _load_moves(self):
        try:
            with open('datasets/moves.json', 'r', encoding='utf-8') as f:
                moves_data = json.load(f)
            
            print(f"\n=== LOADED {len(moves_data)} MOVES FROM moves.json ===")
            
            for move_key, move_data in moves_data.items():
                move_name = move_data.get('name', '').lower()
                if not move_name:
                    continue
                
                # Extract status effect information
                status_effect = self._extract_status_effect(move_data)
                
                # Create a move entry with all necessary data
                move_entry = {
                    'name': move_name,
                    'type': move_data.get('type', 'normal').lower(),
                    'basePower': int(move_data.get('basePower', 0)),
                    'pp': int(move_data.get('pp', 10)),
                    'accuracy': move_data.get('accuracy', 100),  # Can be True for certain moves
                    'category': move_data.get('category', 'status' if move_data.get('basePower', 0) == 0 else 'physical').lower(),
                    'num': int(move_data.get('num', 0)),
                    'status_effect': status_effect,
                    'is_status_move': move_data.get('category', '').lower() == 'status' or move_data.get('basePower', 0) == 0
                }
                
                # Store by both the move key and the move name for easier lookup
                self.moves_data[move_key.lower()] = move_entry
                if move_key.lower() != move_name.lower():
                    self.moves_data[move_name.lower()] = move_entry
                    
        except FileNotFoundError:
            print("Warning: moves.json file not found")
        except Exception as e:
            print(f"Error loading moves data: {e}")
            raise
    
    def _load_learnsets(self):
        try:
            with open('datasets/learnsets.json', 'r', encoding='utf-8') as f:
                learnsets_data = json.load(f)
            
            print(f"\n=== LOADED LEARNSETS FOR {len(learnsets_data)} POKÉMON ===")
            
            for pokemon_name, data in learnsets_data.items():
                if 'learnset' in data:
                    # Convert move names to lowercase for case-insensitive lookup
                    moves = [move.lower() for move in data['learnset'].keys()]
                    self.learnsets_data[pokemon_name.lower()] = moves
            
        except FileNotFoundError:
            print("Warning: learnsets.json file not found")
        except Exception as e:
            print(f"Error loading learnset data: {e}")
            raise
    
    def _load_typechart(self):
        try:
            with open('datasets/typechart.json', 'r', encoding='utf-8') as f:
                self.typechart_data = json.load(f)
            
            print(f"\n=== LOADED TYPE CHART WITH {len(self.typechart_data)} TYPES ===")
            
        except FileNotFoundError:
            print("Warning: typechart.json file not found")
        except json.JSONDecodeError as e:
            print(f"Error parsing type chart data: {e}")
        except Exception as e:
            print(f"Error loading type chart data: {e}")
            raise
    
    def get_move(self, move_name):
        if not move_name:
            print("\n=== MOVE LOOKUP FAILED ===")
            print("No move name provided")
            return None
            
        move_key = move_name.lower().replace(' ', '').replace('-', '')
        move_data = self.moves_data.get(move_key)
        
        # Log move lookup
        if move_data:
            print(f"\n=== MOVE LOOKUP ===")
            print(f"Requested move: {move_name}")
            print(f"Lookup key: {move_key}")
            print(f"Found move: {move_data.get('name', 'Unknown')}")
            print(f"Move type: {move_data.get('type', 'Unknown')}")
            print(f"Category: {move_data.get('category', 'physical').capitalize()}")
            print(f"Accuracy: {move_data.get('accuracy', 100)}")
            if move_data.get('status_effect'):
                print(f"Status Effect: {move_data['status_effect']['type']} ({move_data['status_effect']['chance']}% chance)")
            print(f"Full move data: {move_data}")
            
            # Log all available keys that contain the move name for debugging
            matching_keys = [k for k in self.moves_data.keys() if move_key in k]
            if len(matching_keys) > 1:
                print(f"Found {len(matching_keys)} matching keys: {matching_keys[:10]}{'...' if len(matching_keys) > 10 else ''}")
        else:
            print(f"\n=== MOVE NOT FOUND ===")
            print(f"Requested move: {move_name}")
            print(f"Lookup key: {move_key}")
            print(f"Available move keys (first 10): {list(self.moves_data.keys())[:10]}")
            
            # Try to find similar move names
            similar_moves = [k for k in self.moves_data.keys() if move_key in k or move_key[:4] in k][:5]
            if similar_moves:
                print(f"Similar moves found: {similar_moves}")
            
        return move_data
    
    def get_pokemon_moves(self, pokemon_name: str, limit: int = 4) -> List[str]:
        pokemon_data = self.learnsets_data.get(pokemon_name.lower(), {})
        
        # Handle case where pokemon_data might be a list instead of dict
        if isinstance(pokemon_data, list):
            # If it's a list, assume it's the moves list directly
            available_moves = pokemon_data
        elif isinstance(pokemon_data, dict):
            # If it's a dict, get the learnset
            learnset = pokemon_data.get('learnset', {})
            available_moves = list(learnset.keys()) if isinstance(learnset, dict) else []
        else:
            available_moves = []
        
        # Filter moves that exist in our moves database
        valid_moves = [move for move in available_moves if move in self.moves_data]
        
        return valid_moves[:limit]
    
    def get_type_effectiveness(self, attacking_type: str, defending_type: str) -> float:
        if not attacking_type or not defending_type:
            print(f"\n=== TYPE EFFECTIVENESS DEBUG ===")
            print(f"Missing type data - attacking: {attacking_type}, defending: {defending_type}")
            return 1.0
            
        # Store original types for logging
        original_attacking = attacking_type
        original_defending = defending_type
        
        # Convert to title case to match the type chart keys
        attacking_type = attacking_type.title()
        defending_type = defending_type.title()
        
        print(f"\n=== TYPE EFFECTIVENESS DEBUG ===")
        print(f"Original types - attacking: {original_attacking}, defending: {original_defending}")
        print(f"Formatted types - attacking: {attacking_type}, defending: {defending_type}")
        
        # Get the defending type's damage taken data (FIXED: use title case)
        defending_data = self.typechart_data.get(defending_type, {})
        damage_taken = defending_data.get('damageTaken', {})
        
        print(f"Defending type data found: {defending_type in self.typechart_data}")
        print(f"Available types in typechart: {list(self.typechart_data.keys())[:10]}...")
        
        # Get the effectiveness code
        effectiveness_code = damage_taken.get(attacking_type, 0)
        
        print(f"Effectiveness code for {attacking_type} vs {defending_type}: {effectiveness_code}")
        
        # Convert to multiplier
        multiplier = 1.0
        if effectiveness_code == 0:  # Normal effectiveness (1x)
            multiplier = 1.0
        elif effectiveness_code == 1:  # 2x effective
            multiplier = 2.0
        elif effectiveness_code == 2:  # 0.5x effective
            multiplier = 0.5
        elif effectiveness_code == 3:  # No effect (0x)
            multiplier = 0.0
        
        print(f"Final effectiveness multiplier: {multiplier}")
        print("=== END TYPE EFFECTIVENESS DEBUG ===\n")
            
        return multiplier
    
    def get_move_power(self, move_name: str) -> int:
        print(f"\n=== GET MOVE POWER ===")
        print(f"Getting power for move: {move_name}")
        move_data = self.get_move_data(move_name)
        power = move_data.get('basePower', 50) if move_data else 50
        print(f"Power for {move_name}: {power}")
        return power
        
    def get_effectiveness_message(self, effectiveness: float) -> str:
        if effectiveness == 0:
            return "It had no effect..."
        elif effectiveness < 1:
            return "It's not very effective..."
        elif effectiveness > 1:
            return "It's super effective!"
        return ""
    
    def calculate_effectiveness(self, move_type: str, target_types: list) -> tuple[float, str]:
        if not move_type or not target_types:
            return 1.0, ""
            
        effectiveness = 1.0
        
        for target_type in target_types:
            effectiveness *= self.get_type_effectiveness(move_type, target_type)
        
        # Round to avoid floating point precision issues (e.g., 0.9999 -> 1.0)
        effectiveness = round(effectiveness, 2)
        
        # Get the appropriate message
        if effectiveness == 0:
            message = "It had no effect..."
        elif effectiveness < 1:
            message = "It's not very effective..."
        elif effectiveness > 1:
            message = "It's super effective!"
        else:
            message = ""
            
        return effectiveness, message
    
    def get_move_type(self, move_name: str) -> str:
        move_data = self.get_move_data(move_name)
        return move_data.get('type', 'normal').lower() if move_data else 'normal'
        
    def get_move_data(self, move_name: str) -> Optional[Dict[str, Any]]:
        if not move_name:
            return None
            
        # Try to find the move by exact key first
        move_key = move_name.lower().replace(' ', '').replace('-', '')
        
        # Check if the move exists in our data
        if move_key in self.moves_data:
            return self.moves_data[move_key]
            
        # If not found, try to find by name in the values
        for key, data in self.moves_data.items():
            if data.get('name', '').lower() == move_name.lower():
                return data
                
        # If still not found, try a partial match
        for key, data in self.moves_data.items():
            if move_name.lower() in key.lower() or move_name.lower() in data.get('name', '').lower():
                return data
                
        return None

# Global instance
data_loader = DataLoader()
