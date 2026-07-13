# Incidents

> The journal of what actually broke — written **hot**, at the moment it happens,
> not reconstructed at the end. This is the section senior readers open first.

Each incident follows the same four beats. Keep them short and honest.

---

## Template (copy for each new incident)

### INC-000 — <one-line symptom>

- **Date:**
- **Phase:**
- **Symptôme** — what you observed (error, wrong number, stuck run).
- **Hypothèse** — what you *thought* was the cause, before checking.
- **Diagnostic** — what you actually found, and how you found it.
- **Correctif** — what you changed, and how you confirmed it worked.
- **Leçon** — the one sentence you'd tell your past self.

### INC-001 — Le pipeline naïf meurt sur une coupure réseau et ne sait pas reprendre

- **Date:** 2026-07-13
- **Phase:** 1
- **Symptôme:** J'ai lancé l'ingestion des 24 heures. Elle est morte à l'heure 09 sur une ConnectionResetError 'le serveur a coupé'. Résultat : 9 heures écrites, 15 manquantes
- **Hypothèse:** une coupure réseau passagère / du rate-limiting du serveur
- **Diagnostic:** La boucle for ne reprend pas où elle s'est arrêtée. Son avancement vit dans la mémoire du processus, qui meurt avec lui. Au redémarrage, range24 repart de l'heure 00 : rien n'enregistre le progrès.
- **Correctif:** le ledger — un registre persistant dans PostgreSQL qui note le statut de chaque heure, pour reprendre via WHERE status != 'done'
- **Leçon:** La reprise sur panne, c'est de l'état durable, pas une boucle for.

---

<!-- Real incidents start below. First ones expected in Phase 3. -->
