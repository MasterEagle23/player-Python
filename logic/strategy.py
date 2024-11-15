from typing import List
from models.game_state import GameState
from models.player_action import PlayerAction
from models.base import Base
from models.game_config import GameConfig
from models.position import Position
from math import sqrt

def decide(gameState: GameState) -> List[PlayerAction]:
    # TODO: place your logic here
    return [PlayerAction(0, 0, 0)]


def get_base_lists(gamestate) -> tuple[List[Base], List[Base]]:
    mybases: List[Base] = []
    otherbases: List[Base] = []
    for base in gamestate.bases:
        if base.player:
            mybases.append(base)
        else:
            otherbases.append(base)

    return mybases, otherbases

def get_death_rate(config: GameConfig) -> int:
    return config.paths.death_rate

def get_grace_period(config: GameConfig) -> int:
    return config.paths.grace_period

def get_spawn_rate(config: GameConfig, base: Base) -> int:
    return config.base_levels[base.level].spawn_rate

def get_max_population(config: GameConfig, base: Base) -> int:
    return config.base_levels[base.level].max_population

def get_upgrade_cost(config: GameConfig, base: Base) -> int:
    return config.base_levels[base.level + 1].upgrade_cost

def unit_amount_after_travel(config: GameConfig, units_sent: int, distance: int) -> int:
    out = units_sent - get_death_rate(config) * max(distance - get_grace_period(config), 0)
    print(f"\treturn: {out}\n")
    return out

def distance_3d(pos1: Position, pos2: Position):
    return sqrt((pos1.x-pos2.x)**2+(pos1.y-pos2.y)**2+(pos1.y-pos2.y)**2)