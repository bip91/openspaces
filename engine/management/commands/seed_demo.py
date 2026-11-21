from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from engine.models import Layer, ObjectType, Space
from ui.demo import DEMO_LAYER_ROLE, DEMO_SPACE_NAME, DEMO_TYPE_NAME, DEMO_USERNAME


class Command(BaseCommand):
    help = "Amorce l'espace, le calque, l'utilisateur et le type de démo du harnais de test."

    def handle(self, *args, **options):
        user, user_created = User.objects.get_or_create(username=DEMO_USERNAME)
        space, space_created = Space.objects.get_or_create(name=DEMO_SPACE_NAME, defaults={"owner": user})
        layer, layer_created = Layer.objects.get_or_create(
            space=space, role=DEMO_LAYER_ROLE, defaults={"owner": user}
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

        created = [
            name
            for name, was_created in (
                ("utilisateur demo", user_created),
                ("espace démo", space_created),
                ("calque développeur", layer_created),
                ("type Document", type_created),
            )
            if was_created
        ]
        if created:
            self.stdout.write(self.style.SUCCESS(f"Créé : {', '.join(created)}."))
        else:
            self.stdout.write("Déjà en place, rien à faire.")
