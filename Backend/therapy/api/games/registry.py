from __future__ import annotations

from typing import Dict, Optional, Protocol, Type, Union, Any


class GamePlugin(Protocol):
    """
    Contract every game plugin must satisfy.

    IMPORTANT:
    - engine passes session_id to build_trial/evaluate for adaptive logic.
    - keep session_id optional so simpler games still work.
    """
    code: str
    trial_type: str
    game_name: str  # optional but recommended

    def compute_level(self, session_id: int) -> int: ...
    def build_trial(self, level: int, *, session_id: Optional[int] = None) -> Dict[str, Any]: ...
    def evaluate(
        self,
        *,
        target: str,
        submit: Dict[str, Any],
        level: int,
        session_id: Optional[int] = None,
    ) -> Dict[str, Any]: ...


GAMES: Dict[str, GamePlugin] = {}


def register(game: Union[GamePlugin, Type[GamePlugin]]):
    """
    Allows:
      @register
      class MyGame: ...

    OR:
      register(MyGame())
    """
    if isinstance(game, type):
        game = game()  # type: ignore[call-arg]
    if not getattr(game, "code", None):
        raise ValueError("Game plugin must define a non-empty `code`")
    GAMES[game.code] = game
    return game


def get_game(code: str) -> GamePlugin:
    game = GAMES.get(code)
    if not game:
        raise KeyError(f"Unknown game code: {code}. Registered: {sorted(GAMES.keys())}")
    return game
