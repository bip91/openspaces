# Jeu de test (lot 5)

Jeu de données préparé à l'avance, résultat attendu connu, pour mesurer les
critères du scénario (voir `docs/spec.md`, section « Scénario, critères et
découpage »). Rejoué à chaque lot qui en a besoin — pas seulement au lot 5.

## Projet source

Le « projet Django réel » du scénario est **openspaces lui-même**
(`engine/models.py`) : 15 modèles, migrations et historique Git déjà en
place, pas besoin d'aller chercher un projet externe. L'adaptateur
`adapters/django/` (à écrire, lot 5) introspecte ces modèles pour produire
des objets `Table`.

Conséquence : les « tables » importées dans le scénario sont `Space`,
`Layer`, `ObjectType`, `ViewTemplate`, `Object`, `Version`, `Typing`,
`Proposal`, `Link`, `Blob`, `Provenance`, `Aspect`, `Event`, `Divergence`,
`Embedding` — les modèles réels du moteur.

## Habillage métier des textes fonctionnels

Pour éviter que l'extraction d'exigences et les liens proposés soient
triviaux (mots du glossaire recopiés tels quels), les mails de
`mails/` sont écrits du point de vue d'un **atelier de design partagé**
qui voudrait un outil « comme openspaces », décrit en langage métier plutôt
qu'en vocabulaire de modèle de données. Correspondance utilisée pour écrire
les mails (et pour vérifier les liens proposés) :

| Modèle réel | Habillage métier |
| --- | --- |
| `Space` | Projet (ex. « Refonte boutique Lumen ») |
| `Layer` (+ `role`, `shared`) | Vue (designer / développeur front) ; `shared` = visible du client |
| `ObjectType` (+ `parent`, `traits`, `schema`) | Type de composant (bouton, écran, palette) ; hiérarchie et gabarit d'attributs |
| `ViewTemplate` | Gabarit d'affichage (tableau, diagramme de dépendances, doc) |
| `Object` | Composant (un bouton, un écran, une palette) |
| `Version` (+ `author`/`agent_name`, `nature`, `sha256`, `validated`) | Itération d'un composant ; signée par une personne ou un agent, jamais les deux |
| `Typing` | Façon dont un composant est vu dans une vue donnée |
| `Link` (+ `nature`, `status`, `version`) | Dépendance entre composants |
| `Proposal` (+ `decision`, `duration_ms`) | Suggestion automatique (acceptée / retouchée / refusée) |
| `Blob` | Fichier source joint (export, maquette) |
| `Provenance` (+ `source_blob`, `anchor`) | Origine d'une itération |
| `Aspect` | Règle automatique de l'atelier (notification, alerte) |
| `Event` | Journal des modifications |
| `Divergence` | Retour contradictoire entre vues, jamais corrigé seul |
| `Embedding` | Recherche d'un composant par le sens, pas seulement par son nom |

Cette correspondance est la référence utilisée pour vérifier les liens
proposés (`liens_attendus.md`) et les divergences attendues
(`divergences_attendues.md`) — elle ne doit pas apparaître telle quelle dans
les mails.

## Contenu du jeu

- `mails/` — 9 textes fonctionnels contenant des exigences : 2 ambiguës
  (07, 09), 1 contradictoire avec le code réel (08).
- `divergences_attendues.md` — 5 cas où un changement technique contredit
  une exigence, 3 cas sans contradiction (mesure des fausses alertes).
- `retouches_spec.md` — 10 modifications en prose, de la plus simple
  (renommer un champ) à la plus floue (aucune traduction directe sur le
  modèle), avec la traduction attendue.
- `liens_attendus.md` — référence des correspondances exigence ↔ table pour
  comparer aux liens proposés par le lot 4.
