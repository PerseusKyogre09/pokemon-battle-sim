import requests
from typing import Dict, Any, List, Optional
from functools import lru_cache
import os
import json
import re

# Resolve data path robustly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Load name-to-ID mapping
POKEMON_ID_MAP = {}
try:
    id_map_path = os.path.join(DATA_DIR, 'pokemon_ids.json')
    if os.path.exists(id_map_path):
        with open(id_map_path, 'r') as f:
            POKEMON_ID_MAP = json.load(f)
except Exception:
    pass

# We import POKEAPI_NAME_MAP inside functions to avoid circular imports if needed, 
# but here it's fine as long as we don't import pokemon_api from pokemon_utils.
from .pokemon_utils import POKEAPI_NAME_MAP

def get_best_sprite(data, side='front', shiny=False):
    # data['name'] is usually the PokeAPI name (e.g., "wishiwashi-solo" or "bulbasaur")
    name = data.get('name', '').lower()
    
    # 1. Base species that Showdown expects WITHOUT hyphens
    
    # Format megas for showdown (e.g. charizard-mega-y -> charizard-megay)
    if '-mega-' in name:
        name = name.replace('-mega-x', '-megax').replace('-mega-y', '-megay')
    FLATTEN_BASE = [
        'ho-oh', 'porygon-z', 'jangmo-o', 'hakamo-o', 'kommo-o', 
        'sirfetch’d', 'farfetch’d', 'sirfetchd', 'farfetchd',
        'mr-mime', 'mr-rime', 'mime-jr', 'type-null',
        'tapu-koko', 'tapu-lele', 'tapu-bulu', 'tapu-fini',
        'nidoran-m', 'nidoran-f'
    ]
    
    # 2. Specific form overrides for Showdown
    SHOWDOWN_OVERRIDES = {
        'aegislash-shield': 'aegislash',
        'aegislash-blade': 'aegislash-blade',
        'basculin-red-striped': 'basculin',
        'basculin-blue-striped': 'basculin-blue',
        'basculin-white-striped': 'basculin-white',
        'darmanitan-standard': 'darmanitan',
        'darmanitan-galar-standard': 'darmanitan-galar',
        'deoxys-normal': 'deoxys',
        'giratina-altered': 'giratina',
        'gourgeist-average': 'gourgeist',
        'keldeo-ordinary': 'keldeo',
        'landorus-incarnate': 'landorus',
        'thundurus-incarnate': 'thundurus',
        'tornadus-incarnate': 'tornadus',
        'meloetta-aria': 'meloetta',
        'mimikyu-disguised': 'mimikyu',
        'morpeko-full-belly': 'morpeko',
        'morpeko-hangry': 'morpeko-hangry',
        'oricorio-baile': 'oricorio',
        'pumpkaboo-average': 'pumpkaboo',
        'shaymin-land': 'shaymin',
        'toxtricity-amped': 'toxtricity',
        'urshifu-single-strike': 'urshifu',
        'wormadam-plant': 'wormadam',
        'zygarde-50': 'zygarde',
        'minior-red-meteor': 'minior',
        'minior-red': 'minior-red',
        'wishiwashi-solo': 'wishiwashi', 
        'wishiwashi-school': 'wishiwashi-school',
        'toxtricity-low-key': 'toxtricity-lowkey',
        'gastrodon-west': 'gastrodon',
        'lycanroc-midday': 'lycanroc'
    }

    pokemon_name = name
    
    # Check for direct overrides first
    if name in SHOWDOWN_OVERRIDES:
        pokemon_name = SHOWDOWN_OVERRIDES[name]
    elif name in FLATTEN_BASE:
        pokemon_name = name.replace('-', '')
    else:
        # Default behavior: remove ' (for things like Farfetch'd) but keep - for forms
        pokemon_name = name.replace("'", "").replace("’", "")
        
        # If it's a simple name without forms, remove spaces
        if ' ' in pokemon_name:
            pokemon_name = pokemon_name.replace(' ', '')

    # Special case: Showdown uses 'mrmime', 'mrrime', etc.
    if pokemon_name.startswith('mr-'):
        pokemon_name = pokemon_name.replace('-', '')
    if pokemon_name.endswith('-jr'):
        pokemon_name = pokemon_name.replace('-', '')

    back_suffix = "-back" if side == 'back' else ""
    shiny_suffix = "-shiny" if shiny else ""

    # Try static PNG from Gen 5 (best compatibility)
    url_pixel_static = f"https://play.pokemonshowdown.com/sprites/gen5{back_suffix}{shiny_suffix}/{pokemon_name}.png"
    
    return url_pixel_static

@lru_cache(maxsize=1000)
def get_pokemon_data(pokemon_name):
    """Fetch Pokemon data from PokeAPI with caching and name normalization."""
    # 1. Try normalizing to map (e.g. "Giratina Origin" -> "giratinaorigin" -> "giratina-origin")
    normalized_name = re.sub(r'[^a-z0-9]', '', pokemon_name.lower())
    api_name = POKEAPI_NAME_MAP.get(normalized_name, None)
    
    # 2. If not in map, but input has hyphens, it might already be a PokeAPI name (e.g. "stunfisk-galar")
    if not api_name:
        # Strip special chars like % and then check if it looks like a PokeAPI name
        cleaned_name = pokemon_name.lower().replace('%', '').strip()
        api_name = cleaned_name if '-' in cleaned_name else normalized_name

    # 3. Check for ID in our map (ID is more reliable)
    pokemon_id = POKEMON_ID_MAP.get(api_name) or POKEMON_ID_MAP.get(normalized_name)
    identifier = str(pokemon_id) if pokemon_id else api_name

    url = f'https://pokeapi.co/api/v2/pokemon/{identifier}'
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
        
    # Try common form patterns if direct hit fails
    patterns = [
        f"{api_name}-galar", f"{api_name}-alola", f"{api_name}-hisui", 
        f"{api_name}-origin", f"{api_name}-altered", f"{api_name}-single-strike",
        f"{api_name}-amped", f"{api_name}-low-key"
    ]
    for p_name in patterns:
        try:
            res = requests.get(f'https://pokeapi.co/api/v2/pokemon/{p_name}', timeout=5)
            if res.status_code == 200:
                return res.json()
        except:
            continue
            
    # Final fallback: try stripping everything after the first hyphen (e.g. silvally-fairy -> silvally)
    if '-' in api_name:
        base_name = api_name.split('-')[0]
        try:
            res = requests.get(f'https://pokeapi.co/api/v2/pokemon/{base_name}', timeout=5)
            if res.status_code == 200:
                return res.json()
        except:
            pass
            
    return None

def get_forme_data(species_name: str, side='front', shiny=False):
    """Helper for mid-battle form changes to get all necessary transformation data."""
    data = get_pokemon_data(species_name)
    if not data:
        return None
        
    primary_ability = next((a['ability']['name'].replace('-', '').lower() for a in data.get('abilities', []) if not a.get('is_hidden')), '')
    if not primary_ability and data.get('abilities'):
        primary_ability = data['abilities'][0]['ability']['name'].replace('-', '').lower()
        
    return {
        'name': data['name'],
        'types': [t['type']['name'] for t in data['types']],
        'sprite_url': get_best_sprite(data, side=side, shiny=shiny),
        'cry_url': data.get('cries', {}).get('latest', ''),
        'stats': {s['stat']['name'].replace('-', '_'): s['base_stat'] for s in data['stats']},
        'ability': primary_ability
    }

def to_display_name(name: str) -> str:
    """Format a Pokémon name for display (e.g. 'tapu-koko' -> 'Tapu-Koko')."""
    # Special cases
    if name.lower() == 'urshifu-single-strike': return 'Urshifu-Single-Strike'
    if name.lower() == 'urshifu': return 'Urshifu-Single-Strike'
    if name.lower() == 'giratina-altered': return 'Giratina-Altered'
    if name.lower() == 'giratina': return 'Giratina-Altered'
    
    # General rule: capitalize parts
    parts = re.split(r'[- ]', name)
    return '-'.join(p.capitalize() for p in parts)
