class Move:
    def __init__(self, name, power, pp):
        self.name = name
        self.power = power
        self.pp = pp

    def use_move(self):
        if self.pp > 0:
            self.pp -= 1
            return self.power
        else:
            return 0  # No PP left, so the move fails
