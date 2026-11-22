from django.core.management.base import BaseCommand

from engine.models import Object, ObjectType
from engine.services.create import create_object
from engine.services.link import link_objects
from ui.demo import DEMO_DECISION_TYPE_NAME, DEMO_USE_CASE_TYPE_NAME, demo_context

DECISION_B10_NAME = "B10 reformulé : classement par activité, IA en rattrapage"

USE_CASES = [
    {
        "name": "Architecte produit (vision desktop)",
        "persona": "architecte produit",
        "description": (
            "Le travail de conception de ce projet lui-même : une idée se "
            "reformule en concept, dérive en cas d'usage, puis en exigence, "
            "puis en spec et en code."
        ),
        "steps": [
            {"from": "architecte", "to": "agent", "message": "propose une idée"},
            {"from": "agent", "to": "concept", "message": "reformule en concept"},
            {"from": "concept", "to": "cas-usage", "message": "dérive en cas d'usage"},
            {"from": "cas-usage", "to": "exigence", "message": "dérive en exigence"},
            {"from": "exigence", "to": "spec-code", "message": "dérive en spec et en code"},
        ],
    },
    {
        "name": "ADV / assistante administrative",
        "persona": "ADV",
        "description": (
            "Un dossier client qui s'accumule dans le temps, pas un projet "
            "ponctuel : devis, bon de commande, relances."
        ),
        "steps": [
            {"from": "client", "to": "adv", "message": "demande un devis"},
            {"from": "adv", "to": "client", "message": "envoie le devis"},
            {"from": "client", "to": "adv", "message": "valide, passe commande"},
            {"from": "adv", "to": "dossier-client", "message": "classe la commande"},
        ],
    },
    {
        "name": "Architecture SI",
        "persona": "architecte SI",
        "description": (
            "Cartographie des systèmes et décisions d'architecture tracées, "
            "contraignant les composants concernés."
        ),
        "steps": [
            {"from": "architecte-si", "to": "contrainte", "message": "identifie une contrainte"},
            {"from": "architecte-si", "to": "decision", "message": "trace une décision"},
            {"from": "decision", "to": "composant", "message": "contraint le composant"},
        ],
    },
    {
        "name": "Directeur",
        "persona": "directeur",
        "description": (
            "Agrège des chiffres venus de plusieurs tableurs pour produire un "
            "rapport récurrent sur l'évolution du service."
        ),
        "steps": [
            {"from": "responsables", "to": "directeur", "message": "envoient leurs tableurs"},
            {"from": "directeur", "to": "rapport", "message": "agrège les chiffres"},
            {"from": "rapport", "to": "comite", "message": "présente l'évolution du service"},
        ],
    },
]


class Command(BaseCommand):
    help = (
        "Documente ce projet-ci avec de vrais objets Décision et Cas d'usage "
        "(persona « Architecte produit (vision desktop) »), pas une fixture "
        "synthétique — voir docs/spec.md (B10) et le glossaire du CLAUDE.md."
    )

    def handle(self, *args, **options):
        space, layer, document_type, user = demo_context()
        decision_type = ObjectType.objects.get(name=DEMO_DECISION_TYPE_NAME, scope=ObjectType.Scope.BASE)
        use_case_type = ObjectType.objects.get(name=DEMO_USE_CASE_TYPE_NAME, scope=ObjectType.Scope.BASE)

        decision_created = False
        if not Object.objects.filter(
            space=space, base_type=decision_type, current_version__attributes__name=DECISION_B10_NAME
        ).exists():
            create_object(
                space,
                decision_type,
                {
                    "name": DECISION_B10_NAME,
                    "justification": (
                        "Le lot 4 a montré que la proposition de liens par un petit "
                        "modèle local est peu discriminante (une exigence liée à "
                        "quasiment toutes les tables candidates, confiance 0.7-1.0). "
                        "Le classement par défaut doit venir de l'activité elle-même "
                        "(espace, geste de dépôt ou de lien explicite) ; l'IA reste "
                        "utile, mais en rattrapage, pas comme voie principale."
                    ),
                    "statut": "actée",
                },
                author=user,
            )
            decision_created = True
        decision = Object.objects.get(
            space=space, base_type=decision_type, current_version__attributes__name=DECISION_B10_NAME
        )

        use_cases_created = []
        for use_case in USE_CASES:
            if not Object.objects.filter(
                space=space, base_type=use_case_type, current_version__attributes__name=use_case["name"]
            ).exists():
                create_object(
                    space,
                    use_case_type,
                    {
                        "name": use_case["name"],
                        "persona": use_case["persona"],
                        "description": use_case["description"],
                        "steps": use_case["steps"],
                    },
                    author=user,
                )
                use_cases_created.append(use_case["name"])

        architecte = Object.objects.get(
            space=space,
            base_type=use_case_type,
            current_version__attributes__name="Architecte produit (vision desktop)",
        )
        link_created = False
        if not architecte.links_from.filter(nature="a-produit", target=decision).exists():
            link_objects("a-produit", architecte, decision, author=user)
            link_created = True

        created = [
            name
            for name, was_created in (
                ("décision B10", decision_created),
                (f"cas d'usage : {', '.join(use_cases_created)}" if use_cases_created else "", bool(use_cases_created)),
                ("lien architecte → décision", link_created),
            )
            if was_created
        ]
        if created:
            self.stdout.write(self.style.SUCCESS(f"Créé : {', '.join(created)}."))
        else:
            self.stdout.write("Déjà en place, rien à faire.")
