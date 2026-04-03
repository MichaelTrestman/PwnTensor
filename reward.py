"""
PwnTensor scoring — per-game scoring functions and cross-game aggregation.

Each game has its own scoring function. Validators score miners per-game,
rank-normalize within each game, then set weights per mechanism.

With Bittensor's multiple incentive mechanisms, each game maps to a separate
mechanism with its own weight matrix and bond pool.
"""

from statistics import mean


# ---------------------------------------------------------------------------
# Per-game scoring functions
# ---------------------------------------------------------------------------

def score_pactensor(episode_log: dict) -> float:
    """
    PacTensor ghost AI scoring — the "fun score" metric.
    Target band: 50-75/100. Penalizes boring AND unfair ghost AI.
    """
    elapsed = max(episode_log.get("elapsed_seconds", 1), 1)
    close_call_ticks = episode_log.get("close_call_ticks", 0)
    pellets_eaten = episode_log.get("pellets_eaten", 0)
    deaths = episode_log.get("deaths", 0)

    danger = min(close_call_ticks / elapsed * 10, 40)
    efficiency = min(pellets_eaten / elapsed * 5, 30)
    survival = max(0, 30 - deaths * 10)

    return (danger + efficiency + survival) / 100.0


def score_mortal_kombat(episode_log: dict) -> float:
    """
    Fighting game scoring. Miner controls p2 against a reference opponent (p1).
    Score = normalized damage dealt minus damage taken.
    """
    MAX_HEALTH = episode_log.get("max_health", 100)
    dmg_dealt = sum(episode_log.get("p2_damage_events", []))
    dmg_taken = sum(episode_log.get("p1_damage_events", []))
    raw = (dmg_dealt - dmg_taken) / MAX_HEALTH  # -1 to +1
    return max(0.0, (raw + 1.0) / 2.0)  # normalize to 0-1


def score_halo(episode_log: dict) -> float:
    """
    Arena combat scoring. Miner controls the agent.
    Score = kills - deaths + time-alive bonus.
    """
    kills = episode_log.get("kills", 0)
    deaths = episode_log.get("deaths", 0)
    survival_ticks = episode_log.get("ticks_alive", 0)
    raw = kills * 1.0 - deaths * 0.8 + survival_ticks * 0.002
    # Normalize: assume reasonable range of 0-10
    return max(0.0, min(1.0, raw / 10.0))


# Game ID -> scoring function registry
GAME_SCORERS = {
    "pactensor": score_pactensor,
    "mortal_kombat": score_mortal_kombat,
    "halo": score_halo,
}


# ---------------------------------------------------------------------------
# Cross-game scoring utilities
# ---------------------------------------------------------------------------

def score_episode(game_id: str, episode_log: dict) -> float:
    """
    Score a single episode for any registered game.
    Applies per-game scoring then a universal latency penalty.
    """
    scorer = GAME_SCORERS.get(game_id)
    if scorer is None:
        raise ValueError(f"Unknown game_id: {game_id}")

    raw = scorer(episode_log)

    # Universal latency penalty
    avg_latency = mean(episode_log.get("tick_latencies", [0]))
    latency_penalty = max(0, (avg_latency - 150) / 150) * 0.2

    return max(0.0, min(1.0, raw - latency_penalty))


def rank_normalize(scores: dict[int, float]) -> dict[int, float]:
    """
    Rank-based normalization across miners for a single game.
    Maps raw scores to [0, 1] based on rank ordering so one
    outlier can't tank the scale.
    """
    if not scores:
        return {}
    sorted_uids = sorted(scores.keys(), key=lambda uid: scores[uid])
    n = len(sorted_uids)
    if n == 1:
        return {sorted_uids[0]: 1.0}
    return {uid: rank / (n - 1) for rank, uid in enumerate(sorted_uids)}


