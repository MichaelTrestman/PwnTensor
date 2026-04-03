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


def score_meleelight(episode_log: dict) -> float:
    """
    Platform fighter scoring (Melee Light). Miner controls one fighter
    vs a reference opponent.
    Score = stocks remaining + damage dealt - damage taken, normalized.
    """
    max_stocks = episode_log.get("max_stocks", 3)
    stocks_remaining = episode_log.get("stocks_remaining", 0)
    damage_dealt = episode_log.get("damage_dealt", 0)
    damage_taken = episode_log.get("damage_taken", 0)
    opponent_stocks = episode_log.get("opponent_stocks_remaining", 0)

    # Stock differential is the primary signal
    stock_score = (stocks_remaining - opponent_stocks + max_stocks) / (2 * max_stocks)
    # Damage differential as secondary signal, normalized by reasonable range
    damage_score = min(1.0, max(0.0, (damage_dealt - damage_taken + 300) / 600))

    # Weight: 70% stock outcome, 30% damage efficiency
    return stock_score * 0.7 + damage_score * 0.3


def score_kaz(episode_log: dict) -> float:
    """
    Co-op survival scoring (Knights Archers Zombies). Miner controls
    one or more agents cooperating against zombie waves.
    Score = waves survived + enemies killed + team survival time.
    """
    waves_survived = episode_log.get("waves_survived", 0)
    max_waves = episode_log.get("max_waves", 10)
    enemies_killed = episode_log.get("enemies_killed", 0)
    max_enemies = episode_log.get("max_enemies", 50)
    team_survival_ticks = episode_log.get("team_survival_ticks", 0)
    max_ticks = episode_log.get("max_ticks", 3600)
    allies_alive = episode_log.get("allies_alive_at_end", 0)
    total_allies = episode_log.get("total_allies", 4)

    # Wave progress is the primary signal
    wave_score = waves_survived / max(max_waves, 1)
    # Kill efficiency
    kill_score = min(1.0, enemies_killed / max(max_enemies, 1))
    # Team survival (cooperative signal — keeping allies alive matters)
    survival_score = allies_alive / max(total_allies, 1)
    # Time alive as tiebreaker
    time_score = min(1.0, team_survival_ticks / max(max_ticks, 1))

    return wave_score * 0.4 + kill_score * 0.25 + survival_score * 0.25 + time_score * 0.1


# Game ID -> scoring function registry
GAME_SCORERS = {
    "pactensor": score_pactensor,
    "meleelight": score_meleelight,
    "kaz": score_kaz,
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


