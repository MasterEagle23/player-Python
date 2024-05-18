from models.game_state import GameState

gamestate: GameState


def setgamestate(game_state: GameState):
    global gamestate
    gamestate = game_state
