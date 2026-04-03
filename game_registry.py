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
        game_id="mortal_kombat",
        name="Mortal Kombat",
        mechanism_index=1,
        scorer_id="mortal_kombat",
        adapter_type="builtin",
        adapter_ref="sim.mortal_kombat",
        latency_budget_ms=150,
        description="1v1 fighter. Miner controls p2 vs reference opponent p1.",
        state_schema={
            "p1_health": "int",
            "p2_health": "int",
            "p1_pos": "float (0-1)",
            "p2_pos": "float (0-1)",
            "p1_state": "string",
            "p2_state": "string",
            "frame": "int",
            "move_history_p1": "[str]",
            "move_history_p2": "[str]",
        },
    ),
    GameConfig(
        game_id="halo",
        name="Halo Arena",
        mechanism_index=1,  # shares mechanism 1 with MK until cap is raised above 2
        scorer_id="halo",
        adapter_type="builtin",
        adapter_ref="sim.halo",
        latency_budget_ms=200,
        description="Simplified arena combat. Miner controls the agent.",
        state_schema={
            "agent_pos": "[x,y,z]",
            "agent_health": "int",
            "agent_shield": "int",
            "enemies": "[{id, pos, health, weapon}]",
            "pickups": "[{type, pos}]",
            "map_id": "string",
            "ammo": "{weapon: count}",
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
