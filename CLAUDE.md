# CLAUDE.md — Environnement objet collaboratif (maquette)

## Le projet

Maquette d'un moteur d'objets typés, versionnés et liés, partagés entre plusieurs lectures (calques) dans un même espace.
Le but n'est pas un produit : la maquette vérifie quatre hypothèses (voir la spec).

- Spec de référence : « Environnement objet collaboratif — expression de besoin et spec maquette » (Claude Docs, exportée en Markdown dans `docs/spec.md`).
- Problème de fond : la manière dont l'utilisateur interagit avec l'information. Le moteur en est la condition ; l'interaction sera traitée après la maquette.
- État : lots 1 (moteur), 2 (vues) et 3 — calques et aspects — faits. Le noyau du bus de coordination (aussi listé au lot 3) reste à faire, dans une passe séparée.

## Langue

- **Identifiants de code en anglais** (modèles, champs, fonctions, outils MCP, routes).
- Documentation de conception, textes affichés à l'utilisateur et messages de commit : **français**.
- Commentaires et docstrings : anglais, courts ; ne commenter que le pourquoi.
- Toujours utiliser le glossaire ci-dessous ; ne pas inventer de synonymes.

## Glossaire FR → code

| Concept (spec) | Identifiant | Remarque |
| --- | --- | --- |
| Objet | `Object` / `object` | identité stable (UUID), jamais réutilisée |
| Type | `ObjectType` | schéma JSON + parent + traits + fusion |
| Version | `Version` | copie complète des attributs, empreinte SHA-256 |
| Typage | `Typing` | un objet peut avoir un type par calque |
| Vue | `View` | représentation d'un objet |
| Gabarit de vue | `ViewTemplate` | vue + rendu (table, mermaid, markdown) |
| Aspect | `Aspect` | règle greffée : coupe (`pointcut`) + action (`action`) |
| Lien | `Link` | relation typée entre objets |
| Correspondance | `Correspondence` | lien entre objets de calques différents (nature de `Link`) |
| Calque | `Layer` | lecture d'un espace par une personne ou un rôle |
| Espace | `Space` | périmètre de travail, privé ou partagé |
| Objet-frontière | `boundary object` | objet partagé par plusieurs calques (pas de modèle dédié) |
| Divergence | `Divergence` | écart signalé entre calques, jamais corrigé en silence |
| Objet dérivé | `derived object` | produit par une opération, recalculable |
| Opération | `Operation` | verbe humain ou opération IA |
| Proposition | `Proposal` | sortie d'une opération IA en attente de décision |
| Provenance | `Provenance` | d'où vient une version |
| Ancre | `Anchor` | citation + contexte dans une source |
| Événement | `Event` | journal des modifications, base du tissage des aspects |
| Blob | `Blob` | contenu volumineux adressé par empreinte |
| Moteur d'objets | `engine` | seul point d'écriture |
| Bus de coordination | `bus` | courtier MCP (lot 3) |
| Univers local / global | `local universe` / `global universe` | hors maquette |

## Pile

- Python 3.13, Django 6, PostgreSQL 16 avec pgvector (aussi en local).
- API interne : Django Ninja. Validation des types : `jsonschema`.
- Tâches de fond : Procrastinate (file sur PostgreSQL).
- IA : Pydantic AI (sorties structurées), passerelle LiteLLM, petit modèle local via Ollama, embeddings multilingues locaux.
- Interface : gabarits Django, htmx, Alpine.js ; Mermaid.js, Tabulator, diff2html.
- Exposition : serveur MCP au-dessus des services du moteur.

## Structure du dépôt (cible)

```
config/            réglages Django
engine/            modèles, services d'écriture, événements, aspects
engine/services/   seul chemin d'écriture (create, update, link, propose, decide)
mcp_server/        contrat MCP : outils et ressources au-dessus de engine/services
ui/                pages, vues (table, mermaid, markdown), htmx
adapters/django/   introspection des modèles Django vers des objets Table
ai/                opérations IA (extraction, réinterprétation, liens), journal des propositions
tests/             tests par lot
docs/              spec exportée, décisions
```

## Règles d'architecture (non négociables)

1. **Toute écriture passe par `engine/services`.** Jamais d'écriture directe via l'ORM ailleurs, jamais de SQL brut hors du moteur.
2. **Chaque modification crée une version et un événement**, attribués (humain ou agent, avec l'opération d'origine).
3. **Écriture optimiste** : chaque mise à jour fournit la version attendue ; conflit = refus, pas d'écrasement, pas de verrou.
4. **Une modification humaine n'est jamais écrasée par un recalcul** : le recalcul la signale.
5. **Le modèle objet vit dans le moteur**, pas dans des fonctionnalités propres à PostgreSQL (pas de logique métier en déclencheurs ou procédures). pgvector et le plein texte servent seulement à l'index.
6. **Les attributs sont validés par le schéma du type** à chaque écriture.
7. **Les aspects s'exécutent dans l'application** (signaux Django ou bus interne) et chaque objet peut lister les aspects qui s'appliquent à lui.
8. **Une incohérence entre calques crée une `Divergence`**, jamais une correction automatique.
9. **Toute sortie d'IA est une `Proposal`** : entrée, sortie, modèle, décision, correction, durée. Rien n'est appliqué sans décision (humaine ou politique explicite).
10. **Le contrat MCP est défini avant l'interface web** ; l'interface web utilise les mêmes services.

## Ce qu'il ne faut pas faire (leçons retenues)

- Pas d'ontologie globale imposée ni de saisie manuelle obligatoire (échec WinFS, Nepomuk).
- Pas de synchronisation bidirectionnelle entre copies : une seule source par objet, les vues sont des projections (échec MDA).
- Pas de logique opaque dans le bus : noyau déterministe, intelligence en services conseillers (échec ESB).
- Pas d'aspect invisible : toujours traçable depuis l'objet (critique AOP).
- Pas de fonctionnalité hors périmètre de la maquette sans accord (voir ci-dessous).

## Périmètre de la maquette

Dans : un espace, deux calques (développeur, fonctionnel), types Table, Champ, Flux, Exigence, Décision ; vues table, Mermaid, Markdown ; trois aspects (notification de changement de champ, divergence exigence/contrainte, attribution) ; trois opérations IA (extraction d'exigences, réinterprétation de la spec, proposition de liens) ; journal des propositions ; serveur MCP.

Hors : shell de bureau, synchronisation et partage d'espaces, univers global, adaptateur mail, ajustement de modèle, droits fins, rosace, poche, barres.

## Lots

1. Moteur : modèle de données, services d'écriture, versions, provenance, contrat MCP.
2. Vues : table, Mermaid, Markdown, édition structurée. Réflexion sécurité (voir ci-dessous).
3. Calques et aspects ; noyau du bus de coordination (registre typé, droits, journal).
4. IA : extraction, réinterprétation, liens, journal des propositions.
5. Test : scénario sur un projet Django réel, mesure des critères.

## Sécurité (à concevoir au lot 2)

Orientation retenue, à approfondir : cohérence au niveau de l'espace, avec possibilité de restreindre l'accès au niveau d'un objet ou d'un attribut lors du partage. Le contenu des sources (mails, documents) est non fiable pour les agents. D'ici là : ne rien concevoir qui empêche un filtrage par objet ou par attribut (par exemple, ne pas dupliquer les attributs hors de `Version`).

Vérifié au lot 2 : `render_view` lit toujours `Version.attributes` directement (engine/services/render.py), aucune copie des attributs ailleurs (pas dans `ViewTemplate`, pas dans l'interface). Un futur filtrage par objet ou par attribut lors d'un partage (calques, lot 3) reste donc possible sans remodeler les vues.

## Commandes

```
# installation
python3.13 -m venv .venv
.venv/bin/pip install -e ".[dev]"
docker compose up -d                     # PostgreSQL 16 + pgvector
.venv/bin/python manage.py migrate

# lancement des tests
.venv/bin/pytest

# serveur de dev (harnais de test ui/, pas l'interface du lot 2)
.venv/bin/python manage.py seed_demo      # espace/calque/type de démo, une fois
.venv/bin/python manage.py runserver

# serveur MCP (stdio)
.venv/bin/python -m mcp_server
```

## Méthode de travail

- Tests d'abord pour les services du moteur ; un lot n'est terminé que si ses tests passent.
- Petites modifications, une intention par commit.
- En cas de doute sur un concept, la spec fait foi ; en cas de contradiction entre spec et code, signaler plutôt que trancher seul.
