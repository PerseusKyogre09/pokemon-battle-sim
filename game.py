from pokemon import Pokemon

class Game:
    def __init__(self):
        self.player_pokemon = None
        self.opponent_pokemon = None
        self.battle_over = False
    def start_battle(self, player_data, opponent_data, player_moves, opponent_moves):
        # Get player's back sprite (prefer Gen 5 animated, fallback to default)
        player_sprite = (
            player_data['sprites'].get('versions', {})
            .get('generation-v', {})
            .get('black-white', {})
            .get('animated', {})
            .get('back_default') or 
            player_data['sprites'].get('back_default')
        )
        
        # Get opponent's front sprite (prefer Gen 5 animated, fallback to default)
        opponent_sprite = (
            opponent_data['sprites'].get('versions', {})
            .get('generation-v', {})
            .get('black-white', {})
            .get('animated', {})
            .get('front_default') or 
            opponent_data['sprites'].get('front_default')
        )
        
        # Extract types for both Pokémon
        player_types = [t['type']['name'] for t in player_data['types']]
        opponent_types = [t['type']['name'] for t in opponent_data['types']]
        
        print(f"DEBUG: Player {player_data['name']} types: {player_types}")
        print(f"DEBUG: Opponent {opponent_data['name']} types: {opponent_types}")
        
        # Create Pokémon instances with the selected sprites and types
        self.player_pokemon = Pokemon(
            player_data['name'], 
            player_types,  # Pass all types as a list
            player_sprite, 
            player_data['stats'], 
            player_moves
        )
        self.opponent_pokemon = Pokemon(
            opponent_data['name'], 
            opponent_types,  # Pass all types as a list
            opponent_sprite, 
            opponent_data['stats'], 
            opponent_moves
        )
        
        print(f"DEBUG: Player Pokémon created with types: {self.player_pokemon.types}")
        print(f"DEBUG: Opponent Pokémon created with types: {self.opponent_pokemon.types}")

    def process_turn(self, move_name):
        """
        Process a turn of battle, handling move execution, damage calculation,
        and effectiveness messages.
        
        Args:
            move_name: Name of the move the player is using
            
        Returns:
            dict: Dictionary containing turn information including effectiveness messages
        """
        turn_info = {
            'player_move': move_name,
            'player_damage': 0,
            'opponent_damage': 0,
            'effectiveness_messages': []
        }
        
        # Get player's selected move
        player_move = self.player_pokemon.moves.get(move_name)
        if not player_move or player_move.pp <= 0:
            return turn_info  # Invalid move or no PP left
                
        # Get opponent's move (AI always picks first move)
        opponent_move_name, opponent_move = next(iter(self.opponent_pokemon.moves.items()))
        turn_info['opponent_move'] = opponent_move_name
        
        # Check if opponent has PP left
        if opponent_move and opponent_move.pp <= 0:
            # If opponent has no PP, they struggle
            opponent_move = None
        
        # Determine who goes first based on speed
        player_first = self.player_pokemon.speed >= self.opponent_pokemon.speed
        turn_info['player_first'] = player_first
        
        def execute_move(attacker, defender, move, move_name, is_player_attacking):
            """Helper function to execute a move and return damage and effectiveness."""
            # Skip if no move (shouldn't happen, but just in case)
            if not move:
                return False
                
            damage, effectiveness_msg = move.use_move(attacker, defender)
            prev_hp = defender.current_hp
            defender.take_damage(damage)
            actual_damage = prev_hp - defender.current_hp
            
            # Log the move and damage
            if is_player_attacking:
                turn_info['player_damage'] = actual_damage
            else:
                turn_info['opponent_damage'] = actual_damage
                
            # Add effectiveness message if any
            if effectiveness_msg:
                turn_info['effectiveness_messages'].append(effectiveness_msg)
                
            print(f"DEBUG: {attacker.name} used {move_name}! {defender.name} lost {actual_damage} HP (Now: {defender.current_hp}/{defender.max_hp})")
            if effectiveness_msg:
                print(f"DEBUG: {effectiveness_msg}")
                
            # Decrement PP after successful move
            move.pp -= 1
            
            return defender.is_fainted()
        
        try:
            if player_first:
                # Player goes first
                if execute_move(self.player_pokemon, self.opponent_pokemon, player_move, move_name, True):
                    print(f"DEBUG: {self.opponent_pokemon.name} fainted!")
                    self.battle_over = True
                    return turn_info
                
                # Opponent goes second if they have PP and didn't faint
                if opponent_move and not self.battle_over:
                    if execute_move(self.opponent_pokemon, self.player_pokemon, opponent_move, opponent_move_name, False):
                        print(f"DEBUG: {self.player_pokemon.name} fainted!")
                        self.battle_over = True
            else:
                # Opponent goes first if they have PP
                if opponent_move:
                    if execute_move(self.opponent_pokemon, self.player_pokemon, opponent_move, opponent_move_name, False):
                        print(f"DEBUG: {self.player_pokemon.name} fainted!")
                        self.battle_over = True
                        return turn_info
                
                # Player goes second if not fainted
                if not self.battle_over:
                    if execute_move(self.player_pokemon, self.opponent_pokemon, player_move, move_name, True):
                        print(f"DEBUG: {self.opponent_pokemon.name} fainted!")
                        self.battle_over = True
        except Exception as e:
            print(f"Error during turn processing: {e}")
            
        return turn_info

    def is_battle_over(self):
        return self.player_pokemon.is_fainted() or self.opponent_pokemon.is_fainted()

    def get_battle_result(self):
        if self.player_pokemon.is_fainted():
            return f"Your {self.player_pokemon.name.capitalize()} fainted! Opponent's {self.opponent_pokemon.name.capitalize()} wins!"
        elif self.opponent_pokemon.is_fainted():
            return f"Opponent's {self.opponent_pokemon.name.capitalize()} fainted! Your {self.player_pokemon.name.capitalize()} wins!"
        return "The battle is ongoing."
