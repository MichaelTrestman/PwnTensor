"""
PwnTensor scoring — the incentive mechanism's scoring model.

Scores ghost AI on the "fun" dimension: ghosts should be challenging but not
unfair. The target fun-score band is 50-75/100. Miners whose ghost AI produces
fun scores in this band get the highest weights.
"""

import math


def score_episode(episode_log: dict) -> float:
    """
    Score a single episode of PacTensor.

    Components:
    - danger: close calls per second (ghost kept pressure on player)
    - efficiency: pellets eaten per second (game pace was good)
    - survival: player didn't die too much (ghost wasn't unfairly hard)

    Returns a normalized score in [0, 1].
    """
    elapsed = max(episode_log.get("elapsed_seconds", 1), 1)
    close_call_ticks = episode_log.get("close_call_ticks", 0)
    pellets_eaten = episode_log.get("pellets_eaten", 0)
    deaths = episode_log.get("deaths", 0)
    ghosts_caught = episode_log.get("ghosts_caught", 0)

    # Danger: close calls per second, capped at 40 points
    danger = min(close_call_ticks / elapsed * 10, 40)

    # Efficiency: pellets per second, capped at 30 points
    efficiency = min(pellets_eaten / elapsed * 5, 30)

    # Survival: penalize excessive deaths, capped at 30 points
    survival = max(0, 30 - deaths * 10)

    fun_score = danger + efficiency + survival  # 0-100 range

    # Latency penalty
    avg_latency = episode_log.get("avg_latency_ms", 0)
    latency_penalty = max(0, (avg_latency - 150) / 150) * 0.2

    # Normalize to [0, 1]
    raw = fun_score / 100.0
    return max(0.0, min(1.0, raw - latency_penalty))


def rank_normalize(scores: dict[int, float]) -> dict[int, float]:
    """
    Rank-based normalization across miners. Maps raw scores to [0, 1]
    based on rank ordering so one outlier can't tank the scale.
    """
    if not scores:
        return {}
    sorted_uids = sorted(scores.keys(), key=lambda uid: scores[uid])
    n = len(sorted_uids)
    if n == 1:
        return {sorted_uids[0]: 1.0}
    return {uid: rank / (n - 1) for rank, uid in enumerate(sorted_uids)}
