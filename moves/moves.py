<<<<<<< HEAD
=======

#Earlier when i wasnt using pokeapi. These are useless now. Delete if you want to.

>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
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
<<<<<<< HEAD
            return 0  # Move can't be used if PP is 0

# Example moves
=======
            return 0

>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
moves = {
    'Thunderbolt': Move('Thunderbolt', damage=40, max_pp=10),
    'Quick Attack': Move('Quick Attack', damage=20, max_pp=5),
    'Flamethrower': Move('Flamethrower', damage=45, max_pp=10),
    'Scratch': Move('Scratch', damage=15, max_pp=5)
}
