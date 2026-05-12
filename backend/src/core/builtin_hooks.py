import random
from .hooks import BattleContext


def self_switch_after_move(context: BattleContext) -> None:
    move = context.move
    attacker = context.attacker
    game = context.game
    if not move or not getattr(move, "self_switch", False):
        return
    if context.flags.get("suppress_self_switch"):
        return
    if attacker.current_hp <= 0:
        return

    move_successful = (
        context.actual_damage > 0
        or context.substitute_damage > 0
        or bool(context.status_message)
    )
    if not move_successful or not game._has_available_switch(context.is_player_attacking):
        return

    if context.is_player_attacking:
        game.pending_player_self_switch = True
        context.events.append({
            "type": "pending_switch",
            "message": f"{game._get_pokemon_name(attacker)} went back to its trainer!",
            "target": "player",
            "is_player_switch": True,
            "pokemon_hp": attacker.current_hp,
            "player_hp": game.player_pokemon.current_hp,
            "opponent_hp": game.opponent_pokemon.current_hp,
        })
    else:
        new_idx = game._first_available_switch_index(False)
        if new_idx is not None:
            context.events.extend(game.switch_pokemon(False, new_idx))


def eject_button_on_hit(context: BattleContext) -> None:
    defender = context.defender
    game = context.game
    if context.actual_damage <= 0 or not defender or not defender.item_obj:
        return
    if defender.item_obj.id != "ejectbutton" or defender.current_hp <= 0:
        return
    is_defender_player = defender == game.player_pokemon
    if not game._has_available_switch(is_defender_player):
        return

    defender.item = None
    defender.item_obj = None
    context.flags["suppress_self_switch"] = True
    context.events.append({
        "type": "item",
        "item_name": "Eject Button",
        "pokemon_name": game._get_pokemon_name(defender),
        "message": f"{game._get_pokemon_name(defender)} was switched out with its Eject Button!",
        "target": "player" if is_defender_player else "opponent",
    })

    if is_defender_player:
        game.pending_player_self_switch = True
        context.events.append({
            "type": "pending_switch",
            "message": f"Choose a Pokemon to switch in for {game._get_pokemon_name(defender)}.",
            "target": "player",
        })
    else:
        new_idx = game._first_available_switch_index(False)
        if new_idx is not None:
            context.events.extend(game.switch_pokemon(False, new_idx))


def ohko_try_hit(context: BattleContext) -> None:
    move = context.move
    attacker = context.attacker
    defender = context.defender
    if not move or not getattr(move, "ohko", False):
        return
    if attacker.level < defender.level:
        context.flags["move_failed"] = True
        context.events.append({
            "type": "status",
            "message": "But it failed!",
            "target": "player" if context.is_player_attacking else "opponent",
        })

def ohko_accuracy(context: BattleContext) -> None:
    move = context.move
    attacker = context.attacker
    defender = context.defender
    if not move or not getattr(move, "ohko", False):
        return
    # OHKO moves have a special accuracy formula: 30 + (attacker.level - defender.level)
    context.accuracy = 30 + (attacker.level - defender.level)

def ohko_damage(context: BattleContext) -> None:
    move = context.move
    defender = context.defender
    if not move or not getattr(move, "ohko", False):
        return
    # OHKO moves deal damage equal to the target's current HP
    context.actual_damage = defender.current_hp

def sturdy_try_hit(context: BattleContext) -> None:
    game = context.game
    move = context.move
    defender = context.defender
    if not move or not defender or not defender.ability:
        return
    if defender.ability.id == "sturdy" and getattr(move, "ohko", False):
        context.flags["move_blocked"] = True
        context.events.append({
            "type": "status",
            "message": f"{game._get_pokemon_name(defender)} is immune to OHKO moves due to its Sturdy!",
            "target": "opponent" if context.is_player_attacking else "player",
        })

def hunger_switch_residual(context: BattleContext) -> None:
    game = context.game
    from ..utils.pokemon_api import get_forme_data
    
    for pokemon in [game.player_pokemon, game.opponent_pokemon]:
        if not pokemon or pokemon.current_hp <= 0 or not pokemon.ability:
            continue
            
        if pokemon.ability.id == "hungerswitch" and "morpeko" in pokemon.name.lower():
            # Morpeko changes form at the end of every turn
            new_species = "morpeko-hangry" if "-hangry" not in pokemon.name.lower() else "morpeko-full-belly"
            side = 'back' if pokemon == game.player_pokemon else 'front'
            
            forme_data = get_forme_data(new_species, side=side)
            if forme_data:
                pokemon.forme_change(
                    new_name=forme_data['name'],
                    new_types=forme_data['types'],
                    new_sprite=forme_data['sprite_url'],
                    new_stats=forme_data['stats'],
                    new_cry=forme_data['cry_url']
                )
                
                context.events.append({
                    "type": "ability",
                    "ability_name": "Hunger Switch",
                    "pokemon_name": game._get_pokemon_name(pokemon),
                    "message": f"{game._get_pokemon_name(pokemon)} changed to its {'Hangry' if '-hangry' in pokemon.name.lower() else 'Full Belly'} Mode!",
                    "target": "player" if pokemon == game.player_pokemon else "opponent",
                    "is_player": pokemon == game.player_pokemon,
                    "new_sprite": pokemon.sprite_url,
                    "new_name": pokemon.name
                })

def stance_change_before_move(context: BattleContext) -> None:
    game = context.game
    attacker = context.attacker
    move = context.move
    
    if not attacker or not attacker.ability or attacker.ability.id != "stancechange":
        return
    if "aegislash" not in attacker.name.lower() or not move:
        return
        
    from ..utils.pokemon_api import get_forme_data
    
    current_forme = "blade" if "-blade" in attacker.name.lower() else "shield"
    target_forme = None
    
    # Use move ID for reliable matching (kingsshield)
    move_id = move.id.lower().replace("-", "").replace("'", "")
    
    if move_id == "kingsshield":
        if current_forme != "shield":
            target_forme = "aegislash-shield"
    elif move.category in ["physical", "special"]:
        if current_forme != "blade":
            target_forme = "aegislash-blade"
            
    if target_forme:
        side = 'back' if attacker == game.player_pokemon else 'front'
        forme_data = get_forme_data(target_forme, side=side)
        if forme_data:
            attacker.forme_change(
                new_name=forme_data['name'],
                new_types=forme_data['types'],
                new_sprite=forme_data['sprite_url'],
                new_stats=forme_data['stats'],
                new_cry=forme_data['cry_url']
            )
            context.events.append({
                "type": "ability",
                "ability_name": "Stance Change",
                "pokemon_name": game._get_pokemon_name(attacker),
                "message": f"{game._get_pokemon_name(attacker)} changed to its {'Blade' if 'blade' in target_forme else 'Shield'} Forme!",
                "target": "player" if attacker == game.player_pokemon else "opponent",
                "is_player": attacker == game.player_pokemon,
                "new_sprite": attacker.sprite_url,
                "new_name": attacker.name
            })


def sturdy_damage(context: BattleContext) -> None:
    game = context.game
    defender = context.defender
    if not defender or not defender.ability or defender.ability.id != "sturdy":
        return
    # Sturdy only works if the Pokemon is at full HP
    if defender.current_hp == defender.max_hp and context.actual_damage >= defender.current_hp:
        context.actual_damage = defender.current_hp - 1
        context.events.append({
            "type": "ability",
            "ability_name": "Sturdy",
            "pokemon_name": game._get_pokemon_name(defender),
            "message": f"{game._get_pokemon_name(defender)} endured the hit with Sturdy!",
            "target": "opponent" if context.is_player_attacking else "player",
        })


def recoil_on_hit(context: BattleContext) -> None:
    game = context.game
    move = context.move
    attacker = context.attacker
    if not move or not getattr(move, "is_recoil_move", False) or context.actual_damage <= 0:
        return
    if attacker.has_ability("rockhead"):
        return
    
    # Recoil calculation (1/4 of damage dealt usually, but we check move data)
    numerator, denominator = getattr(move, "recoil_ratio", [1, 4])
    recoil_damage = int(context.actual_damage * (numerator / denominator))
    if recoil_damage <= 0: recoil_damage = 1
    
    attacker.take_damage(recoil_damage)
    context.events.append({
        "type": "status",
        "message": f"{game._get_pokemon_name(attacker)} is hurt by recoil!",
        "target": "player" if context.is_player_attacking else "opponent",
        "pokemon_hp": attacker.current_hp,
    })

def healing_on_hit(context: BattleContext) -> None:
    game = context.game
    move = context.move
    attacker = context.attacker
    if not move or not getattr(move, "is_healing_move", False):
        return
    
    # Check for drain moves vs non-drain healing
    drain_ratio = getattr(move, "drain_ratio", None)
    if drain_ratio is not None:
        if context.actual_damage <= 0: return
        numerator, denominator = drain_ratio
        heal_amount = int(context.actual_damage * (numerator / denominator))
    else:
        # Standard healing (e.g. Recover) usually 1/2 max HP
        heal_ratio = getattr(move, "heal_amount", [1, 2])
        numerator, denominator = heal_ratio
        heal_amount = int(attacker.max_hp * (numerator / denominator))
        
    if heal_amount <= 0: return
    
    hp_before = attacker.current_hp
    attacker.heal(heal_amount)
    actual_heal = attacker.current_hp - hp_before
    
    if actual_heal > 0:
        msg = f"{game._get_pokemon_name(attacker)} recovered {actual_heal} HP!"
        if drain_ratio: msg += f" {game._get_pokemon_name(context.defender)}'s energy was drained!"
        context.events.append({
            "type": "status",
            "message": msg,
            "target": "player" if context.is_player_attacking else "opponent",
            "pokemon_hp": attacker.current_hp,
        })

def secondary_effects_on_hit(context: BattleContext) -> None:
    move = context.move
    attacker = context.attacker
    defender = context.defender
    if not move or context.actual_damage <= 0 or not defender or defender.current_hp <= 0:
        return
    
    # Sheer Force check
    if attacker.has_ability("sheerforce") and (move.data.get("secondary") or move.data.get("secondaries")):
        return # Sheer Force suppresses secondaries
        
    # Serene Grace multiplier
    multiplier = 2.0 if attacker.has_ability("serenegrace") else 1.0
    
    def process_block(block):
        chance = block.get("chance", 100) * multiplier
        if random.randint(1, 100) > chance:
            return
        
        # Status effects
        if "status" in block:
            msg = defender.apply_status_effect(block["status"])
            if msg: context.events.append({"type": "status", "message": msg, "target": "opponent" if context.is_player_attacking else "player"})
            
        # Volatile status
        if "volatileStatus" in block:
            if block["volatileStatus"] == "flinch" and getattr(defender, "acted_this_turn", False):
                return
            msg = defender.apply_volatile_status(block["volatileStatus"])
            if msg: context.events.append({"type": "status", "message": msg, "target": "opponent" if context.is_player_attacking else "player"})
            
        # Stat boosts
        if "boosts" in block:
            for stat, stage in block["boosts"].items():
                msg = defender.modify_stat_stage(stat, stage)
                if msg: context.events.append({"type": "status", "message": msg, "target": "opponent" if context.is_player_attacking else "player"})

    # Process single secondary
    if "secondary" in move.data and move.data["secondary"]:
        process_block(move.data["secondary"])
        
    # Process multiple secondaries
    if "secondaries" in move.data and move.data["secondaries"]:
        for block in move.data["secondaries"]:
            process_block(block)

def weather_residual_effects(context: BattleContext) -> None:
    game = context.game
    if game.weather == "none":
        return
        
    for p in [game.player_pokemon, game.opponent_pokemon]:
        if not p or p.current_hp <= 0:
            continue
            
        # Sandstorm chip damage
        if game.weather == "sandstorm":
            immune_types = ["rock", "ground", "steel"]
            if not any(t in p.types for t in immune_types) and not p.has_ability("sandveil") and not p.has_ability("sandrush") and not p.has_ability("magicguard"):
                damage = p.max_hp // 16
                p.take_damage(damage)
                context.events.append({
                    "type": "status",
                    "message": f"{game._get_pokemon_name(p)} is buffeted by the sandstorm!",
                    "target": "player" if p == game.player_pokemon else "opponent",
                    "pokemon_hp": p.current_hp
                })
        
        # Snow/Hail chip damage (Snow in Gen 9 doesn't chip, but let's assume Hail logic if we want)
        elif game.weather == "hail":
            if "ice" not in p.types and not p.has_ability("icebody") and not p.has_ability("snowcloak") and not p.has_ability("magicguard"):
                damage = p.max_hp // 16
                p.take_damage(damage)
                context.events.append({
                    "type": "status",
                    "message": f"{game._get_pokemon_name(p)} is buffeted by the hail!",
                    "target": "player" if p == game.player_pokemon else "opponent",
                    "pokemon_hp": p.current_hp
                })

def self_effects_on_hit(context: BattleContext) -> None:
    move = context.move
    attacker = context.attacker
    if not move or context.actual_damage <= 0:
        return
    
    if "self" in move.data and move.data["self"]:
        block = move.data["self"]
        # Stat boosts for self
        if "boosts" in block:
            for stat, stage in block["boosts"].items():
                msg = attacker.modify_stat_stage(stat, stage)
                if msg: context.events.append({"type": "status", "message": msg, "target": "player" if context.is_player_attacking else "opponent"})

def status_residual_effects(context: BattleContext) -> None:
    game = context.game
    for p in [game.player_pokemon, game.opponent_pokemon]:
        if not p or p.current_hp <= 0:
            continue
        
        # Use the existing StatusEffect system logic
        msgs = p.process_turn_end_effects()
        for msg in msgs:
            context.events.append({
                "type": "status",
                "message": msg,
                "target": "player" if p == game.player_pokemon else "opponent",
                "pokemon_hp": p.current_hp
            })

def item_residual_effects(context: BattleContext) -> None:
    game = context.game
    for p in [game.player_pokemon, game.opponent_pokemon]:
        if not p or p.current_hp <= 0 or not p.item_obj:
            continue
            
        # Use the existing Item system logic
        item_events = p.item_obj.on_residual(p)
        for event in item_events:
            # Normalize event target and HP for frontend
            normalized_event = {
                **event,
                "target": "player" if p == game.player_pokemon else "opponent",
                "pokemon_hp": p.current_hp
            }
            context.events.append(normalized_event)

def ability_residual_effects(context: BattleContext) -> None:
    game = context.game
    for p in [game.player_pokemon, game.opponent_pokemon]:
        if not p or p.current_hp <= 0:
            continue
        
        opponent = game.opponent_pokemon if p == game.player_pokemon else game.player_pokemon
        ability_events = p.on_turn_end(opponent)
        for event in ability_events:
            normalized_event = {
                **event,
                "target": "player" if p == game.player_pokemon else "opponent",
                "pokemon_hp": p.current_hp
            }
            context.events.append(normalized_event)

def entry_hazards_on_switch_in(context: BattleContext) -> None:
    game = context.game
    pokemon = context.attacker
    side = game.player_side if pokemon.is_player else game.opponent_side
    hazard_msgs = side.apply_entry_hazards(pokemon)
    for msg in hazard_msgs:
        context.events.append({
            "type": "status",
            "message": msg,
            "target": "player" if pokemon.is_player else "opponent",
            "pokemon_hp": pokemon.current_hp
        })

def ability_on_switch_in(context: BattleContext) -> None:
    pokemon = context.attacker
    opponent = context.defender
    ability_msgs = pokemon.on_switch_in(opponent)
    for msg in ability_msgs:
        if "set_weather" in msg:
            context.game.set_weather(msg["set_weather"], 5)
        
        is_p = pokemon.is_player
        normalized_msg = {
            **msg,
            "target": "player" if is_p else "opponent",
            "is_player": is_p,
            "player_hp": context.game.player_pokemon.current_hp,
            "opponent_hp": context.game.opponent_pokemon.current_hp,
        }
        context.events.append(normalized_msg)

def ability_on_faint(context: BattleContext) -> None:
    attacker = context.attacker
    defender = context.defender
    
    # Victory effects (e.g. Moxie, Beast Boost)
    if attacker and attacker.current_hp > 0:
        victory_msgs = attacker.on_victory(defender)
        for msg in victory_msgs:
            context.events.append({
                **msg,
                "target": "player" if attacker.is_player else "opponent",
                "is_player": attacker.is_player,
            })
            
    # Any-faint effects
    for p in [context.game.player_pokemon, context.game.opponent_pokemon]:
        if p and p.current_hp > 0:
            any_faint_msgs = p.on_any_faint()
            for msg in any_faint_msgs:
                context.events.append({
                    **msg,
                    "target": "player" if p.is_player else "opponent",
                    "is_player": p.is_player,
                })

def check_all_forme_changes(context: BattleContext) -> None:
    game = context.game
    from ..utils.pokemon_api import get_forme_data
    
    for pokemon in [game.player_pokemon, game.opponent_pokemon]:
        if not pokemon or pokemon.current_hp <= 0 or not pokemon.ability:
            continue
            
        ability_id = pokemon.ability.id
        target_forme = None
        ability_name = None
        
        # 1. Castform (Forecast)
        if ability_id == "forecast" and "castform" in pokemon.name.lower():
            weather = game.weather.lower()
            if weather in ["sunny", "desolateland"]:
                if "sunny" not in pokemon.name.lower(): target_forme = "castform-sunny"
            elif weather in ["rainy", "primordialsea"]:
                if "rainy" not in pokemon.name.lower(): target_forme = "castform-rainy"
            elif weather in ["hail", "snow"]:
                if "snowy" not in pokemon.name.lower(): target_forme = "castform-snowy"
            else:
                if pokemon.name.lower() != "castform": target_forme = "castform"
            ability_name = "Forecast"

        # 2. Cherrim (Flower Gift)
        elif ability_id == "flowergift" and "cherrim" in pokemon.name.lower():
            weather = game.weather.lower()
            if weather in ["sunny", "desolateland"]:
                if "sunshine" not in pokemon.name.lower(): target_forme = "cherrim-sunshine"
            else:
                if "sunshine" in pokemon.name.lower(): target_forme = "cherrim"
            ability_name = "Flower Gift"

        # 3. Wishiwashi (Schooling)
        elif ability_id == "schooling" and "wishiwashi" in pokemon.name.lower():
            if pokemon.level >= 20:
                if pokemon.current_hp > pokemon.max_hp / 4:
                    if "school" not in pokemon.name.lower(): target_forme = "wishiwashi-school"
                else:
                    if "school" in pokemon.name.lower(): target_forme = "wishiwashi-solo"
            ability_name = "Schooling"

        # 4. Minior (Shields Down)
        elif ability_id == "shieldsdown" and "minior" in pokemon.name.lower():
            # Get color from name (e.g. minior-red-meteor -> red)
            parts = pokemon.name.lower().split('-')
            color = parts[1] if len(parts) > 1 else "red"
            if color == "meteor": color = "red" # Fallback
            
            if pokemon.current_hp < pokemon.max_hp / 2:
                if "meteor" in pokemon.name.lower(): target_forme = f"minior-{color}"
            else:
                if "meteor" not in pokemon.name.lower(): target_forme = f"minior-{color}-meteor"
            ability_name = "Shields Down"

        # 5. Eiscue (Ice Face) - Weather recovery
        elif ability_id == "iceface" and "eiscue" in pokemon.name.lower():
            weather = game.weather.lower()
            if weather in ["hail", "snow"] and "noice" in pokemon.name.lower():
                target_forme = "eiscue-ice"
                ability_name = "Ice Face"

        if target_forme:
            side = 'back' if pokemon == game.player_pokemon else 'front'
            forme_data = get_forme_data(target_forme, side=side)
            if forme_data:
                pokemon.forme_change(
                    new_name=forme_data['name'],
                    new_types=forme_data['types'],
                    new_sprite=forme_data['sprite_url'],
                    new_stats=forme_data['stats'],
                    new_cry=forme_data['cry_url']
                )
                context.events.append({
                    "type": "ability",
                    "ability_name": ability_name,
                    "pokemon_name": game._get_pokemon_name(pokemon),
                    "message": f"{game._get_pokemon_name(pokemon)} transformed!",
                    "target": "player" if pokemon == game.player_pokemon else "opponent",
                    "is_player": pokemon == game.player_pokemon,
                    "new_sprite": pokemon.sprite_url,
                    "new_name": pokemon.name
                })

def disguise_try_hit(context: BattleContext) -> None:
    defender = context.defender
    move = context.move
    if not defender or not defender.ability or defender.ability.id != "disguise" or not move:
        return
    if "mimikyu" not in defender.name.lower() or "busted" in defender.name.lower():
        return
    if move.category not in ["physical", "special"] or move.flags.get('futuremove'):
        return
        
    # Disguise blocks the hit
    context.flags["move_blocked"] = True
    from ..utils.pokemon_api import get_forme_data
    side = 'back' if defender == context.game.player_pokemon else 'front'
    forme_data = get_forme_data("mimikyu-busted", side=side)
    if forme_data:
        defender.forme_change(forme_data['name'], forme_data['types'], forme_data['sprite_url'], forme_data['stats'], forme_data['cry_url'])
        # Take 1/8 max HP damage as per Gen 8+ logic
        damage = defender.max_hp // 8
        defender.take_damage(damage)
        
        context.events.append({
            "type": "ability",
            "ability_name": "Disguise",
            "pokemon_name": context.game._get_pokemon_name(defender),
            "message": f"Mimikyu's disguise was busted!",
            "target": "player" if defender == context.game.player_pokemon else "opponent",
            "is_player": defender == context.game.player_pokemon,
            "new_sprite": defender.sprite_url,
            "new_name": defender.name,
            "pokemon_hp": defender.current_hp
        })

def iceface_try_hit(context: BattleContext) -> None:
    defender = context.defender
    move = context.move
    if not defender or not defender.ability or defender.ability.id != "iceface" or not move:
        return
    if "eiscue" not in defender.name.lower() or "noice" in defender.name.lower():
        return
    if move.category != "physical":
        return
        
    # Ice Face blocks the physical hit
    context.flags["move_blocked"] = True
    from ..utils.pokemon_api import get_forme_data
    side = 'back' if defender == context.game.player_pokemon else 'front'
    forme_data = get_forme_data("eiscue-noice", side=side)
    if forme_data:
        defender.forme_change(forme_data['name'], forme_data['types'], forme_data['sprite_url'], forme_data['stats'], forme_data['cry_url'])
        context.events.append({
            "type": "ability",
            "ability_name": "Ice Face",
            "pokemon_name": context.game._get_pokemon_name(defender),
            "message": f"Eiscue's ice face shattered!",
            "target": "player" if defender == context.game.player_pokemon else "opponent",
            "is_player": defender == context.game.player_pokemon,
            "new_sprite": defender.sprite_url,
            "new_name": defender.name
        })

def relic_song_on_hit(context: BattleContext) -> None:
    attacker = context.attacker
    move = context.move
    if not attacker or not move or move.name.lower() != "relic song":
        return
    if "meloetta" not in attacker.name.lower() or context.actual_damage <= 0:
        return
        
    from ..utils.pokemon_api import get_forme_data
    target_forme = "meloetta-pirouette" if "-pirouette" not in attacker.name.lower() else "meloetta-aria"
    side = 'back' if attacker == context.game.player_pokemon else 'front'
    forme_data = get_forme_data(target_forme, side=side)
    if forme_data:
        attacker.forme_change(forme_data['name'], forme_data['types'], forme_data['sprite_url'], forme_data['stats'], forme_data['cry_url'])
        context.events.append({
            "type": "status",
            "message": f"Meloetta transformed into its {'Pirouette' if 'pirouette' in target_forme else 'Aria'} Forme!",
            "target": "player" if attacker == context.game.player_pokemon else "opponent",
            "new_sprite": attacker.sprite_url,
            "new_name": attacker.name
        })

def primal_reversion_on_switch_in(context: BattleContext) -> None:
    game = context.game
    attacker = context.attacker # The pokemon switching in
    if not attacker:
        return
        
    is_player = attacker == game.player_pokemon
    if game.can_primal_revert(is_player):
        # We need to simulate the turn_info to collect events
        temp_turn_info = {'battle_events': []}
        game.perform_primal_reversion(is_player, temp_turn_info)
        context.events.extend(temp_turn_info['battle_events'])

def register_builtin_hooks(registry) -> None:
    registry.register("switchIn", entry_hazards_on_switch_in)
    registry.register("switchIn", primal_reversion_on_switch_in)
    registry.register("switchIn", ability_on_switch_in)
    registry.register("switchIn", check_all_forme_changes)
    registry.register("faint", ability_on_faint)
    registry.register("beforeMove", stance_change_before_move)
    registry.register("tryHit", ohko_try_hit)
    registry.register("tryHit", sturdy_try_hit)
    registry.register("tryHit", disguise_try_hit)
    registry.register("tryHit", iceface_try_hit)
    registry.register("accuracy", ohko_accuracy)
    registry.register("damage", ohko_damage)
    registry.register("damage", sturdy_damage)
    registry.register("onHit", eject_button_on_hit)
    registry.register("onHit", recoil_on_hit)
    registry.register("onHit", healing_on_hit)
    registry.register("onHit", self_effects_on_hit)
    registry.register("onHit", relic_song_on_hit)
    registry.register("onHit", check_all_forme_changes)
    registry.register("secondary", secondary_effects_on_hit)
    registry.register("afterMove", self_switch_after_move)
    registry.register("residual", hunger_switch_residual)
    registry.register("residual", check_all_forme_changes)
    registry.register("residual", weather_residual_effects)
    registry.register("residual", status_residual_effects)
    registry.register("residual", item_residual_effects)
    registry.register("residual", ability_residual_effects)
