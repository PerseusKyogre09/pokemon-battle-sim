import json
import os
import re
from typing import List, Optional

# Cache to avoid repeated lookups
moveset_cache = {}
sets_data = None

def get_strategic_moveset(pokemon_name: str, format_name: str = None, debug: bool = True) -> Optional[List[str]]:
    try:
        if debug:
            print(f"\nGetting strategic moveset for: {pokemon_name}")
            if format_name:
                print(f"Format: {format_name}")
                
        # Use the new fetch_sets which handles format selection
        moves = fetch_sets(pokemon_name, format_name, debug)
        
        # Try with gen8ou if no moves found
        if moves is None and format_name is None:
            if debug:
                print("No moveset found in any format, trying gen8ou explicitly...")
            moves = fetch_sets(pokemon_name, "gen8ou", debug)
        
        # If still no moves, try random moveset
        if moves is None:
            if debug:
                print("No set found in any format, trying fallback...")
            moves = get_fallback_moveset(pokemon_name, debug)
        
        return moves
            
    except Exception as e:
        if debug:
            import traceback
            print(f"Error in get_strategic_moveset for {pokemon_name}: {e}")
            traceback.print_exc()
        # If there's an error, try fallback
        return get_fallback_moveset(pokemon_name, debug)

def fetch_sets(pokemon_name: str, format_name: str = None, debug: bool = True) -> Optional[List[str]]:
# Normalize the Pokémon name to lowercase
    normalized_name = re.sub(r'[^a-z0-9]', '', pokemon_name.lower())
    
    if debug:
        print(f"\n==================================================")
        print(f"Getting strategic moveset for: {pokemon_name}")
        print(f"Format: {format_name if format_name else 'search all formats'}")
        print(f"Normalized name: {normalized_name}")
    
    # Check cache first if a specific format is requested
    if format_name:
        cache_key = f"{normalized_name}_{format_name}"
        if cache_key in moveset_cache:
            if debug:
                print(f"Found in cache for {format_name}!")
            return moveset_cache[cache_key]
    
    # Order of formats
    format_order = [
        'gen8ou',    # OverUsed
        'gen8ubers', # Ubers
        'gen8uu',    # UnderUsed
        'gen8ru',    # RarelyUsed
        'gen8nu',    # NeverUsed
        'gen8pu',    # PU (unofficial)
        'gen8lc',    # Little Cup
        'gen8monotype' # Monotype
    ]
    
    formats_to_check = [format_name] if format_name else format_order
    
    for current_format in formats_to_check:
        if debug:
            print(f"Trying format: {current_format}")
        
        # Check cache for this format
        cache_key = f"{normalized_name}_{current_format}"
        if cache_key in moveset_cache:
            if debug:
                print(f"Found in cache for {current_format}!")
            return moveset_cache[cache_key]
        
        # Try to get the moveset for this format
        moves = fetch_sets_direct(pokemon_name, current_format, debug)
        
        if moves is not None:
            # Cache the result for future use
            moveset_cache[cache_key] = moves
            if debug:
                print(f"Successfully found moveset in {current_format}")
            return moves
    if debug:
        print("No moveset found in any format, trying fallback...")
    
    # Last resort
    moves = get_fallback_moveset(pokemon_name, debug)
    if moves is not None:
        moveset_cache[f"{normalized_name}_fallback"] = moves
    
    return moves

def fetch_sets_direct(pokemon_name: str, format_name: str, debug: bool = True) -> Optional[List[str]]:
    try:
        if debug:
            print(f"  Loading data for format: {format_name}")
        
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'gen8_stats_sets.json')
        
        if debug:
            print(f"  Loading JSON file from: {file_path}")
            
        if not os.path.exists(file_path):
            if debug:
                print("  Error: gen8_stats_sets.json not found!")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            if debug:
                print("  Parsing JSON data...")
            try:
                sets_data = json.load(f)
            except json.JSONDecodeError as e:
                if debug:
                    print(f"  Error parsing JSON: {e}")
                return None
        
        if not isinstance(sets_data, dict):
            if debug:
                print("  Error: Invalid data format in JSON file")
            return None
        
        if debug:
            print(f"  Available formats: {list(sets_data.keys())}")
        
        # Find the format in the data
        if format_name not in sets_data:
            if debug:
                print(f"  No data found for format: {format_name}")
            return None
            
        format_data = sets_data[format_name]
        if not isinstance(format_data, dict):
            if debug:
                print(f"  Invalid format data for {format_name}")
            return None
            
        # Get the stats data
        stats_data = format_data.get('stats', {})
        if not stats_data:
            if debug:
                print(f"  No stats data found for format: {format_name}")
            return None
        
        if debug:
            print(f"  Found {len(stats_data)} Pokémon in {format_name}")
            # Print first few Pokémon names for debugging
            sample_pokemon = list(stats_data.keys())[:5]
            print(f"  Sample Pokémon in {format_name}: {', '.join(sample_pokemon)}")
        
        # Try to find the Pokémon in the format's stats data
        # First try exact match, then case-insensitive, then partial match
        pokemon_key = None
        
        # Try exact match first
        if pokemon_name in stats_data:
            pokemon_key = pokemon_name
        else:
            # Try case-insensitive match
            for key in stats_data.keys():
                if key.lower() == pokemon_name.lower():
                    pokemon_key = key
                    break
            
            # If still not found, try partial match
            if pokemon_key is None:
                for key in stats_data.keys():
                    if pokemon_name.lower() in key.lower():
                        pokemon_key = key
                        break
        
        if not pokemon_key:
            if debug:
                print(f"  No stats sets found for {pokemon_name} in {format_name}")
            return None
        
        # Get all sets for this Pokémon in the specified format
        pokemon_sets = stats_data[pokemon_key]
        
        if debug:
            print(f"  Found {len(pokemon_sets)} stats sets for {pokemon_key} in {format_name}")
            print(f"  Available sets: {list(pokemon_sets.keys())}")
        
        # Get the first set
        if not pokemon_sets:
            if debug:
                print(f"  No sets found for {pokemon_key}")
            return None
            
        first_set_name = next(iter(pokemon_sets.keys()))
        first_set = pokemon_sets[first_set_name]
        
        if debug:
            print(f"  Using set: {first_set_name}")
        
        # Extract moves from the set
        moves = first_set.get('moves', [])
        
        if debug:
            print(f"  Raw moves data: {moves}")
        
        # Take the first 4 moves
        moves = moves[:4]
        
        # Filter out any empty or None moves
        moves = [str(move).strip() for move in moves if move and str(move).strip()]
        
        if debug:
            print(f"  Processed moves: {moves}")
        
        if moves:
            if debug:
                print(f"  Found moves in set: {moves}")
            return moves
            
    except FileNotFoundError:
        if debug:
            print("  Error: gen8_stats_sets.json not found in the script directory")
    except json.JSONDecodeError as e:
        if debug:
            print(f"  Error: Invalid JSON in gen8_stats_sets.json: {e}")
    except Exception as e:
        if debug:
            import traceback
            print(f"  Error in fetch_sets_direct: {e}")
            traceback.print_exc()
    
    return None

def is_attack_move(move_name: str) -> bool:
    """Simple heuristic to identify attacking moves."""
    attack_keywords = ['beam', 'bolt', 'blast', 'attack', 'punch', 'kick', 'slash', 
                      'cut', 'claw', 'strike', 'bomb', 'cannon', 'shot', 'throw',
                      'slam', 'smash', 'crash', 'tackle', 'headbutt', 'bite', 'fang']
    
    return any(keyword in move_name.lower() for keyword in attack_keywords)

def is_utility_move(move_name: str) -> bool:
    """Simple heuristic to identify utility moves."""
    utility_keywords = ['protect', 'recover', 'rest', 'substitute', 'toxic', 'leech', 
                       'heal', 'boost', 'dance', 'calm', 'haze', 'mist', 'reflect',
                       'light', 'screen', 'barrier', 'confuse', 'disable', 'encore',
                       'taunt', 'torment', 'wish', 'aromatherapy', 'roost', 'synthesis']
    
    return any(keyword in move_name.lower() for keyword in utility_keywords)

def select_coverage_moves(moves: List[str], count: int) -> List[str]:
    """Select a diverse set of attacking moves for type coverage."""
    if len(moves) <= count:
        return moves
    
    # This is a simplified version
    selected = []
    for _ in range(count):
        if not moves:
            break
        move = random.choice(moves)
        selected.append(move)
        moves.remove(move)
    
    return selected

def get_fallback_moveset(pokemon_name: str, debug: bool = True) -> Optional[List[str]]:
    if debug:
        print(f"  Checking fallback moveset for: {pokemon_name}")
    pokemon_name = pokemon_name.lower().replace('-', '').replace(' ', '')
    # Gen 8 OU common movesets for common Pokémon (only if no sets found)
    fallback_movesets = {
        'landorustherian': ['Earthquake', 'U-turn', 'Stealth Rock', 'Toxic'],
        'clefable': ['Moonblast', 'Soft-Boiled', 'Thunder Wave', 'Stealth Rock'],
        'ferrothorn': ['Power Whip', 'Knock Off', 'Leech Seed', 'Spikes'],
        'dragapult': ['Shadow Ball', 'Draco Meteor', 'Fire Blast', 'U-turn'],
        'toxapex': ['Scald', 'Recover', 'Haze', 'Toxic'],
        'heatran': ['Magma Storm', 'Earth Power', 'Taunt', 'Stealth Rock'],
        'corviknight': ['Brave Bird', 'Body Press', 'Roost', 'U-turn'],
        'zapdos': ['Discharge', 'Heat Wave', 'Roost', 'Defog'],
        'rillaboom': ['Grassy Glide', 'Knock Off', 'U-turn', 'Superpower'],
        'magearna': ['Fleur Cannon', 'Focus Blast', 'Aura Sphere', 'Volt Switch'],
        'tapukoko': ['Thunderbolt', 'Dazzling Gleam', 'U-turn', 'Roost'],
        'pelipper': ['Scald', 'Hurricane', 'U-turn', 'Roost'],
        'barraskewda': ['Liquidation', 'Close Combat', 'Psychic Fangs', 'Flip Turn'],
        'swampert': ['Flip Turn', 'Earthquake', 'Stealth Rock', 'Toxic'],
        'excadrill': ['Earthquake', 'Iron Head', 'Rapid Spin', 'Stealth Rock'],
        'zapdosgalar': ['Thunderous Kick', 'Brave Bird', 'U-turn', 'Roost'],
        'volcarona': ['Quiver Dance', 'Flamethrower', 'Bug Buzz', 'Psychic'],
        'slowbro': ['Scald', 'Slack Off', 'Future Sight', 'Teleport'],
        'kartana': ['Swords Dance', 'Leaf Blade', 'Knock Off', 'Sacred Sword'],
        
        # Iconic Pokémon
        'pikachu': ['Volt Switch', 'Thunderbolt', 'Surf', 'Grass Knot'],
        'charizard': ['Fire Blast', 'Air Slash', 'Focus Blast', 'Roost'],
        'blastoise': ['Hydro Pump', 'Ice Beam', 'Dark Pulse', 'Rapid Spin'],
        'venusaur': ['Giga Drain', 'Sludge Bomb', 'Earth Power', 'Sleep Powder'],
        'gengar': ['Shadow Ball', 'Sludge Wave', 'Focus Blast', 'Nasty Plot'],
        'dragonite': ['Dragon Dance', 'Dual Wingbeat', 'Earthquake', 'Roost'],
        'tyranitar': ['Stone Edge', 'Crunch', 'Earthquake', 'Stealth Rock'],
        'garchomp': ['Swords Dance', 'Earthquake', 'Stone Edge', 'Fire Fang'],
        'mimikyu': ['Swords Dance', 'Play Rough', 'Shadow Claw', 'Shadow Sneak'],
        'aegislash': ['Shadow Ball', 'Flash Cannon', 'Shadow Sneak', 'King\'s Shield']
    }
    
    return fallback_movesets.get(pokemon_name)
