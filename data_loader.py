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
    
    def _parse_ts_object(self, content: str, object_name: str) -> Dict[str, Any]:
        # Find the object
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        
        if not match:
            return {}
        
        object_content = match.group(1)
        # Convert TypeScript object to JSON-like format
        try:
            # Replace TypeScript-specific syntax
            object_content = re.sub(r'(\w+):', r'"\1":', object_content)  # Quote keys
            object_content = re.sub(r':\s*([^",{\[\]}\s]+)(?=\s*[,}])', r': "\1"', object_content)  # Quote string values
            object_content = re.sub(r':\s*true\b', ': True', object_content)  # Convert boolean
            object_content = re.sub(r':\s*false\b', ': False', object_content)  # Convert boolean
            object_content = re.sub(r':\s*null\b', ': None', object_content)  # Convert null
            
            # Wrap in braces and parse
            json_content = '{' + object_content + '}'
            return eval(json_content)
        except:
            # Fallback to manual parsing
            return self._manual_parse_object(object_content)
    
    def _manual_parse_object(self, content: str) -> Dict[str, Any]:
        """Manual parsing for complex TypeScript objects."""
        result = {}
        
        # Split by top-level entries
        entries = re.findall(r'(\w+):\s*{([^{}]*(?:{[^{}]*}[^{}]*)*)},?', content)
        
        for key, value in entries:
            try:
                # Parse the inner object
                inner_obj = {}
                # Find key-value pairs
                pairs = re.findall(r'(\w+):\s*([^,}]+)', value)
                for pair_key, pair_value in pairs:
                    pair_value = pair_value.strip()
                    if pair_value.isdigit():
                        inner_obj[pair_key] = int(pair_value)
                    elif pair_value == 'true':
                        inner_obj[pair_key] = True
                    elif pair_value == 'false':
                        inner_obj[pair_key] = False
                    elif pair_value == 'null':
                        inner_obj[pair_key] = None
                    else:
                        inner_obj[pair_key] = pair_value.strip('"\'')
                
                result[key] = inner_obj
            except:
                continue
        
        return result
    
    def _load_moves(self):
        """Load moves data from moves.ts file."""
        try:
            with open('datasets/moves.ts', 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("\n=== STARTING MOVE DATA LOADING ===")
            print(f"Total moves.ts file size: {len(content)} characters")
            
            # Find all move entries using a more precise pattern
            pattern = r'(\w+):\s*{\s*num:\s*(\d+).*?name:\s*"(.*?)".*?type:\s*"(\w+)"'
            print(f"Using regex pattern: {pattern}")
            
            move_entries = list(re.finditer(pattern, content, re.DOTALL))
            print(f"Found {len(move_entries)} move entries in the file")
            
            for idx, match in enumerate(move_entries, 1):
                move_key = match.group(1).lower()
                move_num = int(match.group(2))
                move_name = match.group(3).lower()
                move_type = match.group(4).lower()
                
                # Log every 100th move for progress tracking
                if idx % 100 == 0 or 'hurricane' in move_key or 'hurricane' in move_name:
                    print(f"\nProcessing move {idx}: {move_name} (key: {move_key})")
                    print(f"  Move type from regex: {move_type}")
                
                # Get the full move data block
                move_start = match.start()
                next_brace = content.find('},', move_start) + 1
                if next_brace == 0:  # Handle last move in the file
                    next_brace = content.find('}', move_start) + 1
                move_data = content[move_start:next_brace]
                
                # Log detailed info for Hurricane move
                if 'hurricane' in move_key or 'hurricane' in move_name:
                    print("\n=== HURRICANE MOVE FOUND ===")
                    print(f"Move key: {move_key}")
                    print(f"Move name: {move_name}")
                    print(f"Move type from regex: {move_type}")
                    print(f"Move data block:\n{move_data[:500]}...")  # Print first 500 chars of move data
                
                # Get base power (default to 50 if not found)
                power_match = re.search(r'basePower\s*:\s*(\d+)', move_data)
                base_power = int(power_match.group(1)) if power_match else 50
                
                # Get PP (default to 10 if not found)
                pp_match = re.search(r'pp\s*:\s*(\d+)', move_data)
                pp = int(pp_match.group(1)) if pp_match else 10
                
                # Get accuracy (default to 100 if not found)
                accuracy_match = re.search(r'accuracy\s*:\s*(\d+)', move_data)
                accuracy = int(accuracy_match.group(1)) if accuracy_match else 100
                
                # Get category (Physical, Special, or Status)
                category_match = re.search(r'category\s*:\s*"(\w+)"', move_data)
                category = category_match.group(1).lower() if category_match else 'physical'
                
                # Store by both the move key and the move name for easier lookup
                move_entry = {
                    'name': move_name,
                    'type': move_type,
                    'basePower': base_power,
                    'pp': pp,
                    'accuracy': accuracy,
                    'category': category,
                    'num': move_num
                }
                
                self.moves_data[move_key] = move_entry
                if move_key != move_name:  # Avoid duplicate entries
                    self.moves_data[move_name] = move_entry
                
        except FileNotFoundError:
            print("Warning: moves.ts file not found")
        except Exception as e:
            print(f"Error loading moves data: {e}")
    
    def _load_learnsets(self):
        """Load learnsets data from learnsets.ts file."""
        try:
            with open('datasets/learnsets.ts', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract Pokemon learnset data
            pokemon_pattern = r'(\w+):\s*{\s*learnset:\s*{([^{}]*(?:{[^{}]*}[^{}]*)*)}'
            pokemon_data = re.findall(pokemon_pattern, content)
            
            for pokemon_name, learnset_data in pokemon_data:
                moves = {}
                # Parse individual moves
                move_entries = re.findall(r'(\w+):\s*\[([^\]]+)\]', learnset_data)
                for move_name, learn_methods in move_entries:
                    # Clean up the learn methods
                    methods = [method.strip().strip('"\'') for method in learn_methods.split(',')]
                    moves[move_name] = methods
                
                self.learnsets_data[pokemon_name] = {'learnset': moves}
                
        except FileNotFoundError:
            print("Warning: learnsets.ts file not found")
        except Exception as e:
            print(f"Error loading learnsets data: {e}")
    
    def _load_typechart(self):
        """Load type chart data from typechart.ts file."""
        try:
            with open('datasets/typechart.ts', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # The typechart is already properly formatted in the attachment
            # Extract the TypeChart object
            chart_match = re.search(r'export const TypeChart[^=]*=\s*({.*?});', content, re.DOTALL)
            if chart_match:
                chart_content = chart_match.group(1)
                
                # Parse type effectiveness data
                type_pattern = r'(\w+):\s*{\s*damageTaken:\s*{([^{}]+)}'
                types = re.findall(type_pattern, chart_content)
                
                for type_name, damage_data in types:
                    effectiveness = {}
                    damage_entries = re.findall(r'(\w+):\s*(\d+)', damage_data)
                    for attacking_type, effectiveness_value in damage_entries:
                        effectiveness[attacking_type] = int(effectiveness_value)
                    
                    self.typechart_data[type_name] = {
                        'damageTaken': effectiveness
                    }
                    
        except FileNotFoundError:
            print("Warning: typechart.ts file not found")
        except Exception as e:
            print(f"Error loading typechart data: {e}")
    
    def get_move(self, move_name):
        """Get move data by name."""
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
        """Get available moves for a Pokemon."""
        learnset = self.learnsets_data.get(pokemon_name.lower(), {}).get('learnset', {})
        available_moves = list(learnset.keys())
        
        # Filter moves that exist in our moves database
        valid_moves = [move for move in available_moves if move in self.moves_data]
        
        return valid_moves[:limit]
    
    def get_type_effectiveness(self, attacking_type: str, defending_type: str) -> float:
        """
        Get type effectiveness multiplier.
        
        Args:
            attacking_type: The type of the attacking move
            defending_type: The type of the defending Pokémon
            
        Returns:
            float: Effectiveness multiplier (0.0, 0.5, 1.0, or 2.0)
        """
        if not attacking_type or not defending_type:
            return 1.0
            
        # Convert to title case to match the type chart keys
        attacking_type = attacking_type.title()
        defending_type = defending_type.title()
        
        # Get the defending type's damage taken data
        defending_data = self.typechart_data.get(defending_type.lower(), {})
        damage_taken = defending_data.get('damageTaken', {})
        
        # Get the effectiveness code
        # 0 = normal, 1 = 2x, 2 = 0.5x, 3 = 0x (immune)
        effectiveness_code = damage_taken.get(attacking_type, 0)
        
        # Convert to multiplier
        if effectiveness_code == 0:  # Normal effectiveness (1x)
            return 1.0
        elif effectiveness_code == 1:  # 2x effective
            return 2.0
        elif effectiveness_code == 2:  # 0.5x effective
            return 0.5
        elif effectiveness_code == 3:  # No effect (0x)
            return 0.0
            
        return 1.0  # Default to normal effectiveness
    
    def get_move_power(self, move_name: str) -> int:
        """Get the base power of a move."""
        print(f"\n=== GET MOVE POWER ===")
        print(f"Getting power for move: {move_name}")
        move_data = self.get_move_data(move_name)
        power = move_data.get('basePower', 50) if move_data else 50
        print(f"Power for {move_name}: {power}")
        return power
        
    def get_effectiveness_message(self, effectiveness: float) -> str:
        """Get the appropriate effectiveness message based on the multiplier."""
        if effectiveness == 0:
            return "It had no effect..."
        elif effectiveness < 1:
            return "It's not very effective..."
        elif effectiveness > 1:
            return "It's super effective!"
        return ""
    
    def calculate_effectiveness(self, move_type: str, target_types: list) -> tuple[float, str]:
        """
        Calculate the effectiveness of a move against a target with given types.
        
        Args:
            move_type: The type of the move being used
            target_types: List of types of the target Pokémon
            
        Returns:
            tuple: (effectiveness_multiplier, effectiveness_message)
        """
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
        """Get the type of a move."""
        print(f"\n=== GET MOVE TYPE ===")
        print(f"Getting type for move: {move_name}")
        move_data = self.get_move_data(move_name)
        move_type = move_data.get('type', 'normal') if move_data else 'normal'
        print(f"Move type for {move_name}: {move_type}")
        return move_type

    def get_move_data(self, move_name: str) -> Optional[Dict[str, Any]]:
        """Get move data by name."""
        print(f"\n=== GET MOVE DATA ===")
        print(f"Looking up move: {move_name}")
        move_data = self.get_move(move_name)
        if not move_data:
            print(f"Move not found: {move_name}")
            # Try to find the move by name in the values
            for key, data in self.moves_data.items():
                if data.get('name', '').lower() == move_name.lower():
                    print(f"Found move by name match: {key}")
                    move_data = data
                    break
        return move_data

# Global instance
data_loader = DataLoader()
