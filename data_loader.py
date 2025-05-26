"""
Data loader for Pokemon battle system using TypeScript dataset files.
Parses moves.ts, learnsets.ts, and typechart.ts files.
"""

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
        """Load all data from TypeScript files on initialization."""
        self._load_moves()
        self._load_learnsets()
        self._load_typechart()
    
    def _parse_ts_object(self, content: str, object_name: str) -> Dict[str, Any]:
        """Parse a TypeScript object export into a Python dictionary."""
        # Find the object definition
        pattern = rf'export const {object_name}[^=]*=\s*{{(.*)}};?\s*$'
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        
        if not match:
            return {}
        
        object_content = match.group(1)
        
        # Convert TypeScript object to JSON-like format
        # This is a simplified parser - may need refinement for complex cases
        try:
            # Replace TypeScript-specific syntax
            object_content = re.sub(r'(\w+):', r'"\1":', object_content)  # Quote keys
            object_content = re.sub(r':\s*([^",{\[\]}\s]+)(?=\s*[,}])', r': "\1"', object_content)  # Quote string values
            object_content = re.sub(r':\s*true\b', ': True', object_content)  # Convert boolean
            object_content = re.sub(r':\s*false\b', ': False', object_content)  # Convert boolean
            object_content = re.sub(r':\s*null\b', ': None', object_content)  # Convert null
            
            # Wrap in braces and parse
            json_content = '{' + object_content + '}'
            return eval(json_content)  # Using eval for simplicity - in production, use proper JSON parser
        except:
            # Fallback to manual parsing for complex structures
            return self._manual_parse_object(object_content)
    
    def _manual_parse_object(self, content: str) -> Dict[str, Any]:
        """Manual parsing for complex TypeScript objects."""
        result = {}
        
        # Split by top-level entries (this is a simplified approach)
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
            
            # Extract move data using regex patterns
            move_pattern = r'(\w+):\s*{([^{}]*(?:{[^{}]*}[^{}]*)*)}'
            moves = re.findall(move_pattern, content)
            
            for move_name, move_data in moves:
                move_info = {}
                
                # Parse individual properties
                props = re.findall(r'(\w+):\s*([^,}\n]+)', move_data)
                for prop_name, prop_value in props:
                    prop_value = prop_value.strip().rstrip(',')
                    
                    if prop_value.isdigit():
                        move_info[prop_name] = int(prop_value)
                    elif prop_value == 'true':
                        move_info[prop_name] = True
                    elif prop_value == 'false':
                        move_info[prop_name] = False
                    elif prop_value == 'null':
                        move_info[prop_name] = None
                    else:
                        move_info[prop_name] = prop_value.strip('"\'')
                
                self.moves_data[move_name] = move_info
                
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
