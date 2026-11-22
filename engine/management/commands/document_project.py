from django.core.management.base import BaseCommand

from engine.models import Object, ObjectType, Proposal
from engine.services.create import create_object
from engine.services.link import link_objects
from engine.services.propose import record_proposal
from ui.demo import DEMO_DECISION_TYPE_NAME, DEMO_USE_CASE_TYPE_NAME, demo_context

ARCHITECT_USE_CASE_NAME = "Architecte produit (vision desktop)"

# Décisions réelles, actées en conversation avec l'utilisateur — pas une fixture
# synthétique. Liste qui grossit au fil des sessions ; idempotente par nom.
DECISIONS = [
    {
        "name": "B10 reformulé : classement par activité, IA en rattrapage",
        "justification": (
            "Le lot 4 a montré que la proposition de liens par un petit modèle "
            "local est peu discriminante (une exigence liée à quasiment toutes "
            "les tables candidates, confiance 0.7-1.0). Le classement par défaut "
            "doit venir de l'activité elle-même (espace, geste de dépôt ou de "
            "lien explicite) ; l'IA reste utile, mais en rattrapage, pas comme "
            "voie principale."
        ),
    },
    {
        "name": "Trois axes de classement orthogonaux, jamais imbriqués",
        "justification": (
            "Space répond à « qui a le droit de voir ça » (accès), ObjectType à "
            "« qu'est-ce que c'est structurellement » (essence, seule hiérarchie "
            "is-a légitime), Dossier à « pourquoi je m'y intéresse maintenant » "
            "(intention, multi-valué). Aucune UI ne doit permettre d'imbriquer "
            "l'un dans l'autre (ex. glisser un Space dans un Dossier) — ça "
            "réintroduirait en douce la hiérarchie unique que le projet existe "
            "pour éviter."
        ),
    },
    {
        "name": "Space : réplication + filtre comportemental + périmètre d'activité, pas RWX",
        "justification": (
            "Space ne donne pas un accès binaire (RWX) : c'est une politique "
            "déclarative de comportement des objets face à l'extérieur "
            "(anonymisation, criticité, obligations légales), appliquée par le "
            "noyau du bus — jamais du code métier par espace (sinon on "
            "réinvente l'anti-modèle ESB avec Space à la place du bus). "
            "Partager un projet entre espaces ne duplique jamais l'identité : "
            "une référence traverse la frontière, synchronisée par événements "
            "tracés — cohérent avec « identité référencée, jamais copiée » déjà "
            "écrit pour l'univers global, ici appliqué un niveau plus bas "
            "(entre deux espaces locaux). Sécurité par plugin selon la "
            "criticité/le cadre légal : direction actée, pas construite."
        ),
    },
    {
        "name": "Dossier dynamique : appartenance calculée, pas posée par un Link",
        "justification": (
            "Même type Dossier, attribut facultatif `query` (égalité sur des "
            "champs de Version) — l'appartenance est calculée à l'affichage, "
            "pas un Link explicite. Reprend un précédent établi (Smart Folders "
            "macOS, Smart Collections Lightroom), pas une invention : concilie "
            "B1 (retrouver par le sens) et le confort du dossier familier. "
            "Vérifié en réel dans les deux sens sur « En attente de validation » "
            "(query: validated=false) : un objet créé par l'agent y apparaît, "
            "puis en sort sans toucher à un Link quand un humain le réenregistre "
            "(update_object positionne validated=true de lui-même) — déplacer un "
            "objet d'un dossier dynamique, c'est changer l'attribut, rien de plus."
        ),
    },
    {
        "name": "Hiérarchie de Dossier pour la navigation seulement",
        "justification": (
            "Même recette que le classement : un Link de plus (nature "
            "`sous-dossier-de`), pas un nouveau mécanisme. L'appartenance reste "
            "inchangée — un dossier parent purement navigationnel (« Vues ») ne "
            "contient rien en propre, c'est volontaire (précédent Lightroom : "
            "Collection Set regroupe des Collections sans rien posséder). Évite "
            "de faire porter ce rôle par Space, qui en a déjà trois (réplication, "
            "filtre comportemental, périmètre d'activité) — pas un quatrième."
        ),
    },
    {
        "name": "Menu radial remplacé par menu contextuel (prompt + liste)",
        "justification": (
            "Essayé pour de vrai dans le prototype desktop, pas sur supposition : "
            "le radial n'est pas plus clair qu'une liste, malgré une mécanique qui "
            "fonctionne. Remplacé par un pattern déjà éprouvé ailleurs (command "
            "palette : VS Code, Notion, Linear, Raycast) — prompt en haut qui "
            "filtre, commandes principales dessous — cohérent avec le prompt déjà "
            "posé en barre du bas. Un seul composant (CommandMenu) réutilisé pour "
            "les objets, les espaces, et les sous-menus (ex. « Classer dans… »)."
        ),
    },
    {
        "name": "Barre latérale = contexte, barre du bas = verbes",
        "justification": (
            "Objets/Liens/Bus ne sont ni un contexte (espace) ni un verbe sur un "
            "objet : ce sont des outils système (catalogues globaux). Déplacés en "
            "bas de la barre latérale (avec un Paramètres à venir), pas dans le "
            "dock de la barre du bas. Historique n'est dans aucune des deux "
            "listes : pas une destination fixe, il s'ouvre tout seul quand une "
            "commande l'invoque sur un objet précis, se ferme avec son propre "
            "bouton. Barre du bas = prompt seul pour l'instant, futurs widgets "
            "d'info/action ponctuels, pas les outils système lourds."
        ),
    },
    {
        "name": "Système est un espace de plus, pas une section à part",
        "justification": (
            "Affine la décision précédente : plutôt qu'une section d'icônes "
            "codée en dur pour Objets/Liens/Bus/Paramètres, Système rejoint la "
            "liste des espaces (sans activité, sans sélection, sans dossier), "
            "et ses fonctions passent par le même menu clic-droit (CommandMenu) "
            "que n'importe quel espace. Un seul pattern pour tout (« espace + "
            "menu contextuel »), pas deux à maintenir en parallèle."
        ),
    },
]

# Prototypes d'interaction réels (voir prototypes/), jetables côté code mais
# suivis ici comme de vrais Cas d'usage — liste à compléter au fil des
# prototypes construits.
PROTOTYPES = [
    {
        "name": "Prototype — bande d'espaces",
        "persona": "architecte produit",
        "description": (
            "prototypes/space-switcher (Svelte + Vite), jetable, données "
            "bidon, pas branché sur le vrai moteur. Teste le geste : bande "
            "persistante plutôt qu'un menu radial pour l'accès aux espaces "
            "(« toujours accessible » et « sélection rapide d'un verbe » sont "
            "deux besoins différents, pas le même widget)."
        ),
        "steps": [
            {"from": "utilisateur", "to": "bande", "message": "clique une bulle d'espace"},
            {"from": "bande", "to": "contenu", "message": "affiche les objets de l'espace actif"},
            {"from": "utilisateur", "to": "objet", "message": "glisse un objet"},
            {"from": "objet", "to": "bande", "message": "dépose sur une autre bulle"},
            {"from": "bande", "to": "objet", "message": "déplace l'objet vers cet espace"},
        ],
    },
    {
        "name": "Prototype — fenêtrage glissable",
        "persona": "architecte produit",
        "description": (
            "prototypes/windowing (Svelte + Vite), jetable, données bidon, pas "
            "branché sur le vrai moteur. Teste le geste : fenêtres "
            "déplaçables/redimensionnables, et Objets/Liens/Bus (pages Django "
            "réelles) rouvertes comme des fenêtres séparées plutôt que des "
            "pages qu'on quitte pour y aller — première application concrète "
            "de B9 (comparer sans basculer)."
        ),
        "steps": [
            {"from": "utilisateur", "to": "barre-titre", "message": "glisse pour déplacer la fenêtre"},
            {"from": "utilisateur", "to": "coin", "message": "glisse pour redimensionner"},
            {"from": "utilisateur", "to": "dock", "message": "clique Objets/Liens/Bus"},
            {"from": "dock", "to": "fenetre", "message": "ouvre ou ferme la fenêtre correspondante"},
        ],
    },
    {
        "name": "Prototype — fusion bande d'espaces + fenêtrage",
        "persona": "architecte produit",
        "description": (
            "prototypes/desktop (Svelte + Vite), jetable, données bidon, pas "
            "branché sur le vrai moteur. Fusionne les deux prototypes "
            "précédents plutôt que d'en ajouter un : voir les gestes "
            "ensemble, pas isolés. Le contenu de la fenêtre Objets dépend de "
            "l'espace actif ; glisser une carte depuis cette fenêtre sur une "
            "bulle d'espace la déplace, dans le même écran que le fenêtrage "
            "accrochable (4 coins)."
        ),
        "steps": [
            {"from": "utilisateur", "to": "bande", "message": "change d'espace actif"},
            {"from": "fenetre-objets", "to": "bande", "message": "montre les objets de cet espace"},
            {"from": "utilisateur", "to": "carte-objet", "message": "glisse depuis la fenêtre Objets"},
            {"from": "carte-objet", "to": "bande", "message": "dépose sur une autre bulle"},
            {"from": "utilisateur", "to": "fenetre", "message": "déplace/redimensionne/accroche"},
        ],
    },
    {
        "name": "Prototype — menu radial des verbes",
        "persona": "architecte produit",
        "description": (
            "Ajouté au prototype fusionné (prototypes/desktop), pas un "
            "nouveau projet — le geste s'exerce naturellement sur les objets "
            "déjà présents. Sept verbes universels (Voir, Modifier, Lier, "
            "Classer, Typer, Décider, Historique) — la taille où un radial "
            "reste lisible (spec : « sept ou huit »). Pas de « créer » : on "
            "agit sur un objet déjà là, pas sur du vide."
        ),
        "steps": [
            {"from": "utilisateur", "to": "carte-objet", "message": "clic droit"},
            {"from": "carte-objet", "to": "menu-radial", "message": "ouvre centré sur le curseur"},
            {"from": "utilisateur", "to": "tranche", "message": "clique un verbe, ou Échap pour annuler"},
            {"from": "menu-radial", "to": "toast", "message": "confirme l'action choisie"},
        ],
    },
    {
        "name": "Prototype — dossiers épinglés interactifs",
        "persona": "architecte produit",
        "description": (
            "Ajouté au prototype fusionné (prototypes/desktop). Les badges "
            "de dossier épinglés étaient inertes (initiale + tooltip). "
            "Classification réellement multi-valuée (un objet porte "
            "plusieurs dossierIds, comme le vrai Link de classification), "
            "clic sur un badge pour ouvrir son contenu réel, glisser-déposer "
            "une carte sur un badge comme second geste possible — la même "
            "alternative menu/glisser déjà établie pour déplacer un objet "
            "vers un espace."
        ),
        "steps": [
            {"from": "utilisateur", "to": "carte-objet", "message": "clic droit → Classer dans…"},
            {"from": "menu", "to": "objet", "message": "ajoute le dossier choisi (multi-valué)"},
            {"from": "utilisateur", "to": "badge-dossier", "message": "clique"},
            {"from": "badge-dossier", "to": "fenetre-dossier", "message": "liste les objets classés dedans"},
            {"from": "utilisateur", "to": "carte-objet", "message": "glisse vers un badge-dossier"},
            {"from": "badge-dossier", "to": "objet", "message": "classe par dépôt, sans passer par le menu"},
        ],
    },
    {
        "name": "Prototype — barre « ?/! » et gestionnaire de fichiers double panneau",
        "persona": "architecte produit",
        "description": (
            "Ajouté au prototype fusionné (prototypes/desktop), décidé en "
            "une seule fois : la barre du bas distingue désormais « ? » "
            "(prompt IA, mode par défaut) et « ! » (commande directe, type "
            "cp/ren) — même distinction que dans CommandMenu, portée là où "
            "elle manquait, avec un seul espace de retour au-dessus de la "
            "barre pour les deux. Le gestionnaire de fichiers (Système → "
            "Fichiers) reprend le modèle Norton/Total Commander : un vrai "
            "double panneau à diviseur interne glissable, pas deux fenêtres "
            "indépendantes qui pourraient se désassortir — chaque panneau "
            "choisit son dossier via son en-tête, glisser une carte d'un "
            "panneau vers l'autre classe l'objet dans le dossier affiché en "
            "face."
        ),
        "steps": [
            {"from": "utilisateur", "to": "barre-du-bas", "message": "tape « ? » ou rien → question IA"},
            {"from": "utilisateur", "to": "barre-du-bas", "message": "tape « ! commande » → commande directe"},
            {"from": "barre-du-bas", "to": "zone-retour", "message": "affiche la réponse au-dessus de la barre"},
            {"from": "utilisateur", "to": "panneau-gauche", "message": "choisit un dossier dans l'en-tête"},
            {"from": "utilisateur", "to": "carte-objet", "message": "glisse du panneau gauche vers le droit"},
            {"from": "panneau-droit", "to": "objet", "message": "classe dans le dossier affiché à droite"},
        ],
    },
]

# Points relevés, pas encore tranchés — Proposal sans sortie IA (voir
# engine/services/propose.py::record_proposal), le même mécanisme que pour les
# observations UI déjà capturées.
OBSERVATIONS = [
    (
        "pari non prouvé : proximité d'activité vs IA",
        "On a choisi (B10) que l'activité produirait un meilleur signal de "
        "classement que l'IA. Mais Notion/Obsidian/Lightroom ont le même "
        "problème documenté : les utilisateurs lient les deux premières "
        "semaines puis arrêtent (cimetière de notes orphelines). Rien ne "
        "prouve encore que notre pari vaille mieux que celui qu'on vient "
        "d'écarter.",
    ),
    (
        "partage entre espaces jamais stress-testé",
        "Tout a été testé en mono-utilisateur, mono-espace. B11/B12 parlent de "
        "partage, mais le cas à plusieurs personnes/espaces (répliques, "
        "conflits, qui voit quoi) n'a jamais été exercé — c'est généralement "
        "là que ce genre de modèle casse.",
    ),
    (
        "risque sur la thèse du projet, pas sur son exécution",
        "Le moteur prouve de bonnes propriétés (identité, versions, "
        "provenance), mais le vrai problème de fond (150 bascules par jour) "
        "n'est résolu que par la couche d'interaction, toujours repoussée et "
        "encore nébuleuse dans nos échanges. Le substrat pourrait être "
        "parfait et l'objectif réel rester non atteint si l'interaction "
        "s'avère plus dure que prévu.",
    ),
]


class Command(BaseCommand):
    help = (
        "Documente ce projet-ci avec de vrais objets Décision, Cas d'usage et "
        "observations (persona « Architecte produit (vision desktop) »), pas "
        "une fixture synthétique — voir docs/spec.md (B10) et le glossaire du "
        "CLAUDE.md. Liste à compléter au fil des sessions de conception."
    )

    def handle(self, *args, **options):
        space, layer, document_type, user = demo_context()
        decision_type = ObjectType.objects.get(name=DEMO_DECISION_TYPE_NAME, scope=ObjectType.Scope.BASE)
        use_case_type = ObjectType.objects.get(name=DEMO_USE_CASE_TYPE_NAME, scope=ObjectType.Scope.BASE)

        architecte = Object.objects.get(
            space=space, base_type=use_case_type, current_version__attributes__name=ARCHITECT_USE_CASE_NAME
        )

        decisions_created, links_created = [], 0
        for decision_data in DECISIONS:
            decision = Object.objects.filter(
                space=space, base_type=decision_type, current_version__attributes__name=decision_data["name"]
            ).first()
            if decision is None:
                decision = create_object(
                    space,
                    decision_type,
                    {"name": decision_data["name"], "justification": decision_data["justification"], "statut": "actée"},
                    author=user,
                )
                decisions_created.append(decision_data["name"])
            if not architecte.links_from.filter(nature="a-produit", target=decision).exists():
                link_objects("a-produit", architecte, decision, author=user)
                links_created += 1

        prototypes_created = []
        for prototype in PROTOTYPES:
            use_case = Object.objects.filter(
                space=space, base_type=use_case_type, current_version__attributes__name=prototype["name"]
            ).first()
            if use_case is None:
                use_case = create_object(
                    space,
                    use_case_type,
                    {
                        "name": prototype["name"],
                        "persona": prototype["persona"],
                        "description": prototype["description"],
                        "steps": prototype["steps"],
                    },
                    author=user,
                )
                prototypes_created.append(prototype["name"])
            if not use_case.links_from.filter(nature="derive-de", target=architecte).exists():
                link_objects("derive-de", use_case, architecte, author=user)

        observations_created = []
        for title, text in OBSERVATIONS:
            if not Proposal.objects.filter(operation="observation", input__text=text).exists():
                record_proposal("observation", {"text": text})
                observations_created.append(title)

        created = [
            name
            for name, was_created in (
                (f"décisions : {', '.join(decisions_created)}" if decisions_created else "", bool(decisions_created)),
                (f"liens architecte → décision ({links_created})" if links_created else "", bool(links_created)),
                (
                    f"prototypes : {', '.join(prototypes_created)}" if prototypes_created else "",
                    bool(prototypes_created),
                ),
                (
                    f"observations : {', '.join(observations_created)}" if observations_created else "",
                    bool(observations_created),
                ),
            )
            if was_created
        ]
        if created:
            self.stdout.write(self.style.SUCCESS(f"Créé : {' | '.join(created)}."))
        else:
            self.stdout.write("Déjà en place, rien à faire.")
