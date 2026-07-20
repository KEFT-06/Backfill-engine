# backfill-hell

Reprocessing years of GitHub event history without breaking production — an
**idempotent, resumable** backfill engine with **reconciliation proofs**.

Not a "pipeline" project. A project about **idempotence, crash recovery and
reconciliation**: kill it at 60%, restart, and it resumes exactly where it stopped —
zero duplicates, zero gaps, **proven, not claimed**.

## The problem (in business terms)

A transformation bug ships and quietly corrupts a metric for years. Fixing the code is
easy; reprocessing the history is not:

- the daily pipeline cannot stop while history is rewritten;
- reruns must be idempotent, or you double-count;
- the job **will** die halfway — it has to resume, not restart;
- some files are corrupt and will never succeed — the backfill must survive them;
- the event schema **drifted** over the years — old data does not look like new data;
- and at the end, you must **prove** the result is correct.

Source: [GitHub Archive](https://data.gharchive.org/) — one `.json.gz` per hour since 2011.

## Results

| Métrique | Valeur |
|---|---|
| Partitions traitées bout-en-bout (données réelles, 2015-01-01) | 24 h |
| Crashs **réels** survécus, reprise automatique | 3 (0 trou, 0 doublon) |
| Époques de schéma découvertes **empiriquement** | 3 |
| Downtime production pendant le backfill | **0** (latence plate, prouvée) |
| Écarts de réconciliation inexpliqués | **0** |
| Poison pills : isolés, backfill continue | prouvé |
| Compaction horaire → journalière | sans perte (checksum-prouvée) |
| Qualité | `mypy --strict`, `ruff`, `pytest` — verts |

> Périmètre prouvé : 1 journée réelle de bout en bout, plus des preuves ciblées pour
> chaque problème dur. Le moteur et la projection de coût ([`observability/cost.py`](src/backfill/observability/cost.py))
> sont prêts pour un run annuel — c'est la prochaine étape, pas un blocage de conception.

## What broke — [docs/incidents.md](docs/incidents.md)

La section que les lecteurs seniors ouvrent en premier. 7 incidents réels, écrits à chaud :

- **INC-001** — le pipeline naïf meurt sur une coupure réseau et ne sait pas reprendre → d'où le ledger.
- **INC-005** — un téléchargement sans timeout fige tout le worker → tout appel réseau doit avoir un timeout.
- **INC-006** — un bug de typage SQL invisible pour `mypy`, **attrapé par un test d'intégration** (types = forme, tests = comportement).
- (+ conflit de port Postgres, moteur Docker figé, User-Agent bloqué…)

## The 7 hard problems

1. **Idempotence par partition** — écrasement atomique (`.tmp` + `os.replace`), jamais d'`INSERT` nu. [sinks](src/backfill/) · [ADR 005](docs/decisions/005-atomic-swap.md)
2. **Isolation prod / backfill** — plages de dates disjointes, aucun verrou. Downtime = 0 **prouvé**. [ADR 004](docs/decisions/004-isolation-strategy.md)
3. **Reprise sur panne** — le backfill est piloté par le [ledger](src/backfill/ledger/repository.py) (`SELECT ... FOR UPDATE SKIP LOCKED`), jamais par une boucle `for`.
4. **Poison pills** — N tentatives → quarantaine → le backfill **continue**. [runner](src/backfill/runner/worker.py)
5. **Dérive de schéma** — époques **découvertes** ([`discover_schema_eras.py`](scripts/discover_schema_eras.py)), parseurs versionnés. [docs/schema-eras.md](docs/schema-eras.md)
6. **Débit & coût** — concurrence via `SKIP LOCKED`, compaction, projection de coût. [docs/benchmarks.md](docs/benchmarks.md)
7. **Réconciliation** — comptages + checksums, chaque écart expliqué. [reconciliation](src/backfill/reconciliation/report.py)

## Decisions (with the rejected alternatives)

Un ADR par décision, avec les alternatives écartées et **pourquoi** :
[001 granularité horaire](docs/decisions/001-partition-granularity.md) ·
[002 no Spark](docs/decisions/002-no-spark.md) ·
[003 runner avant Dagster](docs/decisions/003-runner-vs-dagster.md) ·
[004 isolation](docs/decisions/004-isolation-strategy.md) ·
[005 bascule atomique](docs/decisions/005-atomic-swap.md) ·
[006 DuckDB](docs/decisions/006-compute-engine.md)

## How I prove it's correct

- **Checksum indépendant de l'ordre** : `bit_xor` de hashs de lignes — mêmes lignes, tout ordre → même empreinte. Rejouer une partition donne le **même** checksum (idempotence).
- **Réconciliation ledger ↔ stockage** : on relit chaque Parquet et on compare au reçu du ledger (comptage + checksum). Une corruption injectée est **détectée** (démo).
- **Compaction sans perte** : le checksum du fichier journalier == le XOR des checksums horaires — mathématiquement, rien n'est perdu.

## What I'd do differently

- Épingler la borne basse exacte de l'époque 2011↔2012 (balayage mois par mois).
- Remplacer le placeholder de coût par un vrai run annuel chiffré.
- Backoff temporisé sur les retries (aujourd'hui : re-`pending` immédiat).
- Wrapper le runner dans Dagster (planification + UI) une fois le cœur prouvé — comme prévu à l'[ADR 003](docs/decisions/003-runner-vs-dagster.md).

## Run it

```bash
make up          # Postgres + MinIO
make backfill    # run the backfill (window in pipelines/backfill.py)
make reconcile   # ledger vs storage, numbers-first report
make chaos       # kill a worker mid-run, resume, prove zero-dup/zero-gap
```
