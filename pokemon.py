from move import Move
from data_loader import data_loader

class Pokemon:
    def __init__(self, name, type_, sprite_url, stats, moves=None, level=100):
        self.name = name
        self.type = type_
        self.sprite_url = sprite_url
        self.level = level
        self.max_hp = int(((stats[0]['base_stat'] * 2) * self.level / 100) + self.level + 10)
        self.current_hp = self.max_hp
        self.attack = int(((stats[1]['base_stat'] * 2) * self.level / 100) + 5)
        self.defense = int(((stats[2]['base_stat'] * 2) * self.level / 100) + 5)
        self.speed = int(((stats[5]['base_stat'] * 2) * self.level / 100) + 5)
        
        # Use dataset moves if no moves provided
        if moves is None:
            available_moves = data_loader.get_pokemon_moves(self.name.lower(), 4)
            self.moves = {}
            for move_name in available_moves:
                move_power = data_loader.get_move_power(move_name)
                move_type = data_loader.get_move_type(move_name)
                self.moves[move_name] = Move(move_name, move_power, 10, move_type)
        else:
            # Use provided moves but enhance with dataset data
            self.moves = {}
            for move in moves:
                move_name = move['name']
                move_power = data_loader.get_move_power(move_name) or move.get('power', 50)
                move_type = data_loader.get_move_type(move_name)
                self.moves[move_name] = Move(move_name, move_power, 10, move_type)
        #scaled to level 100 (since pokeapi wasnt setting pokemons to level 100 automatically for some reason)

    def take_damage(self, damage):
        self.current_hp -= damage
        if self.current_hp < 0:
            self.current_hp = 0

    def is_fainted(self):
        return self.current_hp <= 0
