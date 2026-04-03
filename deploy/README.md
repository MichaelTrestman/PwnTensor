# PwnTensor Deployment

## Architecture

```
┌──────────────────────────────────────────────┐
│  Kubernetes Cluster                          │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │  Validator Pod                          │ │
│  │  ┌──────────┐  ┌────────────────────┐   │ │
│  │  │validator  │  │ frontend (nginx)   │   │ │
│  │  │container  │  │ serves all 3 game  │   │ │
│  │  │(Python)   │  │ UIs on :8080       │   │ │
│  │  │           │  │                    │   │ │
│  │  │ - bittensor│  │ /         PacTensor│   │ │
│  │  │ - game sims│  │ /melee    MeleeL  │   │ │
│  │  │ - scoring  │  │ /kaz      KAZ     │   │ │
│  │  │ - weights  │  │                    │   │ │
│  │  └──────────┘  └────────────────────┘   │ │
│  │        │                    │            │ │
│  │   wallet volume      frontend volume    │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  ┌──────────────┐                            │
│  │  Ingress     │  ← external traffic        │
│  │  :80/:443    │                            │
│  └──────────────┘                            │
└──────────────────────────────────────────────┘
```

## Environments

### Local (minikube/kind)
- `deploy/local/` — Kustomize overlay for local dev
- Uses `kind` or `minikube`
- Builds images locally
- Wallet mounted from host

### Staging (GKE)
- `deploy/staging/` — Kustomize overlay for GCloud
- Hits Bittensor testnet
- Images from GHCR
- Wallet from GKE Secret
- Frontend behind GKE Ingress with managed TLS

## Quick Start

```bash
# Local
kind create cluster --name pwntensor
kubectl apply -k deploy/local/

# Staging
gcloud container clusters get-credentials pwntensor-staging --zone us-central1-a
kubectl apply -k deploy/staging/
```
