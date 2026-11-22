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
