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

### INC-002 — La source (GH Archive) refuse le User-Agent par défaut de Python (403)

- **Date:** 2026-07-13
- **Phase:** 1
- **Symptôme:** Le téléchargement d'un fichier horaire échouait avec `HTTP 403 Forbidden` depuis Python (`urllib`), alors que `Invoke-WebRequest` (PowerShell) téléchargeait le même fichier sans problème.
- **Hypothèse:** Un truc côté réseau ou droits d'accès au fichier.
- **Diagnostic:** Le CDN de GH Archive (Fastly) filtre selon le `User-Agent`. Il bloque l'agent par défaut de Python (`Python-urllib/3.12`), qu'il prend pour un bot. Indice clé : ça marchait avec un outil mais pas l'autre → regarder les en-têtes HTTP envoyés.
- **Correctif:** Envoyer un `User-Agent` d'apparence normale dans la requête. Confirmé : le téléchargement passe.
- **Leçon:** Quand un outil télécharge et un autre non, compare ce que les deux envoient — souvent le User-Agent.

### INC-003 — Le conteneur Docker Postgres masqué par un PostgreSQL natif sur le port 5432

- **Date:** 2026-07-13
- **Phase:** 2
- **Symptôme:** Impossible de se connecter au ledger : `authentification par mot de passe échouée pour l'utilisateur backfill`, alors que le conteneur Docker tournait bien.
- **Hypothèse:** Mauvais identifiants dans notre conteneur, ou conteneur mal démarré.
- **Diagnostic:** Le message d'erreur était **en français** — or l'image `postgres:16` répond en anglais. Donc ce n'était pas notre conteneur qui répondait. `Get-Service` a révélé un service `postgresql-x64-16` **natif** qui occupait déjà `0.0.0.0:5432`. Toute connexion à `localhost:5432` tombait sur ce Postgres natif, pas sur le conteneur.
- **Correctif:** Mapper le conteneur sur le port `5433` (docker-compose + config + .env). Confirmé : la migration s'applique et le ledger répond.
- **Leçon:** Un port déjà occupé par un service préexistant fait qu'on se connecte silencieusement au mauvais serveur ; le symptôme (auth refusée) ne pointe pas la cause. Ici, la langue du message d'erreur a trahi le bon coupable.

### INC-004 — Docker figé et connexions fantômes bloquant les commandes

- **Date:** 2026-07-13
- **Phase:** 2
- **Symptôme:** Toutes les commandes `docker` (même `docker compose ps`) se figeaient. Plus tard, un `TRUNCATE ledger` restait bloqué indéfiniment.
- **Hypothèse:** Un problème passager, ou une commande mal formée.
- **Diagnostic:** Deux causes distinctes. (1) Le moteur Docker Desktop s'était bloqué à force de commandes `exec` interrompues. (2) Des scripts Python tués brutalement avaient laissé des connexions Postgres « fantômes » (idle-in-transaction) qui tenaient un verrou sur `ledger` ; `TRUNCATE` (verrou exclusif) attendait ces verrous pour toujours.
- **Correctif:** Redémarrer Docker Desktop (moteur), puis redémarrer le conteneur Postgres (`docker compose restart postgres`) pour balayer toutes les connexions fantômes d'un coup. Les données du ledger survivent (sur le volume disque).
- **Leçon:** Sur Windows, éviter `docker exec` avec entrée standard (ça fige) — passer par une connexion réseau directe (psycopg). Et un process tué brutalement peut laisser un verrou orphelin en base : redémarrer le serveur nettoie tout.

### INC-005 — Le worker se fige (puis plante) sur un téléchargement sans timeout

- **Date:** 2026-07-14
- **Phase:** 3
- **Symptôme:** Pendant le vrai backfill, le worker s'est figé en plein téléchargement, puis a planté avec une `Fatal Python error: PyEval_SaveThread ... GIL` (pendant `do_handshake` SSL) quand un timeout externe l'a tué au bout de 180 s.
- **Hypothèse:** Un bug de threading / GIL de Python, ou un problème d'installation SSL.
- **Diagnostic:** L'erreur GIL n'était que l'agonie du process tué **en plein appel SSL** — pas la cause. La vraie cause : notre `urlopen(...)` n'avait **aucun timeout**. Quand une connexion meurt ou traîne sans rien renvoyer, Python attend **indéfiniment** → le worker se fige jusqu'à ce qu'on le tue. Le ledger a confirmé une partition bloquée en `running` à chaque mort.
- **Correctif:** Ajouter un `timeout=30` à `urlopen` (constante `_TIMEOUT_SECONDS`). Un téléchargement bloqué lève désormais une erreur au bout de 30 s → attrapée par le runner → `mark_failed` → réessai. Confirmé : le backfill s'est terminé **24/24** après reprise.
- **Leçon:** Tout appel réseau doit avoir un timeout. Sans lui, un seul téléchargement mort fige le worker entier — et le ledger + la reprise sont ce qui a permis de survivre à chaque plantage sans perdre de travail.

---

<!-- Prochains incidents attendus en Phase 3 quand on élargira la plage (fichiers manquants, corrompus, dérive de schéma). -->