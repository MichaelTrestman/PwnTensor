"""
PwnTensor subnet protocol — Synapse definitions for game AI communication.

Validators send GameStateSynapse with the current game state.
Miners return the ghost action decisions.
"""

import bittensor as bt
from typing import Optional


class GameStateSynapse(bt.Synapse):
    """
    Synapse for game AI communication between validators and miners.

    Validators set the immutable fields (game state).
    Miners fill the mutable response field (ghost actions).
    """

    # ---- Set by validator (immutable) ----
    game_id: str                          # "pactensor" (extensible to future games)
    episode_seed: int                     # deterministic RNG seed for the match
    tick: int                             # current sim step
    state: dict                           # full game state snapshot
    valid_actions: list[str]              # legal ghost moves for this tick
    ghost_count: int = 4                  # number of ghosts needing actions

    # ---- Filled by miner (mutable) ----
    ghost_actions: Optional[list[dict]] = None  # [{dir: {dr, dc}} per ghost]
    latency_budget_ms: int = 150                # hard SLA per tick
