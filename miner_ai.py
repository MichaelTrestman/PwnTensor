"""
PwnTensor miner AI — baseline strategies for each game.

This is what miners replace to earn higher weights. The contract is simple:
  Input: game state dict + valid actions + tick + seed
  Output: (action_string, action_args_dict)

Miners can use any technique — scripted logic, RL policies, LLMs,
behavior trees. The subnet only scores outputs.
"""

import math
import random


def handle_game_state(
    game_id: str,
    state: dict,
    valid_actions: list[str],
    tick: int,
    episode_seed: int,
) -> tuple[str, dict]:
    """
    Route to the appropriate game handler and return (action, action_args).
    """
    handler = GAME_HANDLERS.get(game_id)
    if handler is None:
        # Unknown game — pick a random valid action
        action = random.choice(valid_actions) if valid_actions else "noop"
        return action, {}
    return handler(state, valid_actions, tick, episode_seed)


# ---------------------------------------------------------------------------
# PacTensor — Ghost AI
# Miner controls 4 ghosts chasing the player.
# Baseline: BFS chase + scatter archetypes (same as the frontend baseline).
# ---------------------------------------------------------------------------

def handle_pactensor(state: dict, valid_actions: list[str], tick: int, seed: int) -> tuple[str, dict]:
    """
    PacTensor ghost AI. Returns direction vectors for each ghost.
    """
    pacman_pos = state.get("pacman_pos", [0, 0])
    ghost_positions = state.get("ghost_positions", [])
    ghost_modes = state.get("ghost_modes", [])

    ghost_actions = []
    for i, (gpos, mode) in enumerate(zip(ghost_positions, ghost_modes)):
        if mode == "frightened":
            # Run away from player
            dx = gpos[0] - pacman_pos[0]
            dy = gpos[1] - pacman_pos[1]
        elif mode == "scatter":
            # Head to assigned corner
            corners = [[1, 1], [1, 20], [22, 1], [22, 20]]
            corner = corners[i % 4]
            dx = corner[0] - gpos[0]
            dy = corner[1] - gpos[1]
        else:
            # Chase: move toward player
            dx = pacman_pos[0] - gpos[0]
            dy = pacman_pos[1] - gpos[1]

        # Normalize to a direction
        if abs(dx) >= abs(dy):
            dr, dc = 0, (1 if dx > 0 else -1)
        else:
            dr, dc = (1 if dy > 0 else -1), 0

        ghost_actions.append({"dr": dr, "dc": dc})

    return "ghost_move", {"ghost_actions": ghost_actions}


# ---------------------------------------------------------------------------
# Melee Light — Platform Fighter
# Miner controls one fighter vs a reference opponent.
# Baseline: approach + attack when close, recover when off stage.
# ---------------------------------------------------------------------------

def handle_meleelight(state: dict, valid_actions: list[str], tick: int, seed: int) -> tuple[str, dict]:
    """
    Melee Light fighter AI. Returns controller inputs.
    """
    p1 = state.get("p1_pos", {"x": 300, "y": 200})
    p2 = state.get("p2_pos", {"x": 300, "y": 200})
    my_percent = state.get("p2_percent", 0)
    stage_left = state.get("stage_left", 80)
    stage_right = state.get("stage_right", 520)

    dx = p1["x"] - p2["x"]
    dy = p1["y"] - p2["y"]
    dist = math.sqrt(dx * dx + dy * dy) if (dx or dy) else 1

    inputs = {
        "stick_x": 0.0,
        "stick_y": 0.0,
        "a": False,
        "b": False,
    }

    # Recovery: if below stage, jump
    if p2["y"] > 350:
        inputs["stick_y"] = -1.0  # jump
        inputs["b"] = True  # special (up-B recovery)
        return "controller", inputs

    # Approach
    if dist > 50:
        inputs["stick_x"] = 1.0 if dx > 0 else -1.0
    else:
        # In range — attack
        inputs["a"] = True
        inputs["stick_x"] = 1.0 if dx > 0 else -1.0

    # Occasionally jump to mix up
    if tick % 60 < 5:
        inputs["stick_y"] = -1.0

    return "controller", inputs


# ---------------------------------------------------------------------------
# Knights Archers Zombies — Co-op Survival
# Miner controls one or more agents (knights/archers) vs zombie waves.
# Baseline: move toward nearest zombie, attack when close.
# ---------------------------------------------------------------------------

def handle_kaz(state: dict, valid_actions: list[str], tick: int, seed: int) -> tuple[str, dict]:
    """
    KAZ co-op AI. Returns an action int per agent the miner controls.
    Action space: 0=noop, 1=rotate_cw, 2=rotate_ccw, 3=forward, 4=backward, 5=attack
    """
    agent_pos = state.get("agent_pos", {"x": 300, "y": 400})
    agent_type = state.get("agent_type", "knight")
    nearby_zombies = state.get("nearby_zombies", [])

    if not nearby_zombies:
        # No zombies visible — hold position
        return "action", {"action_id": 0}

    # Find nearest zombie
    nearest = min(nearby_zombies, key=lambda z: z.get("distance", 999))
    zdist = nearest.get("distance", 999)

    # Calculate angle to zombie
    zpos = nearest.get("pos", {"x": 300, "y": 0})
    dx = zpos["x"] - agent_pos["x"]
    dy = zpos["y"] - agent_pos["y"]
    target_angle = math.atan2(dy, dx)

    # Simple behavior:
    if agent_type == "knight":
        if zdist > 30:
            return "action", {"action_id": 3}  # move forward
        else:
            return "action", {"action_id": 5}  # attack (sword)
    else:
        # Archer: shoot if zombie exists, back up if too close
        if zdist < 60:
            return "action", {"action_id": 4}  # backward
        else:
            return "action", {"action_id": 5}  # attack (shoot arrow)


# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------

GAME_HANDLERS = {
    "pactensor": handle_pactensor,
    "meleelight": handle_meleelight,
    "kaz": handle_kaz,
}
