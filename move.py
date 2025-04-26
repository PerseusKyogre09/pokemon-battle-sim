class Move:
    def __init__(self, name, power, pp):
        self.name = name
        self.power = power
        self.pp = pp

<<<<<<< HEAD
=======
    #pp check
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
    def use_move(self):
        if self.pp > 0:
            self.pp -= 1
            return self.power
        else:
<<<<<<< HEAD
            return 0  # No PP left, so the move fails
=======
            return 0
>>>>>>> 24696daa70a40374ab8723bf813fdcce65ebd396
