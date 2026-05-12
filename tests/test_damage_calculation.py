import unittest
from unittest.mock import patch

from backend.src.models.move import Move
from backend.src.models.pokemon import Pokemon


BASE_STATS = {
    "hp": 100,
    "attack": 100,
    "defense": 100,
    "special_attack": 100,
    "special_defense": 100,
    "speed": 100,
}


def make_pokemon(name, types, level=100, item="", ability="noability"):
    return Pokemon(
        name,
        types,
        None,
        BASE_STATS.copy(),
        moves=[],
        level=level,
        ability=ability,
        item=item,
    )


class DamageCalculationTests(unittest.TestCase):
    @patch("backend.src.models.move.random.randint", return_value=100)
    @patch("backend.src.models.move.random.random", return_value=1.0)
    def test_damage_uses_attacker_level(self, _random, _randint):
        defender = make_pokemon("Snorlax", ["normal"], level=100)
        level_50_attacker = make_pokemon("Pikachu", ["electric"], level=50)
        level_100_attacker = make_pokemon("Pikachu", ["electric"], level=100)

        low_damage = Move("Tackle").use_move(level_50_attacker, defender)[0]
        high_damage = Move("Tackle").use_move(level_100_attacker, defender)[0]

        self.assertGreater(high_damage, low_damage)

    @patch("backend.src.models.move.random.randint", return_value=85)
    @patch("backend.src.models.move.random.random", return_value=0.0)
    def test_fixed_damage_ignores_random_critical_and_stab_modifiers(self, _random, _randint):
        attacker = make_pokemon("Dragonite", ["dragon"], level=100)
        defender = make_pokemon("Blissey", ["normal"], level=100)

        damage = Move("Dragon Rage").use_move(attacker, defender)[0]

        self.assertEqual(damage, 40)

    def test_fixed_damage_respects_type_immunity(self):
        attacker = make_pokemon("Gengar", ["ghost"], level=100)
        defender = make_pokemon("Blissey", ["normal"], level=100)

        damage, _, message, _, _ = Move("Night Shade").use_move(attacker, defender)

        self.assertEqual(damage, 0)
        self.assertEqual(message, "It had no effect...")

    @patch("backend.src.models.move.random.randint", return_value=100)
    @patch("backend.src.models.move.random.random", return_value=1.0)
    def test_effectiveness_is_available_to_damage_modifying_items(self, _random, _randint):
        attacker = make_pokemon("Pikachu", ["electric"], level=100, item="Expert Belt")
        defender = make_pokemon("Squirtle", ["water"], level=100)
        move = Move("Thunderbolt")

        raw_damage = move.use_move(attacker, defender)[0]
        boosted_damage = attacker.item_obj.modify_damage_dealt(attacker, defender, move, raw_damage)

        self.assertEqual(move.effectiveness, 2.0)
        self.assertEqual(boosted_damage, int(raw_damage * 1.2))

    @patch("backend.src.models.move.random.randint", return_value=100)
    @patch("backend.src.models.move.random.random", return_value=1.0)
    def test_single_hit_damage_is_absorbed_by_substitute(self, _random, _randint):
        attacker = make_pokemon("Pikachu", ["electric"], level=100)
        defender = make_pokemon("Snorlax", ["normal"], level=100)
        defender.substitute_hp = defender.max_hp // 4
        starting_substitute_hp = defender.substitute_hp

        damage, substitute_damage, _, _, _ = Move("Tackle").use_move(attacker, defender)

        self.assertEqual(damage, 0)
        self.assertGreater(substitute_damage, 0)
        self.assertEqual(defender.substitute_hp, starting_substitute_hp - substitute_damage)

    @patch("backend.src.models.move.random.randint", return_value=100)
    @patch("backend.src.models.move.random.random", return_value=1.0)
    def test_choice_band_is_not_applied_twice(self, _random, _randint):
        defender = make_pokemon("Snorlax", ["normal"], level=100)
        no_item_attacker = make_pokemon("Tauros", ["normal"], level=100)
        band_attacker = make_pokemon("Tauros", ["normal"], level=100, item="Choice Band")

        normal_damage = Move("Tackle").use_move(no_item_attacker, defender)[0]
        band_damage = Move("Tackle").use_move(band_attacker, defender)[0]

        self.assertLess(band_damage, normal_damage * 2)

    @patch("backend.src.models.move.random.randint", return_value=100)
    @patch("backend.src.models.move.random.random", return_value=1.0)
    def test_burn_halves_physical_damage_once(self, _random, _randint):
        defender = make_pokemon("Snorlax", ["normal"], level=100)
        healthy_attacker = make_pokemon("Tauros", ["normal"], level=100)
        burned_attacker = make_pokemon("Tauros", ["normal"], level=100)
        burned_attacker.apply_status_effect("brn")

        healthy_damage = Move("Tackle").use_move(healthy_attacker, defender)[0]
        burned_damage = Move("Tackle").use_move(burned_attacker, defender)[0]

        self.assertEqual(burned_damage, healthy_damage // 2)

    @patch("backend.src.models.move.random.randint", return_value=100)
    @patch("backend.src.models.move.random.random", return_value=0.0)
    def test_critical_hit_ignores_bad_attack_and_good_defense_stages(self, _random, _randint):
        attacker = make_pokemon("Tauros", ["normal"], level=100)
        defender = make_pokemon("Snorlax", ["normal"], level=100)
        attacker.modify_stat_stage("attack", -6)
        defender.modify_stat_stage("defense", 6)

        damage = Move("Storm Throw").use_move(attacker, defender)[0]

        self.assertGreater(damage, 20)


if __name__ == "__main__":
    unittest.main()
