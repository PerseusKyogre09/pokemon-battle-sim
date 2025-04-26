from move import Move

class Pokemon:
    def __init__(self, name, type_, sprite_url, stats, moves, level=100):
        self.name = name
        self.type = type_
        self.sprite_url = sprite_url
        self.level = level
        
        # Scale stats based on level 100
        self.max_hp = int(((stats[0]['base_stat'] * 2) * self.level / 100) + self.level + 10)
        self.current_hp = self.max_hp
        self.attack = int(((stats[1]['base_stat'] * 2) * self.level / 100) + 5)
        self.defense = int(((stats[2]['base_stat'] * 2) * self.level / 100) + 5)
        self.speed = int(((stats[5]['base_stat'] * 2) * self.level / 100) + 5)

        # Initialize moves with power from PokeAPI
        self.moves = {move['name']: Move(move['name'], move['power'], 10) for move in moves}

    def take_damage(self, damage):
        self.current_hp -= damage
        if self.current_hp < 0:
            self.current_hp = 0

    def is_fainted(self):
        return self.current_hp <= 0
