from django.apps import apps
from django.core.management.base import BaseCommand

from adapters.django.introspect import table_attributes
from engine.models import Object, ObjectType
from engine.services.create import create_object
from engine.services.update import update_object as update_object_service
from ui.demo import DEMO_TABLE_TYPE_NAME, demo_context


class Command(BaseCommand):
    help = (
        "Introspecte les modèles Django de l'app engine et pousse un objet Table "
        "par modèle, avec son schéma de champs (lot 5, étape 1 du scénario : "
        "« importer les modèles Django du projet, les tables apparaissent avec "
        "leur schéma »)."
    )

    def handle(self, *args, **options):
        space, layer, document_type, user = demo_context()
        table_type = ObjectType.objects.get(name=DEMO_TABLE_TYPE_NAME, scope=ObjectType.Scope.BASE)

        created, updated, unchanged = [], [], []
        for model in apps.get_app_config("engine").get_models():
            attributes = table_attributes(model)
            provenance = {"operation": "import-django-models"}

            existing = (
                Object.objects.filter(
                    space=space, base_type=table_type, current_version__attributes__name=attributes["name"]
                )
                .select_related("current_version")
                .first()
            )

            if existing and existing.current_version.attributes == attributes:
                unchanged.append(attributes["name"])
            elif existing:
                update_object_service(
                    existing.id, existing.current_version.number, attributes, author=user, provenance=provenance
                )
                updated.append(attributes["name"])
            else:
                create_object(space, table_type, attributes, author=user, provenance=provenance)
                created.append(attributes["name"])

        self.stdout.write(
            self.style.SUCCESS(f"{len(created)} créées, {len(updated)} mises à jour, {len(unchanged)} inchangées.")
        )
