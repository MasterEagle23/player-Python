from typing import List
from models.game_state import GameState
from models.game_state import BoardAction
from models.player_action import PlayerAction
from models.base import Base
from models.game_config import GameConfig
from models.position import Position
from math import sqrt



PLAYMODE = 1

# aggressive + normal mode
UPGRADE_GOAL = 14

# oneshot mode
ATTACK_FACTOR = 1.1
SUPPORT_THRESHOLD = 0.3
LOOK_AHEAD = 10

# aggressive + oneshot mode
SEND_THRESHOLD = 5



def decide(gameState: GameState) -> List[PlayerAction]:

    print(f'gameid: {gameState.game.uid}')

    config: GameConfig = gameState.config

    mybases, otherbases = get_base_lists(gameState)
    # board_action = get_board_action(gameState)
    boardactions: dict[str: List[BoardAction]] = get_actions_by_target_base(gameState)
    actions: List[PlayerAction] = []

    playmode = 1
    if gameState.game.tick > len(gameState.bases):
        playmode = 1

    if playmode == 0:
        # aggressive mode
        upgradebases: List[Base] = []

        for base in mybases:
            attack = validate_send(config, base, closest_hostile_base(base, otherbases))
            if attack is not None:
                actions.append(attack)
            else:
                upgradebases.append(base)
        temp = get_group_upgrades(config, upgradebases)
        if temp is not None:
            actions += temp

        return actions
    
    elif playmode == 1:
        # oneshot mode
        if len(mybases) == 1:
            source = mybases[0]
            for target in otherbases:
                # try to oneshot base
                b_acts = boardactions.get(str(target.uid))
                if b_acts is None:
                    b_acts = []
                attack = oneshot(config, source, target, b_acts)
                if attack is not None:
                    return [attack]
                temp = valid_upgrade(config, source)
                if temp is not None:
                    return [temp]
            return []
        
        # more than one base
        left_bases = mybases
        for base in left_bases:
            upgrade = valid_upgrade(config, base)
            if upgrade is not None:
                actions.append(upgrade)
                left_bases.pop(left_bases.index(base))
        
        if len(left_bases) == 0:
            # nothing left to do
            return actions
        
        target = closest_hostile_base(left_bases[0], otherbases)
        source = closest_ally_base(target, left_bases)

        b_acts = boardactions.get(str(target.uid))
        if b_acts is None:
            b_acts = []
        attack = oneshot(config, source, target, b_acts)

        if attack is not None:
            actions.append(attack)
            return actions
        
        left_bases.pop(left_bases.index(source))
        
        for base in left_bases:
            b_acts = boardactions.get(str(target.uid))
            if b_acts is None:
                b_acts = []
            if project_base_pop(config, base, LOOK_AHEAD, b_acts) > base.population - int(config.base_levels[base.level].max_population * SUPPORT_THRESHOLD):
                # projected pop > support threshold
                support = send_support(config, base, source)
                if support is not None:
                    actions.append(support)
        
        return actions

    else:
        # normal mode
        if len(mybases) == 1:
            return [do_spam_attack(gameState, mybases[0], otherbases)]

        actions += get_group_upgrades(config, mybases)

        if actions == []:
            # do some attack
            target = closest_hostile_base(mybases[0], otherbases)
            source = closest_ally_base(target, mybases)
            actions.append(PlayerAction(source.uid, target.uid, source.population-1))
            for base in mybases:
                if base != source:
                    actions.append(PlayerAction(base.uid, source.uid, base.population - 1))

        return actions
    
def oneshot(config: GameConfig, source: Base, target: Base, inbound_actions: List[BoardAction]) -> PlayerAction:
    units_needed = int(units_needed_to_defeat_base_from_base(config, target, source, inbound_actions)) * ATTACK_FACTOR
    if source.population > units_needed:
        return PlayerAction(source.uid, target.uid, units_needed)
    return None
    
def valid_upgrade(config: GameConfig, base: Base) -> PlayerAction:
    if base.population >= upgrade_cost(config, base) and base.level < len(config.base_levels) - 1:
        return PlayerAction(base.uid, base.uid, config.base_levels[base.level].upgrade_cost)
    return None

def send_support(config: GameConfig, source: Base, target: Base) -> PlayerAction:
    leftover = source.population - int(config.base_levels[source.level].max_population * SUPPORT_THRESHOLD)
    if leftover > 0:
        return validate_send(config, source, target, leftover)
    else:
        return None

def upgrade_cost(config: GameConfig, base: Base) -> int:
    return config.base_levels[base.level].upgrade_cost - base.units_until_upgrade

def project_base_pop(config: GameConfig, base: Base, ticks: int, inbound_actions: List[BoardAction]) -> int:
    '''
    
    '''
    pop_in_x_ticks: int = base.population + get_spawn_rate(config, base) * ticks
    pop_in_x_ticks = min(pop_in_x_ticks, get_max_population(config, base) + get_spawn_rate(config, base))

    for action in inbound_actions:
        if (action.progress.distance - action.progress.traveled) <= ticks:
            if action.player == base.player:
                pop_in_x_ticks += action.amount
            else:
                pop_in_x_ticks -= action.amount

    return abs(pop_in_x_ticks)

def units_needed_to_defeat_base_from_base(config: GameConfig, hostileBase: Base, myBase: Base, hostile_base_inbound_actions: List[BoardAction]) -> int: 
    '''
    Übergib gegnerbasis und eigene basis. Berechnet, wie viele Units gebraucht werden um die Basis mit +1 Pop einzunehmen.
    '''
    d = distance_3d(myBase.position, hostileBase.position)
    pop = project_base_pop(config, hostileBase, d, hostile_base_inbound_actions)
    return units_to_send(config, d, pop + 1)

def units_to_send(config: GameConfig, distance: int, units_that_need_to_arrive: int) -> int:
    '''
    Nimmt einen int. Berechnet die Menge an Units, die gebraucht werden, dass die Meneg int an units ankommt
    '''
    return units_that_need_to_arrive + get_death_rate(config) * max(distance - get_grace_period(config), 0)

def get_group_upgrades(config: GameConfig, mybases: List[Base]) -> List[PlayerAction]:
    '''
    Picks all units and sends all overflowing units to that base.
    '''
    if len(mybases) > 0:
        upgradebase: Base = mybases[0]
        actions: List[PlayerAction] = []
        for base in mybases:
            if base.level < UPGRADE_GOAL:
                overflow = base.population > config.base_levels[base.level].max_population
                if overflow > 0:
                    actions.append(PlayerAction(base.uid, upgradebase.uid, overflow))
        return actions
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

def get_actions_by_target_base(gamestate: GameState) -> dict:
    '''
    
    '''
    actions_by_target_base: dict = {}
    for action in gamestate.actions:
        if (actions_by_target_base.get(str(action.dest)) is None):
            actions_by_target_base[str(action.dest)] = []
        actions_by_target_base[str(action.dest)].append(action)
    return actions_by_target_base
        


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

def validate_send(config: GameConfig, source: Base, target: Base, amount=0) -> PlayerAction:
    '''
    validate and create attacks
    '''
    loss = (distance_3d(source.position, target.position) - config.paths.grace_period) * config.paths.death_rate
    if amount == 0:
        if loss <= 0:
            return PlayerAction(source.uid, target.uid, source.population - 1)
        if loss  * SEND_THRESHOLD <= (source.population - 1):
            return PlayerAction(source.uid, target.uid, source.population - 1)
    else:
        if loss <= 0:
            return PlayerAction(source.uid, target.uid, amount)
        if loss  * SEND_THRESHOLD <= amount:
            return PlayerAction(source.uid, target.uid, amount)
    
    return None
