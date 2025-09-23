#!/usr/bin/env python3
"""
Test script to verify priority messaging functionality
"""

from game import Game
from data_loader import data_loader
import requests

def get_pokemon_data(pokemon_name):
    url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'Pokémon {pokemon_name} not found!')

def create_test_moves():
    """Create test moves with different priorities"""
    from move import Move
    
    # Create Extreme Speed (priority +2)
    extreme_speed = Move("Extreme Speed", "normal", 80, 5, 100, "physical")
    extreme_speed.priority = 2
    
    # Create Quick Attack (priority +1)
    quick_attack = Move("Quick Attack", "normal", 40, 30, 100, "physical")
    quick_attack.priority = 1
    
    # Create Sucker Punch (priority +1, priority counter)
    sucker_punch = Move("Sucker Punch", "dark", 70, 5, 100, "physical")
    sucker_punch.priority = 1
    sucker_punch.is_priority_counter = True
    
    # Create Tackle (priority 0)
    tackle = Move("Tackle", "normal", 40, 35, 100, "physical")
    tackle.priority = 0
    
    return {
        "Extreme Speed": extreme_speed,
        "Quick Attack": quick_attack,
        "Sucker Punch": sucker_punch,
        "Tackle": tackle
    }

def test_priority_messaging():
    """Test priority messaging functionality"""
    print("=== TESTING PRIORITY MESSAGING ===")
    
    try:
        # Get Pokemon data
        player_data = get_pokemon_data('pikachu')
        opponent_data = get_pokemon_data('charizard')
        
        # Create test moves
        test_moves = create_test_moves()
        player_moves = [
            {'name': 'Extreme Speed', 'power': 80, 'type': 'normal', 'pp': 5, 'max_pp': 5},
            {'name': 'Quick Attack', 'power': 40, 'type': 'normal', 'pp': 30, 'max_pp': 30},
            {'name': 'Sucker Punch', 'power': 70, 'type': 'dark', 'pp': 5, 'max_pp': 5},
            {'name': 'Tackle', 'power': 40, 'type': 'normal', 'pp': 35, 'max_pp': 35}
        ]
        
        opponent_moves = [
            {'name': 'Tackle', 'power': 40, 'type': 'normal', 'pp': 35, 'max_pp': 35},
            {'name': 'Quick Attack', 'power': 40, 'type': 'normal', 'pp': 30, 'max_pp': 30}
        ]
        
        # Initialize game
        game = Game()
        game.start_battle(player_data, opponent_data, player_moves, opponent_moves)
        
        # Test 1: Extreme Speed vs Tackle (should show priority explanation)
        print("\n--- Test 1: Extreme Speed vs Tackle ---")
        turn_info = game.process_turn("Extreme Speed")
        
        print("Battle events:")
        for event in turn_info.get('battle_events', []):
            print(f"  {event['type']}: {event.get('message', 'N/A')}")
        
        # Reset game for next test
        game = Game()
        game.start_battle(player_data, opponent_data, player_moves, opponent_moves)
        
        # Test 2: Sucker Punch vs Tackle (should show priority counter)
        print("\n--- Test 2: Sucker Punch vs Tackle ---")
        turn_info = game.process_turn("Sucker Punch")
        
        print("Battle events:")
        for event in turn_info.get('battle_events', []):
            print(f"  {event['type']}: {event.get('message', 'N/A')}")
        
        print("\n=== PRIORITY MESSAGING TEST COMPLETED ===")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_priority_messaging()