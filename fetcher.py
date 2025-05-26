import requests
import json
import sys
from typing import Dict, Any


def fetch_pokemon_data(url: str) -> Dict[str, Any]:
    try:
        print(f"Fetching data from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"Successfully fetched data containing {len(data)} Pokemon")
        return data
        
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)


def extract_stats_sets(data: Dict[str, Any]) -> Dict[str, Any]:
    stats_only = {}
    stats_count = 0
    dex_count = 0
    
    for format_name, format_data in data.items():
        if isinstance(format_data, dict):
            # Count dex sets
            if 'dex' in format_data and isinstance(format_data['dex'], dict):
                for pokemon_name, pokemon_sets in format_data['dex'].items():
                    if isinstance(pokemon_sets, dict):
                        dex_count += len(pokemon_sets)
            
            # Extract stats sets
            if 'stats' in format_data and isinstance(format_data['stats'], dict):
                stats_data = format_data['stats']
                if stats_data:
                    stats_only[format_name] = {"stats": stats_data}
                    
                    # Count stats sets for reporting
                    for pokemon_name, pokemon_sets in stats_data.items():
                        if isinstance(pokemon_sets, dict):
                            stats_count += len(pokemon_sets)
    
    print(f"Extracted {stats_count} stats sets from {len(stats_only)} formats")
    print(f"Excluded {dex_count} dex sets")
    
    return stats_only


def save_to_json(data: Dict[str, Any], filename: str) -> None:
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved data to {filename}")
        
    except IOError as e:
        print(f"Error saving file: {e}")
        sys.exit(1)


def main():
    # Pokemon Showdown Gen 8 sets URL
    url = "https://play.pokemonshowdown.com/data/sets/gen8.json"
    
    # Output filename
    output_file = "gen8_stats_sets.json"
    
    # Fetch the data
    full_data = fetch_pokemon_data(url)
    
    # Extract only stats sets
    stats_data = extract_stats_sets(full_data)
    
    if not stats_data:
        print("Warning: No stats sets found in the data!")
        return
    
    # Save to JSON file
    save_to_json(stats_data, output_file)
    
    print(f"\nProcess completed successfully!")
    print(f"Stats sets have been saved to '{output_file}'")


if __name__ == "__main__":
    main()