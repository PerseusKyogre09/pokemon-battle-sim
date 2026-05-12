import random
from typing import Any, Dict, Optional

from .smogon_oracle import smogon_damage_oracle


STATUS_TO_SMOGON = {
    "burn": "brn",
    "paralysis": "par",
    "poison": "psn",
    "toxic": "tox",
    "sleep": "slp",
    "freeze": "frz",
}

WEATHER_TO_SMOGON = {
    "raindance": "Rain",
    "sunnyday": "Sun",
    "sandstorm": "Sand",
    "hail": "Snow",
    "snow": "Snow",
    "primordialsea": "Primordial Sea",
    "desolateland": "Desolate Land",
    "deltastream": "Delta Stream",
    "none": None,
}

STAT_TO_SMOGON = {
    "attack": "atk",
    "defense": "def",
    "special_attack": "spa",
    "special_defense": "spd",
    "speed": "spe",
}


def _clean_name(value: Any) -> Optional[str]:
    if not value:
        return None
    text = str(value)
    if text.lower().replace(" ", "").replace("-", "") in {"", "none", "noability", "unknown"}:
        return None
    return text


def _normalize_spread(values: Dict[str, int] | None, default: int) -> Dict[str, int]:
    values = values or {}
    result = {}
    for key in ["hp", "atk", "def", "spa", "spd", "spe"]:
        long_key = {
            "atk": "attack",
            "def": "defense",
            "spa": "special_attack",
            "spd": "special_defense",
            "spe": "speed",
        }.get(key, key)
        result[key] = int(values.get(key, values.get(long_key, default)))
    return result


def _pokemon_payload(pokemon) -> Dict[str, Any]:
    ability = _clean_name(getattr(getattr(pokemon, "ability", None), "name", None))
    item = _clean_name(getattr(pokemon, "item", None))
    boosts = {}
    for stat, stage in getattr(pokemon, "stat_stages", {}).items():
        key = STAT_TO_SMOGON.get(stat)
        if key:
            boosts[key] = int(stage)

    return {
        "species": getattr(pokemon, "name", "Pikachu"),
        "level": getattr(pokemon, "level", 100),
        "ability": ability,
        "item": item,
        "nature": getattr(pokemon, "nature", "Hardy"),
        "evs": _normalize_spread(getattr(pokemon, "evs", {}), 0),
        "ivs": _normalize_spread(getattr(pokemon, "ivs", {}), 31),
        "boosts": boosts,
        "status": STATUS_TO_SMOGON.get(getattr(pokemon, "major_status", None)),
    }


def smogon_damage_for_move(attacker, defender, move, field: Dict[str, Any] | None = None) -> Optional[Dict[str, Any]]:
    if getattr(move, "fixed_damage", None) or getattr(move, "ohko", False):
        return None
    if getattr(move, "category", "status") == "status" or getattr(move, "power", 0) <= 0:
        return None

    field = field or {}
    gen = field.get("gen", 9)
    
    # Mega Evolution is not standard in Gen 9, use Gen 7 for Megas to ensure support
    attacker_name = getattr(attacker, "name", "").lower()
    defender_name = getattr(defender, "name", "").lower()
    if "-mega" in attacker_name or "-mega" in defender_name:
        gen = 7

    payload = {
        "gen": gen,
        "attacker": _pokemon_payload(attacker),
        "defender": _pokemon_payload(defender),
        "move": {"name": getattr(move, "name", "")},
        "field": {
            "weather": WEATHER_TO_SMOGON.get(field.get("weather"), field.get("weather")),
            "terrain": field.get("terrain"),
            "isReflect": bool(field.get("is_reflect")),
            "isLightScreen": bool(field.get("is_light_screen")),
            "isAuroraVeil": bool(field.get("is_aurora_veil")),
        },
    }
    result = smogon_damage_oracle.calculate(payload)
    if not result or result.get("error") or not result.get("damage"):
        return None
    result["selected_damage"] = random.choice(result["damage"])
    return result
