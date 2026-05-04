from pokemon import Pokemon
from game import Game

def test_ability_automation():
    print("Testing Ability Automation...")
    
    # 1. Test Intimidate (Switch-in effect)
    # Pikachu vs Charizard (Intimidate)
    pikachu_stats = {'hp': 35, 'attack': 55, 'defense': 40, 'special_attack': 50, 'special_defense': 50, 'speed': 90}
    charizard_stats = {'hp': 78, 'attack': 84, 'defense': 78, 'special_attack': 109, 'special_defense': 85, 'speed': 100}
    
    game = Game()
    # Mocking data structures expected by start_battle
    p_data = {'name': 'Pikachu', 'types': [{'type': {'name': 'electric'}}], 'stats': pikachu_stats, 'sprites': {}}
    o_data = {'name': 'Charizard', 'types': [{'type': {'name': 'fire'}}, {'type': {'name': 'flying'}}], 'stats': charizard_stats, 'sprites': {}}
    
    print("\n--- Starting Battle: Pikachu vs Charizard (Intimidate) ---")
    messages = game.start_battle(p_data, o_data, [], [], player_ability="noability", opponent_ability="intimidate")
    
    print(f"Battle Start Messages: {messages}")
    print(f"Pikachu Attack Stage: {game.player_pokemon.stat_stages['attack']}")
    
    assert game.player_pokemon.stat_stages['attack'] == -1
    print("SUCCESS: Intimidate lowered Pikachu's attack!")

    # 2. Test Huge Power (Stat multiplier)
    print("\n--- Testing Huge Power ---")
    marill = Pokemon("Marill", "water", "", pikachu_stats, ability="hugepower")
    print(f"Marill Base Attack: {marill.base_stats['attack']}")
    print(f"Marill Calculated Attack (should be doubled): {marill.attack}")
    
    # Huge Power doubles Attack. 
    # Base calculation for level 100 is: ((base * 2) + 5) = (55 * 2 + 5) = 115
    # Doubled = 230
    assert marill.attack >= 200 # Roughly check it's boosted
    print(f"SUCCESS: Huge Power boosted attack! ({marill.attack})")

    # 3. Test Levitate (Immunity)
    print("\n--- Testing Levitate ---")
    from move import Move
    ghastly = Pokemon("Ghastly", "ghost", "", pikachu_stats, ability="levitate")
    earthquake = Move("Earthquake") # Ground type
    
    damage, msg, effect = earthquake.use_move(marill, ghastly)
    print(f"Earthquake vs Levitate Ghastly: {msg}")
    assert damage == 0
    assert "It had no effect" in msg
    print("SUCCESS: Levitate provided Ground immunity!")

    # 4. Test Blaze (Damage modifier)
    print("\n--- Testing Blaze ---")
    charizard = Pokemon("Charizard", "fire", "", charizard_stats, ability="blaze")
    flamethrower = Move("Flamethrower")
    
    # Normal health damage
    dmg_full, _, _ = flamethrower.use_move(charizard, marill)
    
    # Low health damage
    charizard.current_hp = 10
    dmg_low, _, _ = flamethrower.use_move(charizard, marill)
    
    print(f"Full HP Damage: {dmg_full}, Low HP (Blaze) Damage: {dmg_low}")
    assert dmg_low > dmg_full
    print("SUCCESS: Blaze boosted damage at low HP!")

if __name__ == "__main__":
    try:
        test_ability_automation()
        print("\nALL TESTS PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
