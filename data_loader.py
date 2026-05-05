import re
import json
from typing import Dict, Any, List, Optional

class DataLoader:
    def __init__(self):
        self.moves_data = {}
        self.moves_desc_data = {}
        self.learnsets_data = {}
        self.typechart_data = {}
        self.abilities_data = {}
        self._load_all_data()
    
    def _load_all_data(self):
        self._load_moves()
        self._load_moves_descriptions()
        self._load_learnsets()
        self._load_typechart()
        self._load_abilities()
    
    def _load_moves(self):
        try:
            with open('datasets/moves.json', 'r', encoding='utf-8') as f:
                moves_data = json.load(f)
            
            for move_key, move_data in moves_data.items():
                move_name = move_data.get('name', '').lower()
                if not move_name:
                    continue
                
                self.moves_data[move_key.lower()] = move_data
                clean_name = move_name.lower().replace(' ', '').replace('-', '')
                if move_key.lower() != clean_name:
                     self.moves_data[clean_name] = move_data
                
            print(f"=== LOADED {len(self.moves_data)} MOVES FROM moves.json ===")
            
        except FileNotFoundError:
            print("Warning: moves.json file not found")
        except Exception as e:
            print(f"Error loading moves data: {e}")
            raise
    
    def _load_moves_descriptions(self):
        try:
            with open('datasets/moves_desc.json', 'r', encoding='utf-8') as f:
                content = f.read()
                
                content = content.strip()
                if content.startswith('{') and content.endswith('}'):
                    content = content[1:-1]
                
                move_pattern = r'(\w+):\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
                matches = re.findall(move_pattern, content, re.DOTALL)
                
                for move_key, move_content in matches:
                    try:
                        move_desc = {}
                        
                        name_match = re.search(r'name:\s*"([^"]+)"', move_content)
                        if name_match:
                            move_desc['name'] = name_match.group(1)
                        
                        desc_match = re.search(r'desc:\s*"([^"]+)"', move_content)
                        if desc_match:
                            move_desc['desc'] = desc_match.group(1)
                        
                        short_desc_match = re.search(r'shortDesc:\s*"([^"]+)"', move_content)
                        if short_desc_match:
                            move_desc['shortDesc'] = short_desc_match.group(1)
                        
                        boost_match = re.search(r'boost:\s*"([^"]+)"', move_content)
                        if boost_match:
                            move_desc['boost'] = boost_match.group(1)
                        
                        self.moves_desc_data[move_key.lower()] = move_desc
                        
                    except Exception as e:
                        print(f"Warning: Failed to parse move description for {move_key}: {e}")
                        continue
                
                print(f"\n=== LOADED {len(self.moves_desc_data)} MOVE DESCRIPTIONS ===")
                
        except FileNotFoundError:
            print("Warning: moves_desc.json file not found")
        except Exception as e:
            print(f"Error loading move descriptions: {e}")
    
    def _load_learnsets(self):
        try:
            with open('datasets/learnsets.json', 'r', encoding='utf-8') as f:
                learnsets_data = json.load(f)
            
            for pokemon_name, data in learnsets_data.items():
                if 'learnset' in data:
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
            
        except FileNotFoundError:
            print("Warning: typechart.json file not found")
        except json.JSONDecodeError as e:
            print(f"Error parsing type chart data: {e}")
        except Exception as e:
            print(f"Error loading type chart data: {e}")
            raise
            
    def _load_abilities(self):
        try:
            with open('datasets/abilities_logic.json', 'r', encoding='utf-8') as f:
                self.abilities_data = json.load(f)
            
            print(f"=== LOADED {len(self.abilities_data)} ABILITIES FROM abilities_logic.json ===")
            
        except FileNotFoundError:
            print("Warning: abilities_logic.json file not found")
        except Exception as e:
            print(f"Error loading abilities data: {e}")
            raise
    
    def get_move(self, move_name):
        if not move_name:
            return None
            
        move_key = move_name.lower().replace(' ', '').replace('-', '')
        move_data = self.moves_data.get(move_key)
        
        return move_data
    
    def get_pokemon_moves(self, pokemon_name: str, limit: Optional[int] = None) -> List[str]:
        name_lower = pokemon_name.lower()
        normalized = name_lower.replace("-", "")
        
        all_move_ids = set()
        
        data = self.learnsets_data.get(normalized)
        if data:
            all_move_ids.update(data)
            
        data_hyphen = self.learnsets_data.get(name_lower)
        if data_hyphen:
            all_move_ids.update(data_hyphen)
            
        if "-" in name_lower:
            base_name = name_lower.split("-")[0]
            base_data = self.learnsets_data.get(base_name)
            if base_data:
                all_move_ids.update(base_data)
            
            base_norm = base_name.replace("-", "")
            if base_norm != base_name:
                base_data_norm = self.learnsets_data.get(base_norm)
                if base_data_norm:
                    all_move_ids.update(base_data_norm)
        
             for key in self.learnsets_data:
                 if key in normalized or normalized in key:
                     all_move_ids.update(self.learnsets_data[key])
                     if len(all_move_ids) > 10: break

        move_names = []
        for move_id in all_move_ids:
            move_data = self.moves_data.get(move_id.lower())
            if move_data:
                move_names.append(move_data.get('name', move_id))
            else:
                move_names.append(move_id.replace('-', ' ').title())
        
        results = sorted(list(set(move_names)))
        if limit:
            return results[:limit]
        return results
    
    def get_type_effectiveness(self, attacking_type: str, defending_type: str) -> float:
        if not attacking_type or not defending_type:
            return 1.0
            
        attacking_type = attacking_type.title()
        defending_type = defending_type.title()
        
        defending_data = self.typechart_data.get(defending_type, {})
        damage_taken = defending_data.get('damageTaken', {})
        
        effectiveness_code = damage_taken.get(attacking_type, 0)
        
        multiplier = 1.0
        if effectiveness_code == 0:
            multiplier = 1.0
        elif effectiveness_code == 1:
            multiplier = 2.0
        elif effectiveness_code == 2:
            multiplier = 0.5
        elif effectiveness_code == 3:
            multiplier = 0.0
            
        return multiplier
    
    def get_move_power(self, move_name: str) -> int:
        move_data = self.get_move_data(move_name)
        power = move_data.get('basePower', 50) if move_data else 50
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
        
        effectiveness = round(effectiveness, 2)
        
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
    
    def get_move_pp(self, move_name: str) -> int:
        move_data = self.get_move_data(move_name)
        return move_data.get('pp', 15) if move_data else 15
        
    def get_move_data(self, move_name: str) -> Optional[Dict[str, Any]]:
        if not move_name:
            return None
            
        # Try to find the move by exact key first
        move_key = move_name.lower().replace(' ', '').replace('-', '')
        
        if move_key in self.moves_data:
            return self.moves_data[move_key]
            
        for key, data in self.moves_data.items():
            if data.get('name', '').lower() == move_name.lower():
                return data
                
        for key, data in self.moves_data.items():
            if move_name.lower() in key.lower() or move_name.lower() in data.get('name', '').lower():
                return data
                
        return None
        
    def get_ability(self, ability_name: str) -> Optional[Dict[str, Any]]:
        if not ability_name:
            return None
            
        ability_key = ability_name.lower().replace(' ', '').replace('-', '')
        return self.abilities_data.get(ability_key)
    
    def get_move_description(self, move_name: str) -> Optional[Dict[str, Any]]:
        if not move_name:
            return None
            
        # Try to find the move by exact key first
        move_key = move_name.lower().replace(' ', '').replace('-', '')
        
        if move_key in self.moves_desc_data:
            return self.moves_desc_data[move_key]
            
        for key, data in self.moves_desc_data.items():
            if data.get('name', '').lower() == move_name.lower():
                return data
                
        return None

# Global instance
data_loader = DataLoader()
