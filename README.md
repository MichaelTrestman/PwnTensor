# PwnTensor: Game AI Marketplace on Bittensor

A Bittensor subnet designed to beat you at video games.

Game developers can bring their games to have miners compete to build the best AI agents to challegne players. Each game has its own incentive mechanism with its own weight matrix, bond pool, and emissions.

## The Concept

- **Game developers** design a competition for the best AI for your game, which becomes a mechanism on the subnet
- **Miners** receive game state, return actions. Any technique: FSM, RL, LLM, behavior trees. Only outputs are scored.
- **Validators** run headless game sims, fan out state to miner axons, score episodes, set weights per mechanism. Also serve playable frontends for all games.
- **Stakers** back validators; game developers stake TAO into their game's mechanism to attract miner attention (market-driven prioritization).

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
