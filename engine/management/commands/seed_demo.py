from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from engine.models import Layer, Object, ObjectType, Space, ViewTemplate
from engine.services.create import create_object
from ui.demo import (
    DEMO_LAYER_ROLE,
    DEMO_LAYER_ROLE_FONCTIONNEL,
    DEMO_SECOND_TYPE_NAME,
    DEMO_SPACE_NAME,
    DEMO_TABLE_OBJECT_NAME,
    DEMO_TABLE_TYPE_NAME,
    DEMO_TYPE_NAME,
    DEMO_USERNAME,
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
        exigence_type, exigence_type_created = ObjectType.objects.get_or_create(
            name=DEMO_SECOND_TYPE_NAME,
            scope=ObjectType.Scope.BASE,
            defaults={"schema": {"type": "object", "properties": {"name": {"type": "string"}}}},
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
            )
            if was_created
        ]
        if created:
            self.stdout.write(self.style.SUCCESS(f"Créé : {', '.join(created)}."))
        else:
            self.stdout.write("Déjà en place, rien à faire.")
