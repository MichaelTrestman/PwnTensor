"""
PwnTensor game registry — manages the set of active games (mechanisms) on the subnet.

Each game registers with:
  - A game adapter (Docker image or API endpoint validators call to run episodes)
  - A scoring function ID (maps to a scorer in reward.py)
  - A context schema (what state fields exist in this game)
  - A mechanism index (which Bittensor incentive mechanism it maps to)

For the demo, the registry is hardcoded with three games. In production,
this would read from on-chain storage or a config fetched from the subnet.
"""

from dataclasses import dataclass, field


@dataclass
class GameConfig:
    """Configuration for a single game on the subnet."""
    game_id: str
    name: str
    mechanism_index: int          # which Bittensor incentive mechanism this maps to
    scorer_id: str                # key into reward.GAME_SCORERS
    adapter_type: str             # "builtin" | "docker" | "api"
    adapter_ref: str              # Docker image or API endpoint
    latency_budget_ms: int = 150
    state_schema: dict = field(default_factory=dict)
    description: str = ""


# Demo game registry — three games, three mechanisms
DEMO_GAMES: list[GameConfig] = [
    GameConfig(
        game_id="pactensor",
        name="PacTensor",
        mechanism_index=0,
        scorer_id="pactensor",
        adapter_type="builtin",
        adapter_ref="sim.pactensor",
        latency_budget_ms=150,
        description="Pac-Man variant with AI-controlled ghosts. Miner = ghost AI.",
        state_schema={
            "pacman_pos": "[x, y]",
            "ghost_positions": "[[x,y], ...]",
            "ghost_modes": "[chase|scatter|frightened|eaten]",
            "ghost_boost_multiplier": "float",
            "pellets_remaining": "int",
            "power_pellet_active": "bool",
            "maze_layout": "run-length encoded grid",
            "tick": "int",
        },
    ),
    GameConfig(
        game_id="meleelight",
        name="Melee Light",
        mechanism_index=1,
        scorer_id="meleelight",
        adapter_type="builtin",
        adapter_ref="sim.meleelight",
        latency_budget_ms=150,
        description=(
            "Smash Bros-style platform fighter (MIT, github.com/schmooblidon/meleelight). "
            "Miner controls one fighter vs a reference opponent. "
            "Game loop separated from rendering, runs headless in Node.js."
        ),
        state_schema={
            "p1_pos": "{x, y} float position",
            "p2_pos": "{x, y} float position",
            "p1_percent": "int (damage accumulated, 0+)",
            "p2_percent": "int (damage accumulated, 0+)",
            "p1_stocks": "int (lives remaining)",
            "p2_stocks": "int (lives remaining)",
            "p1_action_state": "string (current animation/action state)",
            "p2_action_state": "string",
            "p1_facing": "int (-1 or 1)",
            "p2_facing": "int (-1 or 1)",
            "stage_id": "string",
            "frame": "int",
        },
    ),
    GameConfig(
        game_id="kaz",
        name="Knights Archers Zombies",
        mechanism_index=2,
        scorer_id="kaz",
        adapter_type="builtin",
        adapter_ref="sim.kaz",
        latency_budget_ms=150,
        description=(
            "Co-op survival game (MIT, Farama PettingZoo butterfly/knights_archers_zombies). "
            "2 knights + 2 archers vs zombie waves. Miner controls one or more agents. "
            "Headless native, structured observations, 6 discrete actions."
        ),
        state_schema={
            "agent_id": "string (knight_0, knight_1, archer_0, archer_1)",
            "agent_pos": "{x, y} float position",
            "agent_health": "int",
            "agent_type": "string (knight|archer)",
            "nearby_zombies": "[{pos, health, distance}]",
            "nearby_allies": "[{id, pos, health, type}]",
            "arrows_in_flight": "[{pos, velocity}] (archers only)",
            "wave": "int",
            "zombies_remaining": "int",
            "tick": "int",
        },
    ),
]


def get_game_registry() -> list[GameConfig]:
    """
    Return the active game registry.

    TODO: In production, read from on-chain storage or subnet config.
    For now, returns the hardcoded demo games.
    """
    return DEMO_GAMES


def get_game_by_id(game_id: str) -> GameConfig | None:
    """Look up a game config by its game_id."""
    for game in DEMO_GAMES:
        if game.game_id == game_id:
            return game
    return None


def get_games_by_mechanism(mechanism_index: int) -> list[GameConfig]:
    """Get all games assigned to a specific mechanism index."""
    return [g for g in DEMO_GAMES if g.mechanism_index == mechanism_index]
