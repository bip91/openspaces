# Environnement objet collaboratif — expression de besoin et spec maquette

Nov 21, 2026 · @Bruno Pennec

## Contexte et constat

Le besoin n'est pas un meilleur gestionnaire de fenêtres, mais un substrat commun d'objets typés, liés et versionnés, sous les applications.

La réflexion est partie d'un window manager Linux « objet », dans l'esprit des systèmes des années 80 (Xerox Star, Smalltalk). Elle a montré trois choses :

- **Le coût est dans les bascules** (environ 150 par jour) : comparer, voir un résultat, reprendre une information, jongler entre sujets. Ce sont des symptômes du cloisonnement des applications, pas un problème de placement des fenêtres.
- **Un WM reste en aval des applications** : il peut accélérer les gestes, pas supprimer le cloisonnement. Les gains restent incrémentaux.
- **Le système de fichiers n'a pas évolué** : pas d'identité stable, de types, de liens, de fragments, de provenance ni d'historique. Chaque application réinvente son stockage, d'où les silos.

Le code possède déjà les propriétés qui manquent ailleurs (adressable, versionné, vérifiable, dépendances calculables) : c'est pour cela que le travail avec des agents IA y fonctionne bien. L'objectif est de donner ces propriétés à toute l'information de travail.

## Le problème de fond : interagir avec l'information

Le problème de base est la manière dont l'utilisateur interagit avec l'information : aujourd'hui il interagit avec des applications, et c'est lui qui fait circuler l'information entre elles. Tout le reste du document sert ce problème.

| Aujourd'hui, l'utilisateur… | Demain, l'utilisateur… |
| --- | --- |
| lance une application, puis cherche un fichier | désigne un objet, puis ce qu'il veut en faire |
| range et classe pour retrouver | retrouve par le sens, le système propose les rattachements |
| bascule pour comparer, voir un résultat, reprendre une info | voit les objets liés côte à côte, sans basculer |
| recopie d'un outil à l'autre | relie, et la vue cible se met à jour |
| reprend à la main tout ce qui dépend d'un changement | valide les propagations proposées |
| exécute chaque transformation | délègue, puis arbitre et retouche |
| reconstruit seul le contexte d'un sujet | retrouve un espace dans l'état où il l'a laissé |

La désignation suit quatre modes, du plus immédiat au plus abstrait : la **position** (ce qui est sous les yeux), le **nom** (ce qu'on connaît), le **sens** (ce qu'on a oublié), l'**intention** (ce qu'on veut faire). L'utilisateur passe de la manipulation directe à la délégation et l'arbitrage, sans perdre la main à aucun niveau.

**En perspective.** Le substrat d'objets décrit ensuite est la condition de cette interaction, pas sa fin. La maquette le vérifie d'abord avec une interface volontairement simple ; la phase suivante traitera l'interaction elle-même : verbes universels, dépôt sur une cible avec rosace, deux barres en flux gauche-droite, poche, ligne d'intention, disposition des vues déduite des liens, et surface de supervision du travail des agents.

## Expression de besoin globale

L'utilisateur veut travailler sur des objets et leurs relations, quel que soit l'outil qui les a produits, sans organiser ni recopier l'information à la main.

| # | Besoin | Exemple |
| --- | --- | --- |
| B1 | Retrouver par le sens plutôt que par le classement | « le devis badge de la semaine dernière » |
| B2 | Emporter un objet avec sa grappe (fil, pièces, suites) | déplacer un mail dans un sujet avec tout son contexte |
| B3 | Fendre l'information en idées et remonter à la source | extraire une décision d'un mail, retrouver le passage d'origine |
| B4 | Voir un même objet sous plusieurs formes et l'éditer dans chacune | une table en schéma, en tableau, en spec |
| B5 | Propager un changement à tout ce qui en dépend | modifier une colonne sans reprendre doc et analyse d'impact |
| B6 | Garder sa propre interprétation d'un objet partagé | vues développeur, fonctionnel, chef de projet, architecte |
| B7 | Voir les écarts d'interprétation entre rôles | une règle de gestion contredite par une contrainte technique |
| B8 | Déléguer les transformations à des agents et garder la main à chaque niveau | « mets à jour la spec », puis retouche directe |
| B9 | Comparer, voir un résultat, consulter une référence sans basculer | source et résultat côte à côte |
| B10 | Aucun entretien manuel de l'organisation | types, liens, rattachements proposés, validés d'un geste |
| B11 | Travailler seul ou à plusieurs, en local et hors ligne | un espace privé, puis partagé |
| B12 | Maîtrise des données : local par défaut, souverain, droits respectés | aucune fuite d'un espace vers un autre |

Le besoin vaut pour plusieurs métiers : développement (flux, tables, exigences), ADV (sujets construits depuis des mails, réponses préparées), architecture SI.

## Concepts et vocabulaire

L'utilisateur ne manipule que trois notions : objets, espaces, vues. Les autres restent internes ou n'apparaissent que lorsqu'elles servent.

| Terme | Définition | Équivalent connu |
| --- | --- | --- |
| Objet | Entité à identité stable, suite de versions, un ou plusieurs types | objet Smalltalk |
| Type | Définition d'attributs, contraintes et fonction de fusion ; global ou local, hérité par prototype | prototype (Self), schéma |
| Vue | Représentation d'un objet ; structurée (éditable dans les deux sens) ou narrative (dérivée, réinterprétée) | vue MVC, édition projectionnelle |
| Gabarit de vue | Une vue et son rendu (Markdown/Mermaid, table, Visio…), partageable | perspective Eclipse |
| Aspect | Préoccupation greffée sur des objets sans les modifier : règle, droit, provenance | aspect (AOP) |
| Lien | Relation typée entre objets ; une correspondance relie des objets de calques différents | context map (DDD) |
| Calque | Lecture d'un espace par une personne ou un rôle : ses types, aspects, vues et liens | bounded context (DDD), sujet (programmation orientée sujet) |
| Espace | Lieu de travail : objets-frontières, calques, correspondances, divergences ; privé ou répliqué | dépôt Git, espace Confluence |
| Objet-frontière | Objet partagé par plusieurs calques, lu différemment par chacun | boundary object (Star et Griesemer) |
| Divergence | Écart d'interprétation entre calques, toléré et signalé | conflit de fusion, ViewPoints |
| Objet dérivé | Produit par une opération (résumé, spec), recalculable, avec sa provenance | artefact de build |
| Opération | Verbe humain ou opération du modèle qui produit ou modifie des objets | message Smalltalk |
| Univers local | Le poste d'une personne : types appris, préférences, objets privés, espaces créés ou rejoints | image Smalltalk |
| Univers global | Ontologie de base, identités partagées, sources de vérité, copie de référence des espaces partagés | shared kernel (DDD) |

Un univers local peut se rattacher à plusieurs univers globaux (entreprise, personnel, association) ; chaque espace relève d'un seul. Pour l'utilisateur, ce sont des comptes, comme dans un client mail.

## Hiérarchie d'objets

L'ontologie de base tient en sept familles ; les types métier et les types appris en héritent, et les capacités qui traversent les familles passent par des traits.

> Schéma : hiérarchie de types (voir la version Claude Docs).

Lecture : un type hérite des attributs, contraintes, vues et aspects de son parent, et peut les redéfinir.

- **Héritage simple, par prototype** : un type local naît d'un objet concret répété (trois fiches complétées de la même façon proposent un type « Commande », enfant de Document ou de Fonctionnel).
- **Traits composables** pour ce qui traverse la hiérarchie : une Exigence et un Mail peuvent tous deux être Sensibles ; une Table et un Texte sont Versionnés.
- **Typage multiple par calque** : le même objet est une Table dans le calque développeur et une Entité dans le calque fonctionnel ; la hiérarchie s'applique dans chaque calque.
- **Les méta-objets sont des objets** : un Type, un Aspect ou un Gabarit de vue se versionne, se partage et s'hérite comme le reste.
- **Surcharge par instance** : un objet peut redéfinir localement une propriété de son type (cette table est sensible, ce dossier aussi).
- **Références globales** : une Personne ou un Objet distant (commande de l'ERP, document SharePoint) est référencé, jamais copié.

Les types Document reprennent la hiérarchie MIME existante (`text/markdown` hérite de `text/plain`) au lieu de la dupliquer.

## Exemples de bout en bout

Deux cas montrent les concepts ensemble : un objet de conception lu par quatre rôles, et un sujet métier construit depuis des mails.

**La table Commande, dans l'espace du projet**

| Calque | Ce qu'il voit de l'objet | Ce qu'il y ajoute |
| --- | --- | --- |
| Développeur | une table : colonnes, types, contraintes, migrations | contraintes techniques, index |
| Fonctionnel | une entité : règles de gestion, états | exigences, correspondances avec les colonnes |
| Chef de projet | un élément de lot : charge, échéance | tâches, jalons |
| Architecte | un composant dans un flux | interfaces, dépendances |

Déroulement : une décision est extraite d'un mail client (« délai de livraison facultatif pour les commandes internes »). Le développeur rend la colonne `delai` facultative. Le schéma et la spec dérivée se mettent à jour. Une divergence est signalée au fonctionnel, dont une exigence imposait un délai ; le chef de projet reçoit « règle de délai remise en cause, lot 3 concerné ». L'historique relie le changement à la décision et au passage du mail.

**Un sujet ADV construit depuis des mails**

1. Un mail client arrive ; il est rattaché à un sujet existant ou en crée un.
2. La fiche (client, produit, quantités, délais, statut) est complétée par extraction, chaque champ ancré dans le passage source.
3. Les écarts sont signalés (« quantité différente de la commande initiale »).
4. Une réponse est dérivée du modèle de réponse et de l'état du sujet ; l'utilisateur la retouche et l'envoie.
5. La réponse envoyée rejoint la grappe du sujet.

## Principes et invariants

**Principes**

1. L'objet avant l'application : on désigne un objet, puis un verbe.
2. Le système propose, l'utilisateur arbitre : aucune réorganisation ni action irréversible sans validation.
3. Pas de classement à entretenir : retrouver par le sens, rattacher par proposition.
4. Le moteur enrichit l'existant de l'extérieur, sans exiger que les applications changent.
5. Local par défaut, IA locale par défaut ; le distant est une décision explicite.
6. Le modèle objet vit dans le moteur, pas dans le stockage ni dans un outil tiers.
7. Complexité interne autorisée, complexité exposée minimale.

**Invariants**

1. L'identité d'un objet survit à ses modifications et à ses déplacements.
2. Une vue voit le global, ses propres calques et ceux qu'on lui partage. Le global ne lit jamais le local.
3. Une modification humaine n'est jamais écrasée par un recalcul, seulement signalée.
4. Les droits d'un objet dérivé sont l'intersection de ceux de ses sources.
5. Une incohérence entre calques est tolérée et signalée, jamais corrigée en silence.
6. Un dérivé n'est versionné comme vérité que s'il a été validé ou retouché.
7. Toute modification est attribuée (humain ou agent) et justifiable.
8. Les aspects qui s'appliquent à un objet sont visibles depuis cet objet (pas d'action à distance cachée).

## Registre des décisions

Ce registre évite de rouvrir des pistes déjà tranchées ; une décision ne change que par une nouvelle entrée motivée.

| # | Décision | Statut | Raison |
| --- | --- | --- | --- |
| D1 | Le problème est l'interaction avec l'information, pas le gestionnaire de fenêtres | retenu | un WM reste en aval des applications ; gains incrémentaux seulement |
| D2 | Substrat d'objets typés, versionnés, liés, superposé à l'existant | retenu | les applications n'adopteront pas un nouveau stockage |
| D3 | Retrouver par le sens plutôt que classer | retenu | le classement manuel n'est jamais entretenu |
| D4 | Un objet, plusieurs vues ; édition projectionnelle | retenu | évite la dérive des copies synchronisées |
| D5 | Aspect au sens de la programmation orientée aspect ; vue pour la représentation | retenu | distinguer préoccupation greffée et représentation |
| D6 | Types appris par prototype, pas d'ontologie globale complète | retenu | ontologie de base minimale, le reste émerge de l'usage |
| D7 | Vocabulaire : univers global, univers local, espace, calque | retenu | « sac » abandonné ; l'utilisateur ne voit qu'objets, espaces, vues |
| D8 | Incohérences entre calques tolérées et signalées | retenu | une divergence est une information |
| D9 | Local-first ; IA locale par défaut | retenu | maîtrise des données, souveraineté |
| D10 | PostgreSQL sur le poste comme au global, avec pgvector | retenu | une seule pile ; modèle objet dans le moteur pour rester remplaçable |
| D11 | Django et interface web pour la maquette, pas de shell | retenu | vérifier le modèle avant l'interaction |
| D12 | Bus de coordination MCP : noyau déterministe, intelligence en conseillers | retenu | leçon des ESB |
| D13 | Petit modèle spécialisé après collecte des propositions | retenu | pas d'entraînement sans données d'usage |
| D14 | Identifiants de code en anglais, documentation en français | retenu | glossaire dans le CLAUDE.md |
| D15 | Base future du shell : KDE Frameworks et KWin ; COSMIC hors sujet | reporté | à rouvrir au moment du shell |
| D16 | X11 pour démarrer | écarté | Wayland et ses portails conviennent mieux à la médiation |
| D17 | Portage Windows | écarté | cible Linux et productivité |
| D18 | Liens typés comme rupture à eux seuls | écarté | jugés incrémentaux ; conservés comme brique |
| D19 | Poche remplaçant le copier-coller | réduit | ne vaut que pour les objets atomiques |
| D20 | SQLite ou base objet embarquée sur le poste | écarté pour la maquette | PGlite gardé si un poste léger devient nécessaire |

## Anti-modèles

Chaque échec passé se traduit en une interdiction de conception.

| Échec | Cause | Ce que la conception s'interdit |
| --- | --- | --- |
| WinFS (Microsoft, abandonné en 2006) | remplacer le système de fichiers, adoption nulle | remplacer le stockage existant au lieu de s'y superposer |
| Bureau sémantique KDE (Nepomuk) | ontologie lourde, annotations manuelles, ressources | ontologie globale complète, saisie manuelle obligatoire |
| OpenDoc | les éditeurs vendent des applications, pas des composants | exiger que les applications changent |
| Ingénierie dirigée par les modèles (MDA) | synchronisation bidirectionnelle modèle et code | plusieurs copies synchronisées d'un même objet |
| Bus de services d'entreprise (ESB) | logique opaque dans le bus | intelligence dans le cœur du bus |
| Programmation orientée aspect | action à distance invisible | un aspect qu'on ne peut pas voir depuis l'objet |
| Bureaux virtuels, groupes, activités manuelles | entretien abandonné | toute organisation qui demande un entretien manuel |
| Agents des années 1990 | incapables de faire le travail | déléguer sans vérification ni arbitrage |
| Microsoft Recall (version initiale) | capture continue, stockage mal protégé | indexer le contenu sans activation explicite ni protection locale |

## Architecture cible

Le poste est autonome (local-first) ; le global fournit la référence et l'échange, pas l'exécution.

> Schéma : architecture cible, univers global et poste (voir la version Claude Docs).

Le moteur d'objets est le cœur : tout le reste passe par son API locale (D-Bus et MCP plus tard).

**Articulation avec le global**

- **Descendant, toujours en lecture** : ontologie de base, identités globales, données des sources de vérité mises en cache avec leurs droits, gabarits et types partagés.
- **Montant, sur décision explicite** : espaces et calques partagés, correspondances.
- **Écriture vers une source de vérité** (ERP, CRM) : jamais par synchronisation, toujours par un verbe explicite, confirmé, via le connecteur.
- **Identité globale référencée, jamais copiée** : un calque ajoute des types et des liens à « client X », il ne crée pas un second client X.
- **Entre univers globaux** : seules des références circulent, sauf transfert explicite et tracé.

## Bus de coordination

Les composants communiquent par un courtier MCP local : chaque composant publie ses capacités typées, tout client (agents, interface, futur shell) les découvre et les appelle au même endroit. D-Bus reste une source à récolter par un adaptateur.

| Couche | Rôle | Nature |
| --- | --- | --- |
| Noyau | registre des capacités (verbe, type d'entrée, type de sortie, effets, réversibilité), routage, validation des schémas, droits par client, confirmation de l'irréversible, journal attribué | déterministe, sans IA |
| Médiateur | traduit entre types via le graphe de conversion ; perte signalée | déterministe d'abord, IA en repli |
| Conseiller | découverte par intention, proposition de plans, routage des modèles, apprentissage des séquences récurrentes | service IA branché sur le bus, ne décide jamais seul |

Le bus fonctionne sans IA. Toute sortie du conseiller est une proposition, soumise aux mêmes règles que le reste. Le tissage des aspects reste interne au moteur : MCP gère mal la diffusion d'événements. Le courtier concentre les privilèges du poste et sera traité comme le composant le plus sensible.

Calendrier : contrat MCP du moteur au lot 1 ; noyau du bus au lot 3 ; médiateur et conseiller après la maquette, nourris par le journal des appels.

## Spec maquette : objectif et hypothèses

La maquette vérifie quatre hypothèses sur un cas réel ; elle ne vise pas un produit. Chacune peut faire tomber le modèle.

| # | Hypothèse | Mesure |
| --- | --- | --- |
| H1 | Les vues structurées s'éditent dans les deux sens sans dérive | nombre d'incohérences entre vues sur le scénario |
| H2 | La réinterprétation de la prose vers le modèle est assez fiable | taux de propositions acceptées, telles quelles ou retouchées |
| H3 | Deux calques sur un même espace restent compréhensibles | divergences justes, fausses alertes, confusion « qui voit quoi » |
| H4 | Types et liens s'infèrent sans entretien manuel | part des liens acceptés sans saisie |

Terrain : un projet Django réel de l'utilisateur, dans un seul espace, avec deux calques (développeur et fonctionnel).

## Périmètre de la maquette

Un espace, deux calques, trois vues, trois aspects, trois opérations IA ; tout le reste est reporté.

**Dans le périmètre**

- **Types d'objets** : Table (lue depuis les modèles Django), Champ, Flux, Exigence, Décision.
- **Vues** : table éditable, schéma Mermaid, spec Markdown. Édition directe des vues structurées ; réinterprétation de la spec par l'IA.
- **Calques** : développeur (tables, champs, contraintes techniques) ; fonctionnel (exigences, règles de gestion, correspondances avec les tables).
- **Aspects** :
  - un changement de champ notifie le calque qui le référence ;
  - une incohérence entre exigence et contrainte est enregistrée comme divergence ;
  - toute modification est attribuée (humain ou agent).
- **Opérations IA** : extraction d'exigences depuis un texte collé ; réinterprétation d'une modification de spec en changements proposés ; proposition de liens entre exigences et tables.
- **Journal des propositions** : entrée, sortie, modèle, décision, correction ; base de mesure et futur jeu d'entraînement.
- **Serveur MCP** sur l'API du moteur, pour tester avec un agent existant.

**Hors périmètre**

Shell de bureau et gestionnaire de fenêtres ; synchronisation et partage d'espaces ; univers global et univers multiples ; adaptateur mail ; ajustement d'un modèle spécialisé ; droits fins ; rosace, poche, barres.

## Modèle de données du moteur (lot 1)

Une table générique d'objets, attributs en JSONB validés par le schéma du type, versions par copie complète. Point de départ à affiner dans Claude Code.

| Entité | Champs principaux | Rôle |
| --- | --- | --- |
| Espace | id, nom, propriétaire, créé_le | périmètre de travail |
| Calque | id, espace, propriétaire, rôle, partagé | lecture d'un espace par un rôle |
| Type | id, nom, parent, schéma JSON, portée (base, espace, calque), version | définition et héritage par prototype |
| Objet | id (UUID stable), espace, type de base, version courante, créé_le | identité |
| Version | id, objet, numéro, attributs JSONB, empreinte SHA-256, auteur, nature (humain, agent), validée, créée_le | historique et attribution |
| Typage | objet, calque, type | typage multiple d'un objet par calque |
| Lien | id, nature, source, cible, calque, version, proposé_par, statut | relations et correspondances |
| Provenance | version, source (objet ou blob), ancre (citation et contexte), opération | d'où vient une version |
| Blob | empreinte SHA-256, type MIME, taille, chemin | contenus volumineux |
| Aspect | id, calque, coupe (type, événement), action, actif | règle greffée |
| Événement | id, objet, version, nature, auteur, horodatage | journal pour le tissage des aspects |
| Divergence | id, espace, objets, calques, description, statut | écart signalé |
| Proposition | id, opération, entrée, sortie, modèle, décision, correction, durée | mesure et apprentissage |
| Embedding | version, modèle, vecteur (pgvector) | recherche par le sens |

Règles d'écriture : toute modification passe par le service du moteur (jamais d'écriture directe en base), produit une version et un événement, puis déclenche les aspects.

## Contrat MCP du moteur

Le contrat est défini avant l'interface web ; l'interface utilise les mêmes services. Première version, à affiner au lot 1.

**Outils (verbes)**

| Outil | Entrée | Sortie | Effet |
| --- | --- | --- | --- |
| `create_object` | espace, type, attributs, calque, provenance | objet, version 1 | écriture |
| `update_object` | objet, version attendue, attributs modifiés, provenance | nouvelle version | écriture ; refus si conflit |
| `link_objects` | nature, source, cible, calque | lien | écriture |
| `set_typing` | objet, calque, type | typage | écriture |
| `search` | texte, espace, calque, mode (nom, sens) | objets classés | lecture |
| `render_view` | objet, gabarit de vue, calque | représentation | lecture |
| `apply_view_edit` | objet, gabarit, modification structurée, version attendue | nouvelle version | écriture |
| `propose` | opération (extraction, réinterprétation, liens), entrée | proposition | aucune écriture d'objet |
| `decide_proposal` | proposition, décision (accepter, modifier, rejeter), correction | objets modifiés ou rien | écriture si acceptée |
| `resolve_divergence` | divergence, résolution | divergence close | écriture |

**Ressources (lecture)**

- `object://{id}` : dernière version, typages, aspects applicables.
- `object://{id}/history` : versions, auteurs, provenance.
- `space://{id}/divergences` : divergences ouvertes.
- `space://{id}/proposals` : propositions en attente.
- `type://{id}` : schéma, parent, traits.

Chaque appel est attribué au client appelant ; les outils d'écriture refusent toute requête sans version attendue sur un objet existant.

## Formats de déclaration

Types, aspects et gabarits de vue sont eux-mêmes des objets, déclarés en JSON et versionnés comme les autres.

**Type**

```json
{
  "name": "Table",
  "parent": "Document",
  "scope": "base",
  "traits": ["Indexable", "Versioned"],
  "schema": {
    "type": "object",
    "required": ["name"],
    "properties": {
      "name": {"type": "string"},
      "fields": {"type": "array", "items": {"$ref": "type://Field"}}
    }
  },
  "merge": {"fields": "by_key:name", "*": "conflict"}
}
```

**Aspect**

```json
{
  "name": "notify-field-change",
  "layer": "fonctionnel",
  "pointcut": {"type": "Field", "event": "updated", "linked_from": "Requirement"},
  "action": {"kind": "notify", "target_layer": "fonctionnel"}
}
```

**Gabarit de vue**

```json
{
  "name": "table-mermaid",
  "applies_to": "Table",
  "kind": "structured",
  "renderer": "mermaid.erDiagram",
  "editable": true
}
```

Les noms de clés suivent le glossaire du CLAUDE.md. Le format de `merge` et de `pointcut` est une première proposition, à valider au lot 1 sur les trois aspects de la maquette.

## Écritures concurrentes et versions

Toute écriture est optimiste : elle porte la version qu'elle a lue, et elle est refusée si l'objet a changé entre-temps.

1. Le client lit l'objet et reçoit son numéro de version.
2. Il envoie sa modification avec ce numéro.
3. Si la version courante est la même, le moteur crée la version suivante, l'événement, puis déclenche les aspects.
4. Sinon, le moteur refuse, renvoie la version courante et ne modifie rien ; le client relit et refait sa modification.

Règles complémentaires :

- aucun verrou long ; aucune écriture sans version attendue sur un objet existant ;
- une version est une copie complète des attributs, avec son empreinte SHA-256, son auteur, sa nature (humain ou agent) et sa provenance ;
- une version produite par un agent porte la proposition d'origine ; elle n'est considérée comme vérité qu'une fois validée ;
- la fusion automatique entre versions concurrentes n'est pas dans la maquette ; le format `merge` des types la prépare pour la synchronisation des espaces.

## Composants et choix techniques

Une seule pile Python, Django et PostgreSQL, sans service supplémentaire à opérer.

| Composant | Choix maquette | Alternative |
| --- | --- | --- |
| Stockage | PostgreSQL (JSONB), sur le poste comme au global | PGlite si un poste léger sans serveur devient nécessaire |
| Moteur d'objets | Django, API interne Django Ninja | Django REST Framework |
| Types | schémas JSON stockés comme objets, validés par jsonschema | Pydantic générés |
| Aspects | règles objets, déclenchées par les signaux Django | déclencheurs PostgreSQL et NOTIFY |
| Tâches de fond | Procrastinate (file sur PostgreSQL) | Celery |
| Agents | Pydantic AI, sorties structurées et validées | LangGraph |
| Modèles | passerelle LiteLLM ; petit modèle local via Ollama | appel direct |
| Embeddings | modèle multilingue local (famille bge-m3) | via la passerelle |
| Index | pgvector et plein texte PostgreSQL (configuration française) | moteur dédié |
| Blobs | répertoire local, fichiers nommés par empreinte SHA-256 | MinIO ou S3 au global |
| Adaptateur code | introspection des modèles Django vers des objets Table ; pygit2 | analyse statique |
| Interface | gabarits Django, htmx, Alpine.js | React |
| Vues | Mermaid.js, Tabulator, Markdown avec aperçu ; diff2html pour les différentiels | éditeurs plus riches |
| Exposition | serveur MCP sur l'API du moteur | — |
| Authentification | comptes Django locaux | OIDC (Entra, Keycloak) |

Trois choix structurants : les aspects restent dans l'application pour ne pas lier le modèle à la base ; les opérations IA sont des fonctions typées qui produisent des objets validés par schéma ; aucun shell de bureau tant que le modèle n'est pas vérifié.

**Stratégie IA** : un petit modèle généraliste à sorties contraintes d'abord ; journal des propositions ; distillation et ajustement (LoRA) ensuite, sur les données réelles. À terme deux ou trois modèles spécialisés : classification (100 à 300 M de paramètres), extraction et traduction de commandes (0,3 à 3 Md), réinterprétation (7 à 14 Md ou passerelle).

## Scénario, critères et découpage

**Scénario de démonstration**

1. Importer les modèles Django du projet : les tables apparaissent avec leur schéma.
2. Coller un mail fonctionnel : exigences extraites, liens proposés vers les tables.
3. Modifier un champ dans la table : schéma mis à jour, divergence signalée côté fonctionnel.
4. Retoucher la spec en prose : changements proposés sur le modèle, validés ou rejetés.
5. Consulter l'historique d'un objet : qui a fait quoi, à partir de quelle source.

**Critères de réussite**

- zéro dérive entre vues structurées sur l'ensemble du scénario ;
- au moins deux tiers des réinterprétations acceptées, telles quelles ou après retouche mineure ;
- aucune divergence manquée sur les cas préparés, peu de fausses alertes ;
- liens proposés acceptés majoritairement sans saisie manuelle.

**Découpage**

- [ ] Lot 1 — Moteur : modèle de données, service d'écriture, versions, provenance, API.
- [ ] Lot 2 — Vues : table, Mermaid, Markdown, édition structurée.
- [ ] Lot 3 — Calques et aspects : deux calques, trois règles, divergences.
- [ ] Lot 4 — IA : extraction, réinterprétation, liens, journal des propositions.
- [ ] Lot 5 — Test : scénario sur le projet réel et mesure des critères.

## Jeu de test

Les critères ne sont mesurables qu'avec des cas préparés à l'avance, dont le résultat attendu est connu.

- **Projet source** : un projet Django réel, d'une dizaine de modèles, avec ses migrations et son historique Git.
- **Textes fonctionnels** : cinq à dix mails ou notes contenant des exigences, dont au moins deux ambiguës et une contradictoire avec le code.
- **Divergences attendues** : au moins cinq cas où un changement technique contredit une exigence, et trois cas sans contradiction (pour mesurer les fausses alertes).
- **Retouches de spec** : dix modifications en prose, de la plus simple (renommer un champ) à la plus floue (« rendre la commande plus souple »), avec la traduction attendue sur le modèle.
- **Liens attendus** : la liste de référence des correspondances exigences et tables, pour comparer aux liens proposés.

Le jeu est versionné dans le dépôt (`tests/fixtures/`) et rejoué à chaque lot.

## Exigences non fonctionnelles

Cibles indicatives pour la maquette, à confirmer sur le poste réel.

| Exigence | Cible |
| --- | --- |
| Écriture d'un objet (version, événement, aspects) | moins de 100 ms |
| Rendu d'une vue structurée | moins de 300 ms |
| Recherche par nom ou par sens | moins de 500 ms |
| Proposition IA par le petit modèle local | moins de 3 s |
| Proposition IA par la passerelle | moins de 15 s, avec indication d'attente |
| Volumétrie de la maquette | quelques milliers d'objets, quelques dizaines de milliers de versions |
| Fonctionnement hors ligne | complet, sauf les opérations routées vers la passerelle |
| Reproductibilité | scénario de test rejouable de bout en bout par une commande |

## Questions ouvertes et suite

- Indexation des sources d'entreprise : index global filtré par droits, index local, ou mixte.
- Serveur des espaces partagés : relais local-first (CRDT) ou serveur de dépôts façon Git.
- Modèle de versions : copie complète (maquette) ou faits immuables à la Datomic (provenance plus fine).
- Fusion typée : quelles fonctions de fusion par type de base.
- Gabarits de vue : format de déclaration et partage.
- Shell de bureau : KWin ou compositeur basé sur Smithay, une fois le modèle vérifié.
- Liste des verbes universels (sept ou huit), à fixer au moment du shell.

**Sécurité (lot 2)** : orientation à approfondir, cohérence au niveau de l'espace, avec possibilité de restreindre l'accès au niveau d'un objet ou d'un attribut lors du partage. Le contenu des sources est non fiable pour les agents.

**Langue du code** : identifiants en anglais selon le glossaire du CLAUDE.md, documentation en français.

**Suite** : reprendre ce document dans Claude Code, commencer par le lot 1 (modèle de données et service d'écriture), avec tests dès le départ. Une fois les hypothèses vérifiées, la phase suivante porte sur l'interaction de l'utilisateur avec l'information, qui reste le problème de fond.
