from pathlib import Path

from django.core.management.base import BaseCommand

from engine.models import Object
from engine.services.blob import store_blob
from engine.services.create import create_object
from engine.services.update import update_object as update_object_service
from ui.demo import demo_context

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "mails"


class Command(BaseCommand):
    help = (
        "Importe les mails du jeu de test (tests/fixtures/mails/) comme objets Document, "
        "pour avoir de vraies données à explorer (lot 5). Rejouable : dédoublonne par nom "
        "et par empreinte de contenu, comme le dépôt de fichier du harnais web."
    )

    def handle(self, *args, **options):
        space, layer, document_type, user = demo_context()
        created, updated, unchanged = [], [], []

        for path in sorted(FIXTURES_DIR.glob("*.md")):
            content = path.read_bytes()
            blob = store_blob(content, "text/markdown")
            attributes = {"name": path.name, "mime_type": "text/markdown", "size": len(content)}
            provenance = {"source_blob": blob, "operation": "import-fixture-lot5"}

            existing = (
                Object.objects.filter(
                    space=space, base_type=document_type, current_version__attributes__name=path.name
                )
                .select_related("current_version")
                .first()
            )
            existing_provenance = existing.current_version.provenances.first() if existing else None
            unchanged_flag = existing_provenance and existing_provenance.source_blob_id == blob.sha256

            if unchanged_flag:
                unchanged.append(path.name)
            elif existing:
                update_object_service(
                    existing.id, existing.current_version.number, attributes, author=user, provenance=provenance
                )
                updated.append(path.name)
            else:
                create_object(space, document_type, attributes, author=user, provenance=provenance)
                created.append(path.name)

        self.stdout.write(
            self.style.SUCCESS(f"{len(created)} créés, {len(updated)} mis à jour, {len(unchanged)} inchangés.")
        )
