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
            
            # Find all move entries
            move_entries = re.finditer(r'(\w+):\s*{\s*num:\s*(\d+).*?type:\s*"(\w+)"', content, re.DOTALL)
            
            for match in move_entries:
                move_name = match.group(1).lower()
                move_num = int(match.group(2))
                move_type = match.group(3)
                
                # Extract other properties with a more targeted approach
                move_data = match.group(0)
                
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
                category = category_match.group(1) if category_match else 'Physical'
                
                self.moves_data[move_name] = {
                    'name': move_name,
                    'type': move_type,
                    'basePower': base_power,
                    'pp': pp,
                    'accuracy': accuracy,
                    'category': category,
                    'num': move_num
                }
                
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
    
    def get_move_data(self, move_name: str) -> Optional[Dict[str, Any]]:
        """Get move data by name."""
        return self.moves_data.get(move_name.lower().replace(' ', '').replace('-', ''))
    
    def get_pokemon_moves(self, pokemon_name: str, limit: int = 4) -> List[str]:
        """Get available moves for a Pokemon."""
        learnset = self.learnsets_data.get(pokemon_name.lower(), {}).get('learnset', {})
        available_moves = list(learnset.keys())
        
        # Filter moves that exist in our moves database
        valid_moves = [move for move in available_moves if move in self.moves_data]
        
        return valid_moves[:limit]
    
    def get_type_effectiveness(self, attacking_type: str, defending_type: str) -> float:
        """Get type effectiveness multiplier."""
        defending_data = self.typechart_data.get(defending_type.lower(), {})
        damage_taken = defending_data.get('damageTaken', {})
        effectiveness_code = damage_taken.get(attacking_type.title(), 0)
        
        # Convert effectiveness codes to multipliers
        # 0 = 1x, 1 = 2x, 2 = 0.5x, 3 = 0x (immune)
        multipliers = {0: 1.0, 1: 2.0, 2: 0.5, 3: 0.0}
        return multipliers.get(effectiveness_code, 1.0)
    
    def get_move_power(self, move_name: str) -> int:
        """Get the base power of a move."""
        move_data = self.get_move_data(move_name)
        if move_data:
            return move_data.get('basePower', 50)
        return 50  # Default power
    
    def get_move_type(self, move_name: str) -> str:
        """Get the type of a move."""
        move_data = self.get_move_data(move_name)
        if move_data:
            return move_data.get('type', 'Normal')
        return 'Normal'  # Default type

# Global instance
data_loader = DataLoader()
