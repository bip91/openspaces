from django.core.management.base import BaseCommand

from bus.core import call
from bus.models import CallLog
from engine.models import ObjectType
from ui.demo import DEMO_TABLE_TYPE_NAME, demo_context


class Command(BaseCommand):
    help = (
        "Démontre le noyau du bus (lot 3) sur l'espace de démo : un appel "
        "autorisé, un refus de droits, un refus de verbe inconnu — puis "
        "affiche le journal attribué (CallLog) qui en résulte."
    )

    def handle(self, *args, **options):
        space, layer, document_type, user = demo_context()
        table_type = ObjectType.objects.get(name=DEMO_TABLE_TYPE_NAME, scope=ObjectType.Scope.BASE)

        call(
            "create_object",
            "harnais-web",
            {
                "space_id": str(space.id),
                "type_id": str(table_type.id),
                "attributes": {"name": "table-demo-bus"},
                "author_username": user.username,
            },
        )
        call(
            "create_object",
            "lecteur-demo",
            {
                "space_id": str(space.id),
                "type_id": str(table_type.id),
                "attributes": {"name": "table-refusee"},
                "author_username": user.username,
            },
        )
        call("verbe-inexistant", "harnais-web", {})

        self.stdout.write(self.style.SUCCESS("3 appels passés par le bus. Journal :"))
        for entry in CallLog.objects.order_by("-created_at")[:3][::-1]:
            statut = "autorisé" if entry.allowed else f"refusé ({entry.error})"
            self.stdout.write(f"  {entry.verb} @ {entry.client_id} -> {statut}")
