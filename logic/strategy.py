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

    actions.append(get_upgrades(gameState.config, mybases))

    # TODO: place your logic here
    return actions

def project_base_pop(config: GameConfig, base: Base, ticks: int) -> int:
    '''
    
    '''
    pop_in_x_ticks: int = base.population + get_spawn_rate(config, base) * ticks
    pop_in_x_ticks = min(pop_in_x_ticks, get_max_population(config, base) + get_spawn_rate(config, base))
    return pop_in_x_ticks

def units_needed_to_defeat_base_from_base(config: GameConfig, hostileBase: Base, myBase: Base) -> int: 
    '''
    Übergib gegnerbasis und eigene basis. Berechnet, wie viele Units gebraucht werden um die Basis mit +1 Pop einzunehmen.
    '''
    d = distance_3d(myBase.position, hostileBase.position)
    pop = project_base_pop(config, hostileBase, d)
    return units_to_send(config, d, pop + 1)

def units_to_send(config: GameConfig, distance: int, units_that_need_to_arrive: int) -> int:
    '''
    Nimmt einen int. Berechnet die Menge an Units, die gebraucht werden, dass die Meneg int an units ankommt
    '''
    return units_that_need_to_arrive + get_death_rate(config) * max(distance - get_grace_period(config), 0)

def get_upgrades(config: GameConfig, mybases: List[Base]) -> List[PlayerAction]:
    '''
    Picks all units and sends all overflowing units to that base.
    '''
    
    # pick base to upgrade
    upgradeBase: Base = pick_upgrade_base(config, mybases)

    # send units to base
    actions: List[PlayerAction] = []

    for base in mybases:
        actions.append(PlayerAction(base.uid, upgradeBase.uid, units_above_max(config, base)))

    return actions

def pick_upgrade_base(config: GameConfig, mybases: List[Base]) -> Base:
    '''
    Entscheidet welche Base gerade geupgraded werden soll
    '''
    upgradebase: Base = mybases[0]
    for base in mybases:
        if base.level < 5:
            # pick base
            return base
        elif base.level < upgradebase.level:
            # pick lowest base
            upgradebase = base

    return upgradebase

def upgrade_with_overhead(config: GameConfig, mybases: List[Base]) -> List[PlayerAction]:
    '''
    Alle pops über max werden in die eigene Base gesteckt
    '''
    actions: List[PlayerAction] = []
    for base in mybases:
        if base.level < len(config.base_levels):
            actions.append(PlayerAction(base.uid, base.uid, units_above_max(config, base)))
    return actions


def get_base_lists(gameState: GameState) -> tuple[List[Base], List[Base]]:
    '''
    Zieht sich aus gamestate die Informationen der bases und speichert Basisinfos in die Listen mybases udn otherbases
    '''
    mybases: List[Base] = []
    otherbases: List[Base] = []
    for base in gameState.bases:
        if base.player == gameState.game.player:
            mybases.append(base)
        else:
            otherbases.append(base)

    return mybases, otherbases

def get_death_rate(config: GameConfig) -> int:
    '''
    Holt sich death_rate(Variable, wie weit bits reisen, bis sie sterben)
    '''
    return config.paths.death_rate

def get_grace_period(config: GameConfig) -> int:
    
    return config.paths.grace_period

def get_spawn_rate(config: GameConfig, base: Base) -> int:
    '''
    Übergib den Namen einer Basis, returnt spawnrate der Basis
    '''
    return config.base_levels[base.level].spawn_rate

def get_max_population(config: GameConfig, base: Base) -> int:
    '''
    Übergib den Namen einer Basis, returnt maxPop der Basis
    '''   
    return config.base_levels[base.level].max_population

def get_upgrade_cost(config: GameConfig, base: Base) -> int:
    '''
    Übergib den Namen einer Basis, returnt Upgradekosten der Basis
    '''
    return config.base_levels[base.level + 1].upgrade_cost

def unit_amount_after_travel(config: GameConfig, units_sent: int, distance: int) -> int:
    '''
    Übergib die Menge an Units und die Distanz zm ziel. Berechnet dir die übigen Units, beim eintreffen
    '''
    out = units_sent - get_death_rate(config) * max(distance - get_grace_period(config), 0)
    print(f"\treturn: {out}\n")
    return out

def units_above_max(config: GameConfig, base:Base) -> int:
    '''
    Wie viele Units sterben im nächsten tick
    '''
    if base.population > config.base_levels[base.level].max_population:
        return base.population - config.base_levels[base.level].max_population
    return 0

def distance_3d(pos1: Position, pos2: Position):
    '''
    Berechnet die Distanz zwischen den übergebenen Punkten, Punkt 1 und Punkt 2
    '''
    return int(sqrt((pos1.x-pos2.x)**2+(pos1.y-pos2.y)**2+(pos1.y-pos2.y)**2))
