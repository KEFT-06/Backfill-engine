# Lancer le projet (Windows / PowerShell)

Guide pas-à-pas pour démarrer `backfill-hell` sous Windows, avec les pièges déjà
rencontrés et leur solution.

## Prérequis (une seule fois)

1. **Docker Desktop** — [docker.com](https://www.docker.com/products/docker-desktop/). Ouvre l'appli et attends « Engine running » (icône baleine verte, en bas à gauche).
2. **uv** (gère Python + les dépendances) :
   ```powershell
   irm https://astral.sh/uv/install.ps1 | iex
   ```
   Puis **ferme et rouvre le terminal**.

## Installation du projet (une seule fois)

```powershell
cd C:\Users\FOKO\Documents\GitHub\Backfill-engine
uv sync --dev          # crée le venv, installe tout, télécharge Python 3.12
```

## Démarrage quotidien

```powershell
# 1. Docker Desktop doit être ouvert et "Engine running".
# 2. Lance l'infra (Postgres sur 5433 + MinIO) :
docker compose up -d
docker compose ps      # postgres doit être "healthy" sur 0.0.0.0:5433->5432

# 3. Applique la migration du ledger (première fois seulement) :
Get-Content .\src\backfill\ledger\migrations\001_create_ledger.sql -Raw |
  docker compose exec -T postgres psql -U backfill -d backfill
```

## Les commandes du projet

```powershell
$env:PYTHONUTF8 = 1                       # évite les erreurs d'encodage Windows

uv run python -m pipelines.backfill       # le backfill (fenêtre dans pipelines/backfill.py)
uv run python scripts/reconcile.py        # rapport de réconciliation (ledger vs stockage)
uv run python scripts/chaos_kill.py       # démo chaos : kill → reprise → 0 trou / 0 doublon
uv run python scripts/discover_schema_eras.py   # découverte des époques de schéma
```

Avec `make` installé, les raccourcis équivalents : `make backfill`, `make reconcile`,
`make chaos`, `make discover`, `make up`, `make down`.

## Vérifier que tout est sain

```powershell
uv run ruff check .    # style
uv run mypy            # types stricts
uv run pytest -q       # tests (le test chaos se "skip" si Postgres est éteint)
```

## Pièges Windows connus (et leur solution)

| Symptôme | Cause | Solution |
|---|---|---|
| `docker : n'est pas reconnu` | Terminal ouvert avant l'install de Docker (PATH pas à jour) | Ouvre un **terminal neuf**, ou rafraîchis le PATH : `$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")` |
| `UnicodeEncodeError` / caractères cassés | Console en `cp1252` | `$env:PYTHONUTF8 = 1` avant de lancer |
| `authentification échouée` en français sur 5432 | Un **PostgreSQL natif** occupe le port 5432 | Le projet utilise le port **5433** exprès — ne change rien, c'est voulu |
| `docker compose exec` **se fige** | `exec` + entrée standard bloque sous Windows | Utiliser une connexion réseau directe (psycopg sur `localhost:5433`) plutôt que `docker exec` |
| Toutes les commandes docker se figent / `npipe ... cannot find` | Moteur Docker Desktop coincé | **Redémarre la machine** (les données survivent, elles sont sur le volume disque) |
| Un téléchargement se fige puis `Fatal Python error ... GIL` | Réseau lent + kill en plein SSL | C'est le timeout qui tue le process ; relance, la reprise repart du ledger |

## En cas de doute

L'état vrai du backfill est **toujours** dans le ledger :

```powershell
docker compose exec -T postgres psql -U backfill -d backfill -c "SELECT status, count(*) FROM ledger GROUP BY status;"
```
