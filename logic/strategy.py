from typing import List
from models.game_state import GameState
from models.player_action import PlayerAction
from models.base import Base
from models.game_config import GameConfig
from models.position import Position
from math import sqrt


def decide(gameState: GameState) -> List[PlayerAction]:

    mybases, otherbases = get_base_lists(gameState)

    actions: List[PlayerAction] = []

    actions += get_upgrades(gameState.config, mybases)

    # TODO: place your logic here
    return actions

def project_base_pop(config: GameConfig, base: Base, ticks: int) -> int:
    pop_in_x_ticks: int = base.population + get_spawn_rate(config, base) * ticks
    pop_in_x_ticks = min(pop_in_x_ticks, get_max_population(config, base) + get_spawn_rate(config, base))
    return pop_in_x_ticks

def units_needed_to_defeat_base_from_base(config: GameConfig, hostileBase: Base, myBase: Base):
    d = distance_3d(myBase.position, hostileBase.position)
    pop = project_base_pop(config, hostileBase, d)
    return units_to_send(config, d, pop + 1)

def units_to_send(config: GameConfig, distance: int, units_that_need_to_arrive: int):
    return units_that_need_to_arrive + get_death_rate(config) * max(distance - get_grace_period(config), 0)

def get_upgrades(config: GameConfig, mybases: List[Base]) -> List[PlayerAction]:
    # pick base to upgrade
    upgradeBase: Base = pick_upgrade_base(config, mybases)

    # send units to base
    actions: List[PlayerAction] = []

    for base in mybases:
        actions.append(PlayerAction(base.uid, upgradeBase.uid, units_above_max(config, base)))

    return actions

def pick_upgrade_base(config: GameConfig, mybases: List[Base]) -> Base:
    for base in mybases:
        if base.level < 5:
            return base
    return mybases[0]

def upgrade_with_overhead(config: GameConfig, mybases: List[Base]) -> List[PlayerAction]:
    actions: List[PlayerAction] = []
    for base in mybases:
        if base.level < len(config.base_levels):
            actions.append(PlayerAction(base.uid, base.uid, units_above_max(config, base)))
    return actions


def get_base_lists(gameState: GameState) -> tuple[List[Base], List[Base]]:
    mybases: List[Base] = []
    otherbases: List[Base] = []
    for base in gameState.bases:
        if base.player == gameState.game.player:
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

def units_above_max(config: GameConfig, base:Base) -> int:
    # does the bare minimum amount of units to send (into upgrades oder whatever)
    if base.population > config.base_levels[base.level].max_population:
        return base.population - config.base_levels[base.level].max_population
    return 0

def distance_3d(pos1: Position, pos2: Position):
    return int(sqrt((pos1.x-pos2.x)**2+(pos1.y-pos2.y)**2+(pos1.y-pos2.y)**2))

def closest_hostile_base (our_base: Base, other_bases: List[Base] ):
    distance: int = -1
    closest_ally: Base
    for base in other_bases:
        dist_temp: int = distance_3d(our_base.position, base.position)
        if (-1 == distance):
            distance = dist_temp
            closest_ally = base
        elif (dist_temp < distance):
            distance = dist_temp
            closest_ally = base
    return closest_ally

def closest_ally_base (current_base: Base, our_bases: List[Base]):
    distance: int = -1
    closest_ally: Base
    for base in our_bases:
        dist_temp: int = distance_3d(current_base.position, base.position)
        if (-1 == distance):
            distance = dist_temp
            closest_ally = base
        elif (dist_temp < distance):
            if (0 != dist_temp):
                closest_ally = base
                distance = dist_temp
    return closest_ally
