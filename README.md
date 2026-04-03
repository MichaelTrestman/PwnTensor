# PwnTensor: Game AI Marketplace on Bittensor

A subnet where game studios bring their games and miners compete to build the best AI agents. Each game maps to a Bittensor incentive mechanism with its own weight matrix, bond pool, and independent emissions.

## The Concept

- **Game studios** register games on the subnet (each game = one incentive mechanism)
- **Miners** receive game state, return actions. Any technique: FSM, RL, LLM, behavior trees. Only outputs are scored.
- **Validators** run headless game sims, fan out state to miner axons, score episodes, set weights per mechanism. Also serve playable frontends for all games.
- **Stakers** back validators; game studios stake TAO into their game's mechanism to attract miner attention (market-driven prioritization).

## Demo Games

| Mechanism | Game | Source | Miner Role | Scoring |
|-----------|------|--------|------------|---------|
| 0 | **PacTensor** | Custom | Ghost AI | Fun-score: challenging but fair (target 50-75/100) |
| 1 | **Melee Light** | [schmooblidon/meleelight](https://github.com/schmooblidon/meleelight) (MIT) | Platform fighter vs reference opponent | Stocks remaining + damage differential |
| 2 | **Knights Archers Zombies** | [Farama PettingZoo](https://github.com/Farama-Foundation/PettingZoo) (MIT) | Co-op agent vs zombie waves | Waves survived + kills + team survival |

All three games have browser-playable frontends served by validators.

## Structure

```
validator.py      -- main loop: per-mechanism episode running + weight setting
protocol.py       -- GameStateSynapse: universal across all games
reward.py         -- per-game scoring functions + rank normalization
game_registry.py  -- active games and their mechanism mappings
frontend/         -- browser-playable frontends for all games
  index.html      -- PacTensor
  meleelight/     -- Melee Light platform fighter
  kaz/            -- Knights Archers Zombies co-op
knowledge/        -- Chi-compatible knowledge files for vibe-coding agents
```

## Quick Start

```bash
cp env.example .env  # edit with your wallet/netuid
docker-compose up -d
```

## Built on Chi

Follows the [Chi template](https://github.com/unconst/Chi) pattern. Point Cursor at `@knowledge` and go.
