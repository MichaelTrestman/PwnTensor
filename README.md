# PwnTensor: Game AI on Bittensor

Miners compete to build the best ghost AI. Validators run the game, score the ghosts, and host the live frontend where anyone can play against miner-powered ghosts.

## How It Works

1. **Validators** run headless PacTensor simulations and serve the web frontend
2. **Miners** receive game state via `GameStateSynapse`, return ghost movement decisions
3. Ghost AI is scored on a **fun-score** metric (challenging but fair — target band 50-75/100)
4. Weights flow to miners whose ghosts create the most engaging gameplay

## Quick Start

```bash
# Clone and enter
git clone https://github.com/your-org/PwnTensor.git
cd PwnTensor

# Run validator
cp env.example .env  # edit with your wallet/netuid
docker-compose up -d

# Or run directly
pip install -e .
python validator.py --network finney --netuid YOUR_NETUID --coldkey your_wallet --hotkey your_hotkey
```

## For Miners

Your job: implement better ghost AI. The miner contract is simple:

- **Receive**: `GameStateSynapse` with full game state (player position, ghost positions, maze layout, tick)
- **Return**: `ghost_actions` — a list of `{dr, dc}` direction vectors, one per ghost
- **Constraint**: respond within 150ms

The baseline ghost AI uses BFS + scatter/chase archetypes. Beat it.

## Structure

```
validator.py    — main Bittensor validator loop + weight setting
protocol.py     — GameStateSynapse definition
reward.py       — fun-score calculation + rank normalization
frontend/       — PacTensor web game (served by validators)
knowledge/      — Chi-compatible knowledge files for vibe-coding agents
```

## Built on Chi

This subnet follows the [Chi template](https://github.com/unconst/Chi) pattern. Point Cursor at `@knowledge` and go.
