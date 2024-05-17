from models.base import Base
from models.base_level import BaseLevel
from models.game_state import GameState
from logic.globals_init import gamestate
from strategy import *


def attack_checker(base: Base):
    bases = get_base_list()
    attacked_at = []
    for i in range(len(gamestate.actions)):
        for j in range(len(bases[0])):
            if gamestate.actions[i].dest == bases[0][j]:
                attacked_at.append(j)
    return attacked_at
