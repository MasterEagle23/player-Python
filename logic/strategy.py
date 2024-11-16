from typing import List
from models.game_state import GameState
from models.game_state import BoardAction
from models.player_action import PlayerAction
from models.base import Base
from models.game_config import GameConfig
from models.position import Position
from math import sqrt


UPGRADE_GOAL = 14
ATTACK_THRESHOLD = 5
PLAYMODE = 0



def decide(gameState: GameState) -> List[PlayerAction]:

    config: GameConfig = gameState.config

    mybases, otherbases = get_base_lists(gameState)
    # board_action = get_board_action(gameState)
    actions: List[PlayerAction] = []

    if PLAYMODE == 0:
        # aggressive mode
        upgradebases: List[Base] = []

        for base in mybases:
            attack = validate_attack(config, base, closest_hostile_base(base, otherbases))
            if attack is not None:
                actions.append(attack)
            else:
                upgradebases.append(base)
        actions += get_upgrades(config, upgradebases)

        return actions
    
    else:
        # normal mode
        if len(mybases) == 1:
            return [do_spam_attack(gameState, mybases[0], otherbases)]

        actions += get_upgrades(config, mybases)

        if actions == []:
            # do some attack
            target = closest_hostile_base(mybases[0], otherbases)
            source = closest_ally_base(target, mybases)
            actions.append(PlayerAction(source.uid, target.uid, source.population-1))
            for base in mybases:
                if base != source:
                    actions.append(PlayerAction(base.uid, source.uid, base.population - 1))

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
    urwald-player-5ff88f9b4b-zzmrj
    if len(mybases) > 0:
        upgradebase: Base = mybases[0]
        for base in mybases:
            if base.level < UPGRADE_GOAL:
                # pick base
                return base
        return None
    else:
        return None

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


''' pls fix this pile of shit
def get_board_action(gameState: GameState) -> tuple[List[BoardAction], List[BoardAction]]:
   
    # Zieht sich aus gamestate die BoardActions von uns und von allen anderen Spielern
   
    my_board_actions: List[BoardAction]
    other_board_actions= gameState.actions
    for board_actions in gameState.actions:
        counter=0
        if board_actions.player == gameState.actions(counter):
            my_board_actions.append(board_actions)
        else:
            other_board_actions.append(board_actions)
        counter+=1
        
    return my_board_actions, other_board_actions
'''

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
    if (base.player == 0):
        return 0
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

def closest_hostile_base (our_base: Base, other_bases: List[Base] ):
    distance: int = -1
    closest_hostile: Base
    for base in other_bases:
        dist_temp: int = distance_3d(our_base.position, base.position)
        if ((-1 == distance) or (dist_temp < distance)):
            distance = dist_temp
            closest_hostile = base
    return closest_hostile

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

def find_enemies (gameState: GameState ,other_bases: List[Base]):
    enemies: List[Base] = []
    for base in other_bases:
        if (0 != base.player) and (gameState.game.player != base.player):
            enemies.append(base)
    return enemies

def do_spam_attack(config: GameConfig, srcbase: Base, otherbases: List[Base]) -> PlayerAction:
    '''
    spams all units exept one to spam the nearest base
    '''
    target: Base = closest_hostile_base(srcbase, otherbases)

    attack_amount = srcbase.population - 1

    return PlayerAction(srcbase.uid, target.uid, attack_amount)

def validate_attack(config: GameConfig, source: Base, target: Base) -> PlayerAction:
    '''
    validate and create attacks
    '''
    loss = (distance_3d(source.position, target.position) - config.paths.grace_period) * config.paths.death_rate

    if loss <= 0:
        return PlayerAction(source.uid, target.uid, source.population - 1)
    if loss <= (source.population - 1) * ATTACK_THRESHOLD:
        return PlayerAction(source.uid, target.uid, source.population - 1)
    
    return None
