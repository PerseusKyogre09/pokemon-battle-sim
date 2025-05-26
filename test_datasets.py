"""
Test script to verify the TypeScript datasets integration is working properly.
"""

from data_loader import data_loader

def test_moves_data():
    """Test that moves data is loaded correctly."""
    print("Testing moves data...")
    
    # Test a common move
    tackle_data = data_loader.get_move_data('tackle')
    if tackle_data:
        print(f"✓ Tackle found: Power={tackle_data.get('basePower', 'N/A')}, Type={tackle_data.get('type', 'N/A')}")
    else:
        print("✗ Tackle not found in dataset")
    
    # Test move power function
    power = data_loader.get_move_power('tackle')
    print(f"✓ Tackle power via function: {power}")
    
    # Test move type function
    move_type = data_loader.get_move_type('tackle')
    print(f"✓ Tackle type via function: {move_type}")

def test_learnsets_data():
    """Test that learnsets data is loaded correctly."""
    print("\nTesting learnsets data...")
    
    # Test Pikachu's moves
    pikachu_moves = data_loader.get_pokemon_moves('pikachu', 5)
    if pikachu_moves:
        print(f"✓ Pikachu moves found: {pikachu_moves[:3]}...")
    else:
        print("✗ Pikachu moves not found")
    
    # Test Charmander's moves
    charmander_moves = data_loader.get_pokemon_moves('charmander', 5)
    if charmander_moves:
        print(f"✓ Charmander moves found: {charmander_moves[:3]}...")
    else:
        print("✗ Charmander moves not found")

def test_type_effectiveness():
    """Test that type effectiveness is working correctly."""
    print("\nTesting type effectiveness...")
    
    # Test some basic type matchups
    effectiveness_tests = [
        ('Water', 'Fire', 2.0),  # Water vs Fire should be 2x
        ('Fire', 'Water', 0.5),  # Fire vs Water should be 0.5x
        ('Electric', 'Water', 2.0),  # Electric vs Water should be 2x
        ('Ground', 'Electric', 2.0),  # Ground vs Electric should be 2x
        ('Electric', 'Ground', 0.0),  # Electric vs Ground should be 0x (immune)
    ]
    
    for attacking, defending, expected in effectiveness_tests:
        actual = data_loader.get_type_effectiveness(attacking, defending)
        if abs(actual - expected) < 0.01:  # Float comparison with tolerance
            print(f"✓ {attacking} vs {defending}: {actual}x (expected {expected}x)")
        else:
            print(f"✗ {attacking} vs {defending}: {actual}x (expected {expected}x)")

def test_data_loading():
    """Test that data was loaded successfully."""
    print("\nTesting data loading...")
    
    moves_count = len(data_loader.moves_data)
    learnsets_count = len(data_loader.learnsets_data)
    types_count = len(data_loader.typechart_data)
    
    print(f"✓ Loaded {moves_count} moves")
    print(f"✓ Loaded {learnsets_count} Pokemon learnsets")
    print(f"✓ Loaded {types_count} type effectiveness charts")
    
    if moves_count > 0 and learnsets_count > 0 and types_count > 0:
        print("✓ All datasets loaded successfully!")
    else:
        print("✗ Some datasets failed to load")

if __name__ == "__main__":
    print("Pokemon Dataset Integration Test")
    print("=" * 40)
    
    test_data_loading()
    test_moves_data()
    test_learnsets_data()
    test_type_effectiveness()
    
    print("\n" + "=" * 40)
    print("Test completed!")
