import re
import json
import os

def parse_abilities_ts(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Split into ability blocks
    # We look for "key: {" at the start of a line with a tab
    ability_blocks = re.split(r'\n\t([a-z0-9]+): \{', content)
    
    abilities = {}
    
    # ability_blocks[0] is the header
    for i in range(1, len(ability_blocks), 2):
        id = ability_blocks[i]
        block = ability_blocks[i+1]
        
        # End of block is "}," at the start of a line with a tab
        end_match = re.search(r'\n\t\},', block)
        if end_match:
            block = block[:end_match.start()]
        
        data = {"id": id}
        
        # 1. Extract Name
        name_match = re.search(r'name: "(.*?)",', block)
        if name_match:
            data["name"] = name_match.group(1)
            
        # 2. Extract Boosts (simple cases like Intimidate)
        # Match: this.boost({ atk: -1 }, target, pokemon, null, true);
        boost_match = re.search(r'this\.boost\(\{ (.*?) \}', block)
        if boost_match:
            boost_str = boost_match.group(1)
            # Parse { atk: -1, spa: 1 }
            # Stat name normalization map
            STAT_MAP = {
                "atk": "attack",
                "def": "defense",
                "spa": "special_attack",
                "spd": "special_defense",
                "spe": "speed"
            }
            
            boosts = {}
            for part in boost_str.split(','):
                if ':' in part:
                    try:
                        k, v = part.split(':')
                        k = k.strip()
                        # Normalize stat name
                        k = STAT_MAP.get(k, k)
                        boosts[k] = int(v.strip())
                    except ValueError:
                        # Skip non-integer boosts for now (like 'length')
                        continue
            
            # Determine target
            target = "self"
            if "target" in boost_match.string[boost_match.end():boost_match.end()+20]:
                target = "opponent"
            
            data["on_switch_in"] = [{"action": "boost", "target": target, "stats": boosts}]

        for ts_stat, py_stat in [("Atk", "attack"), ("Def", "defense"), ("SpA", "special_attack"), ("SpD", "special_defense"), ("Spe", "speed")]:
            modify_stat = re.search(f'onModify{ts_stat}\(.*?return this\.chainModify\((.*?)\)', block, re.DOTALL)
            if modify_stat:
                code_segment = modify_stat.group(0)
                if "if (" in code_segment:
                    continue # Skip conditional modifiers for now
                val = modify_stat.group(1).strip()
                # Handle [4915, 4096] or (2) case
                nums = re.findall(r'\d*\.\d+|\d+', val)
                if len(nums) >= 2:
                    val = float(nums[0]) / float(nums[1])
                elif len(nums) == 1:
                    val = float(nums[0])
                else:
                    val = 1.0
                data["stat_modifiers"] = data.get("stat_modifiers", {})
                data["stat_modifiers"][py_stat] = float(val)

        # 4. Extract Damage Multipliers (Blaze, Technician)
        dmg_match = re.search(r'(onBasePower|onModifyAtk|onModifySpA)\(.*?return this\.chainModify\((.*?)\)', block, re.DOTALL)
        if dmg_match:
            val = dmg_match.group(2).strip()
            nums = re.findall(r'\d*\.\d+|\d+', val)
            if len(nums) >= 2:
                val = float(nums[0]) / float(nums[1])
            elif len(nums) == 1:
                val = float(nums[0])
            else:
                val = 1.0
            
            condition = "none"
            move_type = None
            if "maxhp / 3" in block:
                condition = "hp_threshold"
                if "Fire" in block: move_type = "fire"
                elif "Water" in block: move_type = "water"
                elif "Grass" in block: move_type = "grass"
            elif "move.power <= 60" in block:
                condition = "base_power_below"
            elif "move.type === 'Normal'" in block and "Flying" in block:
                # Aerilate-like
                move_type = "normal"
                condition = "type_conversion"
                
            data["damage_modifiers"] = [{
                "multiplier": float(val),
                "condition": condition
            }]
            if move_type:
                data["damage_modifiers"][0]["move_type"] = move_type

        # 5. Extract Immunities (Levitate)
        # onTryHit(target, source, move) { if (move.type === 'Ground') return null; }
        if "move.type === 'Ground'" in block and "return null" in block:
            data["immunities"] = {"types": ["ground"]}
            
        # 6. STAB (Adaptability)
        if "onModifySTAB" in block:
            data["on_modify_stab"] = 2.0

        # 7. Secondary Effect Chance (Serene Grace)
        if "secondary.chance *= 2" in block or "secondaries" in block and "*= 2" in block:
            data["secondary_multiplier"] = 2.0
        elif "secondary.chance *= 3" in block:
            data["secondary_multiplier"] = 3.0

        abilities[id] = data
        
    return abilities

if __name__ == "__main__":
    ts_path = "/run/media/perseuskyogre/T7/Projects/Pokemon/datasets/abilities.ts"
    output_path = "/run/media/perseuskyogre/T7/Projects/Pokemon/datasets/abilities_logic.json"
    
    logic = parse_abilities_ts(ts_path)
    with open(output_path, 'w') as f:
        json.dump(logic, f, indent=2)
    
    print(f"Extracted logic for {len(logic)} abilities to {output_path}")
