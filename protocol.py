"""
PwnTensor subnet protocol — Synapse definitions for game AI communication.

One synapse type for all games. game_id routes the miner's internal logic.
Miners that can handle multiple games get scoring opportunities across
multiple incentive mechanisms.
"""

import bittensor as bt
from typing import Optional


class GameStateSynapse(bt.Synapse):
    """
    Universal game AI synapse — works across all registered games.

    Validators set the immutable fields (game identity + state snapshot).
    Miners fill the mutable response fields (chosen action).

    The state dict is game-specific — each game defines its own schema
    (see knowledge/game_adapter.yaml for the adapter contract).
    """

    # ---- Set by validator (immutable) ----
    game_id: str                          # e.g. "pactensor", "meleelight", "kaz"
    episode_seed: int                     # deterministic RNG seed (block_hash + vali_hotkey + tick)
    tick: int                             # current sim step within the episode
    state: dict                           # full game state snapshot (game-specific schema)
    valid_actions: list[str]              # legal moves for this tick
    context_window: Optional[list[dict]] = None  # last N ticks for stateless miners

    # ---- Filled by miner (mutable) ----
    action: Optional[str] = None          # chosen action string
    action_args: Optional[dict] = None    # action parameters, e.g. {"target": [x,y], "move": "up"}
    latency_budget_ms: int = 150          # hard SLA per tick
