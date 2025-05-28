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
        
        # Create Pokémon instances with the selected sprites
        self.player_pokemon = Pokemon(
            player_data['name'], 
            player_data['types'][0]['type']['name'], 
            player_sprite, 
            player_data['stats'], 
            player_moves
        )
        self.opponent_pokemon = Pokemon(
            opponent_data['name'], 
            opponent_data['types'][0]['type']['name'], 
            opponent_sprite, 
            opponent_data['stats'], 
            opponent_moves
        )

    def process_turn(self, move_name):
        # Get player's selected move
        player_move = self.player_pokemon.moves.get(move_name)
        if not player_move or player_move.pp <= 0:
            return  # Invalid move or no PP left
                
        # Get opponent's move (AI always picks first move)
        opponent_move_name, opponent_move = next(iter(self.opponent_pokemon.moves.items()))
        
        # Check if opponent has PP left
        if opponent_move.pp <= 0:
            # If opponent has no PP, they struggle
            opponent_move = None
        
        # Determine who goes first based on speed
        if self.player_pokemon.speed >= self.opponent_pokemon.speed:
            # Player goes first
            player_damage = player_move.use_move(self.player_pokemon, self.opponent_pokemon)
            opponent_prev_hp = self.opponent_pokemon.current_hp
            self.opponent_pokemon.take_damage(player_damage)
            actual_damage = opponent_prev_hp - self.opponent_pokemon.current_hp
            print(f"DEBUG: {self.player_pokemon.name} used {move_name}! {self.opponent_pokemon.name} lost {actual_damage} HP (Now: {self.opponent_pokemon.current_hp}/{self.opponent_pokemon.max_hp})")
            player_move.pp -= 1  # Decrement PP after successful move
                
            # Check if opponent fainted
            if self.opponent_pokemon.is_fainted():
                print(f"DEBUG: {self.opponent_pokemon.name} fainted!")
                self.battle_over = True
                return
            
            # Opponent goes second if they have PP
            if opponent_move:
                opponent_damage = opponent_move.use_move(self.opponent_pokemon, self.player_pokemon)
                player_prev_hp = self.player_pokemon.current_hp
                self.player_pokemon.take_damage(opponent_damage)
                actual_damage = player_prev_hp - self.player_pokemon.current_hp
                print(f"DEBUG: {self.opponent_pokemon.name} used {opponent_move_name}! {self.player_pokemon.name} lost {actual_damage} HP (Now: {self.player_pokemon.current_hp}/{self.player_pokemon.max_hp})")
                opponent_move.pp -= 1  # Decrement PP after successful move
                
                # Check if player fainted
                if self.player_pokemon.is_fainted():
                    print(f"DEBUG: {self.player_pokemon.name} fainted!")
                    self.battle_over = True
                    return
        else:
            # Opponent goes first if they have PP
            if opponent_move:
                opponent_damage = opponent_move.use_move(self.opponent_pokemon, self.player_pokemon)
                player_prev_hp = self.player_pokemon.current_hp
                self.player_pokemon.take_damage(opponent_damage)
                actual_damage = player_prev_hp - self.player_pokemon.current_hp
                print(f"DEBUG: {self.opponent_pokemon.name} used {opponent_move_name}! {self.player_pokemon.name} lost {actual_damage} HP (Now: {self.player_pokemon.current_hp}/{self.player_pokemon.max_hp})")
                opponent_move.pp -= 1  # Decrement PP after successful move
                    
                # Check if player fainted
                if self.player_pokemon.is_fainted():
                    print(f"DEBUG: {self.player_pokemon.name} fainted!")
                    self.battle_over = True
                    return
            
            # Player goes second
            player_damage = player_move.use_move(self.player_pokemon, self.opponent_pokemon)
            opponent_prev_hp = self.opponent_pokemon.current_hp
            self.opponent_pokemon.take_damage(player_damage)
            actual_damage = opponent_prev_hp - self.opponent_pokemon.current_hp
            print(f"DEBUG: {self.player_pokemon.name} used {move_name}! {self.opponent_pokemon.name} lost {actual_damage} HP (Now: {self.opponent_pokemon.current_hp}/{self.opponent_pokemon.max_hp})")
            player_move.pp -= 1  # Decrement PP after successful move

        # Check if battle is over
        self.battle_over = self.is_battle_over()

    def is_battle_over(self):
        return self.player_pokemon.is_fainted() or self.opponent_pokemon.is_fainted()

    def get_battle_result(self):
        if self.player_pokemon.is_fainted():
            return f"Your {self.player_pokemon.name.capitalize()} fainted! Opponent's {self.opponent_pokemon.name.capitalize()} wins!"
        elif self.opponent_pokemon.is_fainted():
            return f"Opponent's {self.opponent_pokemon.name.capitalize()} fainted! Your {self.player_pokemon.name.capitalize()} wins!"
        return "The battle is ongoing."
