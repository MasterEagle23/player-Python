from typing import List
from models.game_state import GameState
from models.player_action import PlayerAction
from models.base import Base
from logic.incoming_units import IncomingUnits
from models.position import Position

gamestate: GameState


def decide(game_state: GameState) -> List[PlayerAction]:
    global gamestate
    gamestate = game_state

    actions: List[PlayerAction] = []

    mybases, otherbases = get_base_list()

    otherbases = sort_bases_by_pop(otherbases)

    my_inactive_bases = mybases

    for base in my_inactive_bases:
        if base.population > gamestate.config.base_levels[base.level].upgrade_cost:
            actions.append(upgrade(base))
            my_inactive_bases.pop(my_inactive_bases.index(base))

    for base in my_inactive_bases:
        if base.population > get_max_population(base) / 2:
            for hostilebase in otherbases:
                tmp_action: PlayerAction = attack(base, hostilebase,
                                                  units_needed_to_defeat_base(base.uid, hostilebase.uid))
                if tmp_action.src >= 0 and tmp_action.dest >= 0 and tmp_action.amount > 0:
                    actions.append(tmp_action)
                    my_inactive_bases.pop(my_inactive_bases.index(base))
                    break

    for base in my_inactive_bases:
        pass

    return actions


def get_base_list() -> tuple[List[Base], List[Base]]:
    mybases: List[Base] = []
    otherbases: List[Base] = []
    for base in gamestate.bases:
        if base.player:
            mybases.append(base)
        else:
            otherbases.append(base)

    return mybases, otherbases


# me_functions

def units_needed_to_defeat_base(srcid: int, destid: int) -> int:
    destbase = get_base_from_uid(destid)
    srcbase = get_base_from_uid(srcid)
    if destbase.uid < 0 or srcbase.uid < 0:
        return -1
    dist = getdistance(srcbase.position, destbase.position)
    if dist < 0:
        return -1
    units_at_dest_after_travel = destbase.population + gamestate.config.base_levels[destbase.level].spawn_rate * dist
    return adjust_for_death_rate(units_at_dest_after_travel, dist)


def adjust_for_death_rate(units_that_arrive: int, distance: int) -> int:
    return units_that_arrive + get_death_rate() * max(distance - get_grace_period(), 0)


def unit_amount_after_travel(units_sent: int, distance: int) -> int:
    out = units_sent - get_death_rate() * max(distance - get_grace_period(), 0)
    print(f"\treturn: {out}\n")
    return out


def get_base_from_uid(uid: int) -> Base:
    for base in gamestate.bases:
        if base.uid == uid:
            return base
    return Base.fromAttributes(Position.fromAttributes(0, 0, 0), -1, 0, 0, 0, 0)


def get_upgrade_cost(base: Base) -> int:
    return gamestate.config.base_levels[base.level + 1].upgrade_cost


def get_max_population(base: Base) -> int:
    return gamestate.config.base_levels[base.level].max_population


def get_spawn_rate(base: Base) -> int:
    return gamestate.config.base_levels[base.level].spawn_rate


def get_grace_period() -> int:
    return gamestate.config.paths.grace_period


def get_death_rate() -> int:
    return gamestate.config.paths.death_rate


# one_functions

def getdistance(pos1, pos2) -> int:
    if type(pos1) == type(pos2) == type(Position) and type(pos1) == type(Position):
        return int(((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2 + (pos1.z - pos2.z) ** 2) ** 0.5)
    elif type(pos1) == type(pos2) == type(tuple[int, int, int]):
        return int(((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2 + (pos1[2] - pos2[2]) ** 2) ** 0.5)
    else:
        return -1  # TypeError


def incoming_units(base: Base) -> IncomingUnits:
    """
    returns a dictionary like object containing the amount of change in unites at a given amount of ticks into the future

    :param base:
        base the units are incoming to
    :return:
        dict{int: int} like
        incoming_units(base)[ticks_into_future] -> the sum of units incoming during the Round with friendly units being
        counted positive and enemy units
    """
    incoming: IncomingUnits = IncomingUnits()
    for act in gamestate.actions:
        if act.dest == base.uid:
            timeremaining = act.progress.distance - act.progress.traveled
            if act.player == gamestate.game.player:
                incoming[timeremaining] += act.amount
            else:
                incoming[timeremaining] -= act.amount
    return incoming


def get_overflowing_bases():
    pass


def units_until_upgrade(base: Base) -> int:
    return gamestate.config.base_levels[base.level].upgrade_cost - base.units_until_upgrade


def upgrade(base: Base, amount: int = None) -> PlayerAction:
    if amount is None:
        amount = base.population / 2
    amount = min(amount, units_until_upgrade(base))
    return PlayerAction(base.uid, base.uid, amount)


# x_functions

def base_overflow(base: Base):
    return base.population - gamestate.config.base_levels[base.level].max_population


# returns difference in base population and max population
# +val: base overflow, -val: base underflow

def attack(attacker: Base, target: Base, amount: int) -> PlayerAction:
    arriving_units = units_needed_to_defeat_base(attacker.uid, target.uid)
    if arriving_units < 0:
        return PlayerAction(-1, -1, -1)
    if units_needed_to_defeat_base(attacker.uid, target.uid) < amount:
        return PlayerAction(-1, -1, -1)
    return PlayerAction(attacker.uid, target.uid, amount)


def sort_bases_by_pop(bases: list[Base]):
    for i in range(len(bases)):
        min_idx = i
        for j in range(i + 1, len(bases)):
            if bases[min_idx].population > bases[j].population:
                min_idx = j
        bases[i].population, bases[min_idx].population = bases[min_idx].population, bases[i].population
    return bases


# attack_alert

def attack_checker(base: Base):
    bases = get_base_list()
    attacked_at = []
    for i in range(len(gamestate.actions)):
        for j in range(len(bases[0])):
            if gamestate.actions[i].dest == bases[0][j]:
                attacked_at.append(j)
    return attacked_at
