import unittest
from unittest.mock import patch

from backend.src.core.game import Game
from backend.src.core.hooks import BattleContext
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


def mon(name, types, moves, level=100, ability="noability", item="", speed=100):
    stats = BASE_STATS.copy()
    stats["speed"] = speed
    return {
        "name": name,
        "types": types,
        "stats": stats,
        "moves": moves,
        "level": level,
        "ability": ability,
        "item": item,
    }


class MechanicsFlowTests(unittest.TestCase):
    @patch("backend.src.models.move.random.randint", return_value=100)
    @patch("backend.src.models.move.random.random", return_value=1.0)
    def test_player_self_switch_move_queues_switch_choice(self, _random, _randint):
        game = Game()
        game.start_battle(
            [
                mon("Scizor", ["bug", "steel"], ["U-turn"], speed=200),
                mon("Pikachu", ["electric"], ["Tackle"]),
            ],
            [mon("Snorlax", ["normal"], ["Tackle"], speed=50)],
        )

        result = game.process_turn(move_name="U-turn")

        self.assertTrue(game.pending_player_self_switch)
        self.assertTrue(any(e.get("type") == "pending_switch" for e in result["battle_events"]))

    @patch("backend.src.models.move.random.randint", return_value=100)
    @patch("backend.src.models.move.random.random", return_value=1.0)
    def test_eject_button_suppresses_user_self_switch(self, _random, _randint):
        game = Game()
        game.start_battle(
            [
                mon("Scizor", ["bug", "steel"], ["U-turn"], speed=200),
                mon("Pikachu", ["electric"], ["Tackle"]),
            ],
            [
                mon("Snorlax", ["normal"], ["Tackle"], item="Eject Button", speed=50),
                mon("Blissey", ["normal"], ["Tackle"]),
            ],
        )

        result = game.process_turn(move_name="U-turn")

        self.assertFalse(game.pending_player_self_switch)
        self.assertEqual(game.opponent_pokemon.name, "Blissey")
        self.assertTrue(any(e.get("item_name") == "Eject Button" for e in result["battle_events"]))

    @patch("backend.src.core.game.random.randint", return_value=1)
    def test_ohko_move_fails_against_higher_level_target(self, _randint):
        game = Game()
        attacker = Pokemon("Dugtrio", ["ground"], None, BASE_STATS.copy(), moves=[], level=50)
        defender = Pokemon("Snorlax", ["normal"], None, BASE_STATS.copy(), moves=[], level=51)
        
        # Setup game state
        game.player_pokemon = attacker
        game.opponent_pokemon = defender
        
        move = Move("Fissure")
        move.ohko = True
        
        turn_info = {'battle_events': []}
        # execute_move will trigger ohko_try_hit hook
        fainted = game.execute_move(attacker, defender, move, "Fissure", True, turn_info)
        
        self.assertFalse(fainted)
        self.assertTrue(any("But it failed!" in e.get("message", "") for e in turn_info['battle_events']))

    def test_hunger_switch_changes_morpeko_form_at_turn_end(self):
        game = Game()
        pokemon = Pokemon(
            "Morpeko",
            ["electric", "dark"],
            None,
            BASE_STATS.copy(),
            moves=[],
            level=100,
            ability="Hunger Switch",
        )
        # Mock ability object if needed, but here we just need the id
        from collections import namedtuple
        Ability = namedtuple('Ability', ['id', 'name', 'on_turn_end'])
        pokemon.ability = Ability('hungerswitch', 'Hunger Switch', lambda p, o: [])
        
        game.player_pokemon = pokemon
        game.opponent_pokemon = Pokemon("Dummy", ["normal"], None, BASE_STATS.copy(), moves=[], level=100)
        
        context = BattleContext(game=game, phase='residual')
        game.hooks.run('residual', context)

        self.assertEqual(pokemon.name, "Morpeko-Hangry")
        self.assertTrue(any(e.get("ability_name") == "Hunger Switch" for e in context.events))

if __name__ == "__main__":
    unittest.main()
