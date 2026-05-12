
import re

def _abbr_to_stat_name(abbr: str):
    abbr_map = {
        'hp': 'hp',
        'atk': 'attack',
        'def': 'defense',
        'spa': 'special_attack',
        'spd': 'special_defense',
        'spe': 'speed',
    }
    return abbr_map.get(abbr.lower())

def _parse_boost_amounts(logic_str: str):
    boosts = {}
    if not logic_str:
        return boosts
    
    match = re.search(r"this\.boost\(\{\s*([^}]+)\s*\}", logic_str)
    if match:
        boost_str = match.group(1)
        stat_pairs = re.findall(r"(\w+):\s*(-?\d+)", boost_str)
        for stat_abbr, value in stat_pairs:
            stat_name = _abbr_to_stat_name(stat_abbr)
            if stat_name:
                boosts[stat_name] = int(value)
    return boosts

intimidate_logic = """onStart(pokemon) {
            let activated = false;
            for (const target of pokemon.adjacentFoes()) {
                if (!activated) {
                    this.add('-ability', pokemon, 'Intimidate', 'boost');
                    activated = true;
                }
                if (target.volatiles['substitute']) {
                    this.add('-immune', target);
                }
                else {
                    this.boost({ atk: -1 }, target, pokemon, null, true);
                }
            }
        }"""

print(f"Intimidate Boosts: {_parse_boost_amounts(intimidate_logic)}")
