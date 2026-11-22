from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from engine.models import Aspect, Layer, Link, Object, ObjectType, Space, ViewTemplate
from engine.services.create import create_object
from engine.services.link import link_objects
from ui.demo import (
    DEMO_DECISION_TYPE_NAME,
    DEMO_EXIGENCE_OBJECT_NAME,
    DEMO_FOLDER_OBJECT_NAME,
    DEMO_FOLDER_TYPE_NAME,
    DEMO_LAYER_ROLE,
    DEMO_LAYER_ROLE_FONCTIONNEL,
    DEMO_SECOND_TYPE_NAME,
    DEMO_SPACE_NAME,
    DEMO_TABLE_OBJECT_NAME,
    DEMO_TABLE_TYPE_NAME,
    DEMO_TYPE_NAME,
    DEMO_USE_CASE_TYPE_NAME,
    DEMO_USERNAME,
    FOLDER_LINK_NATURE,
    USE_CASE_SEQUENCE_VIEW_NAME,
)


class Command(BaseCommand):
    help = "Amorce l'espace, le calque, l'utilisateur et le type de démo du harnais de test."

    def handle(self, *args, **options):
        user, user_created = User.objects.get_or_create(username=DEMO_USERNAME)
        space, space_created = Space.objects.get_or_create(name=DEMO_SPACE_NAME, defaults={"owner": user})
        layer, layer_created = Layer.objects.get_or_create(
            space=space, role=DEMO_LAYER_ROLE, defaults={"owner": user}
        )
        layer_fonctionnel, layer_fonctionnel_created = Layer.objects.get_or_create(
            space=space, role=DEMO_LAYER_ROLE_FONCTIONNEL, defaults={"owner": user}
        )
        document_type, type_created = ObjectType.objects.get_or_create(
            name=DEMO_TYPE_NAME,
            scope=ObjectType.Scope.BASE,
            defaults={
                "schema": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "mime_type": {"type": "string"},
                        "size": {"type": "integer"},
                    },
                }
            },
        )
        # update_or_create (pas get_or_create) : le schéma d'Exigence a évolué (lot 3
        # ajoute field/rule) et doit se mettre à jour en rejouant la commande.
        exigence_type, exigence_type_created = ObjectType.objects.update_or_create(
            name=DEMO_SECOND_TYPE_NAME,
            scope=ObjectType.Scope.BASE,
            defaults={
                "schema": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "field": {"type": "string"},
                        "rule": {"type": "string", "enum": ["obligatoire", "facultatif"]},
                    },
                }
            },
        )
        table_type, table_type_created = ObjectType.objects.get_or_create(
            name=DEMO_TABLE_TYPE_NAME,
            scope=ObjectType.Scope.BASE,
            defaults={
                "schema": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "fields": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["name", "type"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "nullable": {"type": "boolean"},
                                },
                            },
                        },
                    },
                }
            },
        )

        view_templates = [
            ("table-grid", ViewTemplate.Kind.STRUCTURED, "table", True),
            ("table-mermaid", ViewTemplate.Kind.STRUCTURED, "mermaid.erDiagram", True),
            ("table-spec", ViewTemplate.Kind.NARRATIVE, "markdown", False),
        ]
        view_templates_created = False
        for vt_name, kind, renderer, editable in view_templates:
            _, created_flag = ViewTemplate.objects.get_or_create(
                name=vt_name,
                applies_to=table_type,
                defaults={"kind": kind, "renderer": renderer, "editable": editable},
            )
            view_templates_created = view_templates_created or created_flag

        commande_created = False
        if not Object.objects.filter(
            space=space, base_type=table_type, current_version__attributes__name=DEMO_TABLE_OBJECT_NAME
        ).exists():
            create_object(
                space,
                table_type,
                {
                    "name": DEMO_TABLE_OBJECT_NAME,
                    "fields": [
                        {"name": "id", "type": "uuid", "nullable": False},
                        {"name": "delai", "type": "integer", "nullable": False},
                    ],
                },
                author=user,
            )
            commande_created = True

        commande = Object.objects.get(
            space=space, base_type=table_type, current_version__attributes__name=DEMO_TABLE_OBJECT_NAME
        )

        aspects = [
            (
                "notify-field-change",
                {"type": "Table", "event": "updated", "linked_from": "Exigence"},
                {"kind": "notify", "target_layer": DEMO_LAYER_ROLE_FONCTIONNEL},
            ),
            (
                "exigence-contrainte-divergence",
                {"type": ["Table", "Exigence"]},
                {"kind": "check_constraint"},
            ),
        ]
        aspects_created = False
        for aspect_name, pointcut, action in aspects:
            _, created_flag = Aspect.objects.get_or_create(
                name=aspect_name,
                layer=layer_fonctionnel,
                defaults={"pointcut": pointcut, "action": action, "active": True},
            )
            aspects_created = aspects_created or created_flag

        exigence_created = False
        if not Object.objects.filter(
            space=space, base_type=exigence_type, current_version__attributes__name=DEMO_EXIGENCE_OBJECT_NAME
        ).exists():
            exigence = create_object(
                space,
                exigence_type,
                {"name": DEMO_EXIGENCE_OBJECT_NAME, "field": "delai", "rule": "obligatoire"},
                author=user,
            )
            link_objects("correspondence", exigence, commande, layer=layer_fonctionnel, author=user)
            exigence_created = True

        exigence = Object.objects.get(
            space=space, base_type=exigence_type, current_version__attributes__name=DEMO_EXIGENCE_OBJECT_NAME
        )

        # Dossier : classement multi-valué (Object + Link), pas un sous-espace — voir
        # CLAUDE.md (glossaire) et docs/spec.md (B10).
        folder_type, folder_type_created = ObjectType.objects.get_or_create(
            name=DEMO_FOLDER_TYPE_NAME,
            scope=ObjectType.Scope.BASE,
            defaults={"schema": {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}},
        )

        folder_created = False
        if not Object.objects.filter(
            space=space, base_type=folder_type, current_version__attributes__name=DEMO_FOLDER_OBJECT_NAME
        ).exists():
            create_object(space, folder_type, {"name": DEMO_FOLDER_OBJECT_NAME}, author=user)
            folder_created = True

        folder = Object.objects.get(
            space=space, base_type=folder_type, current_version__attributes__name=DEMO_FOLDER_OBJECT_NAME
        )

        classification_created = False
        for classified in (commande, exigence):
            if not Link.objects.filter(source=classified, target=folder, nature=FOLDER_LINK_NATURE).exists():
                link_objects(FOLDER_LINK_NATURE, classified, folder, author=user)
                classification_created = True

        # Décision et Cas d'usage : deux types du périmètre jamais instanciés avant
        # la discussion sur le persona « Architecte produit » (voir document_project).
        decision_type, decision_type_created = ObjectType.objects.get_or_create(
            name=DEMO_DECISION_TYPE_NAME,
            scope=ObjectType.Scope.BASE,
            defaults={
                "schema": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "justification": {"type": "string"},
                        "statut": {"type": "string"},
                    },
                }
            },
        )

        use_case_type, use_case_type_created = ObjectType.objects.get_or_create(
            name=DEMO_USE_CASE_TYPE_NAME,
            scope=ObjectType.Scope.BASE,
            defaults={
                "schema": {
                    "type": "object",
                    "required": ["name", "steps"],
                    "properties": {
                        "name": {"type": "string"},
                        "persona": {"type": "string"},
                        "description": {"type": "string"},
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["from", "to", "message"],
                                "properties": {
                                    "from": {"type": "string"},
                                    "to": {"type": "string"},
                                    "message": {"type": "string"},
                                },
                            },
                        },
                    },
                }
            },
        )

        _, use_case_view_created = ViewTemplate.objects.get_or_create(
            name=USE_CASE_SEQUENCE_VIEW_NAME,
            applies_to=use_case_type,
            defaults={"kind": ViewTemplate.Kind.STRUCTURED, "renderer": "mermaid.sequenceDiagram", "editable": False},
        )

        created = [
            name
            for name, was_created in (
                ("utilisateur demo", user_created),
                ("espace démo", space_created),
                ("calque développeur", layer_created),
                ("calque fonctionnel", layer_fonctionnel_created),
                ("type Document", type_created),
                ("type Exigence", exigence_type_created),
                ("type Table", table_type_created),
                ("gabarits de vue", view_templates_created),
                ("table commande", commande_created),
                ("aspects", aspects_created),
                ("exigence délai obligatoire", exigence_created),
                ("type Dossier", folder_type_created),
                ("dossier de démo", folder_created),
                ("classement dans le dossier", classification_created),
                ("type Décision", decision_type_created),
                ("type Cas d'usage", use_case_type_created),
                ("gabarit cas-usage-sequence", use_case_view_created),
            )
            if was_created
        ]
        if created:
            self.stdout.write(self.style.SUCCESS(f"Créé : {', '.join(created)}."))
        else:
            self.stdout.write("Déjà en place, rien à faire.")
