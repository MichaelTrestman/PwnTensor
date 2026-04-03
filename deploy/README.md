# PwnTensor Deployment

## Architecture

```
┌───────────────────────────────────────────────────────┐
│  Kubernetes Cluster                                   │
│                                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Validator Pod                                   │ │
│  │  ┌──────────────┐  ┌──────────────────────────┐  │ │
│  │  │ validator     │  │ frontend (nginx)         │  │ │
│  │  │ (Python)      │  │ serves 3 game UIs :8080  │  │ │
│  │  │               │  │                          │  │ │
│  │  │ runs sims     │  │ /         PacTensor      │  │ │
│  │  │ queries miners│  │ /melee/   Melee Light    │  │ │
│  │  │ sets weights  │  │ /kaz/     KAZ            │  │ │
│  │  └──────┬───────┘  └──────────────────────────┘  │ │
│  │         │ dendrite                                │ │
│  │         ▼                                         │ │
│  │  ┌──────────────┐                                 │ │
│  │  │ Miner Pod    │  (separate deployment,          │ │
│  │  │              │   separate wallet, scales       │ │
│  │  │ axon :8091   │   independently)                │ │
│  │  │              │                                 │ │
│  │  │ miner.py     │  receives GameStateSynapse      │ │
│  │  │ miner_ai.py  │  returns actions                │ │
│  │  └──────────────┘                                 │ │
│  │                                                   │ │
│  │  ┌──────────────┐                                 │ │
│  │  │  Ingress     │  ← external traffic (frontend)  │ │
│  │  │  :80/:443    │                                 │ │
│  │  └──────────────┘                                 │ │
│  └──────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

## How it works

1. **Validator** runs headless game simulations per mechanism
2. Validator sends `GameStateSynapse` to each **miner**'s axon via dendrite
3. **Miner** receives game state, runs AI logic (`miner_ai.py`), returns actions
4. Validator steps the sim, scores the episode, sets weights on chain
5. **Frontend** (nginx) serves playable game UIs — players see miner AI in action

Miners and validators run on **separate wallets** with separate keys.

## Environments

### Local (docker-compose)
```bash
cp env.example .env  # edit wallet names
docker-compose up -d
# Validator: pwntensor-validator
# Miner: pwntensor-miner (axon on :8091)
# Frontend: http://localhost:8080
```

### Local (kind/minikube)
```bash
kind create cluster --name pwntensor
docker build -t pwntensor-validator:local .
docker build -f Dockerfile.miner -t pwntensor-miner:local .
kind load docker-image pwntensor-validator:local --name pwntensor
kind load docker-image pwntensor-miner:local --name pwntensor
kubectl apply -k deploy/local/
```

### Staging (GKE)
```bash
gcloud container clusters get-credentials pwntensor-staging --zone us-central1-a

# Create wallet secrets
kubectl -n pwntensor create secret generic pwntensor-wallet-files \
  --from-file=~/.bittensor/wallets/validator/
kubectl -n pwntensor create secret generic pwntensor-miner-wallet-files \
  --from-file=~/.bittensor/wallets/miner/

kubectl apply -k deploy/staging/
```

## Images

CI builds two images (both pushed to GHCR):
- `ghcr.io/<org>/pwntensor-validator` — validator + game sims + scoring
- `ghcr.io/<org>/pwntensor-miner` — miner axon + baseline AI

Miners replace `miner_ai.py` with their own strategies and build their own image.
