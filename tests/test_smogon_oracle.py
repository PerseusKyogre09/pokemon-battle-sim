import unittest

from backend.src.systems.smogon_oracle import smogon_damage_oracle
from backend.src.models.move import Move
from backend.src.models.pokemon import Pokemon


class SmogonOracleTests(unittest.TestCase):
    def test_smogon_damage_oracle_returns_damage_range(self):
        if not smogon_damage_oracle.is_available():
            self.skipTest("@smogon/calc is not installed")

        result = smogon_damage_oracle.calculate({
            "gen": 9,
            "attacker": {
                "species": "Pikachu",
                "level": 100,
                "ability": "Static",
                "nature": "Hardy",
            },
            "defender": {
                "species": "Squirtle",
                "level": 100,
                "ability": "Torrent",
                "nature": "Hardy",
            },
            "move": {"name": "Thunderbolt"},
            "field": {},
        })

        self.assertIsInstance(result, dict)
        self.assertGreater(result["min"], 0)
        self.assertGreaterEqual(result["max"], result["min"])
        self.assertEqual(len(result["damage"]), 16)

    def test_move_can_use_smogon_damage_provider(self):
        if not smogon_damage_oracle.is_available():
            self.skipTest("@smogon/calc is not installed")

        stats = {
            "hp": 35,
            "attack": 55,
            "defense": 40,
            "special_attack": 50,
            "special_defense": 50,
            "speed": 90,
        }
        attacker = Pokemon("Pikachu", ["electric"], None, stats.copy(), moves=[], level=100, ability="Static")
        defender = Pokemon("Squirtle", ["water"], None, {
            "hp": 44,
            "attack": 48,
            "defense": 65,
            "special_attack": 50,
            "special_defense": 64,
            "speed": 43,
        }, moves=[], level=100, ability="Torrent")
        move = Move("Thunderbolt")

        damage = move.use_move(attacker, defender, field={"weather": "none"})[0]

        self.assertEqual(move.damage_source, "smogon")
        self.assertIsNotNone(move.last_damage_range)
        self.assertGreaterEqual(damage, move.last_damage_range[0])
        self.assertLessEqual(damage, move.last_damage_range[1])


if __name__ == "__main__":
    unittest.main()
