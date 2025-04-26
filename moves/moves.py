class Move:
    def __init__(self, name, damage, max_pp):
        self.name = name
        self.damage = damage
        self.max_pp = max_pp
        self.pp = max_pp

    def use_move(self):
        if self.pp > 0:
            self.pp -= 1
            return self.damage
        else:
            return 0  # Move can't be used if PP is 0

# Example moves
moves = {
    'Thunderbolt': Move('Thunderbolt', damage=40, max_pp=10),
    'Quick Attack': Move('Quick Attack', damage=20, max_pp=5),
    'Flamethrower': Move('Flamethrower', damage=45, max_pp=10),
    'Scratch': Move('Scratch', damage=15, max_pp=5)
}
