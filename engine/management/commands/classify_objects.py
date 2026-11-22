from django.core.management.base import BaseCommand

from engine.models import Link, Object, ObjectType
from engine.services.create import create_object
from engine.services.link import link_objects
from ui.demo import DEMO_FOLDER_TYPE_NAME, FOLDER_LINK_NATURE, demo_context

# Classement par activité, pas par type (le filtre type existe déjà sur
# /objects/browse/, inutile de le dupliquer en dossier). Noms d'objets réels
# accumulés au fil des sessions de travail/test de ce projet.
FOLDERS = {
    "Jeu de test — atelier de design": [
        "01-historique-modifications.md",
        "02-vues-multiples.md",
        "03-dependances-composants.md",
        "04-fichiers-sources.md",
        "05-alertes-changement.md",
        "06-ecarts-de-lecture.md",
        "07-retrouver-par-le-sens.md",
        "08-signature-double.md",
        "09-suggestions-automatiques.md",
    ],
    "Modèle du moteur (code)": [
        "Space", "Layer", "ObjectType", "ViewTemplate", "Object", "Version",
        "Typing", "Proposal", "Link", "Blob", "Provenance", "Aspect", "Event",
        "Divergence", "Embedding",
    ],
    "Exigences lot 4": [
        "délai obligatoire",
        "Identification des changements de composants",
        "Restitution complète des changements d'un composant",
    ],
    "Documentation du projet": [
        "Architecte produit (vision desktop)",
        "ADV / assistante administrative",
        "Architecture SI",
        "Directeur",
        "B10 reformulé : classement par activité, IA en rattrapage",
    ],
    "Tests techniques (bus, UI)": [
        "table-demo-bus",
        "depuis-ui-bus",
        "demo-terminal-1",
    ],
}


class Command(BaseCommand):
    help = "Classe les objets réels accumulés dans l'espace de démo, par activité (Dossier)."

    def handle(self, *args, **options):
        space, layer, document_type, user = demo_context()
        folder_type = ObjectType.objects.get(name=DEMO_FOLDER_TYPE_NAME, scope=ObjectType.Scope.BASE)

        folders_created, classifications_created = [], 0
        for folder_name, object_names in FOLDERS.items():
            folder = Object.objects.filter(
                space=space, base_type=folder_type, current_version__attributes__name=folder_name
            ).first()
            if folder is None:
                folder = create_object(space, folder_type, {"name": folder_name}, author=user)
                folders_created.append(folder_name)

            for object_name in object_names:
                obj = Object.objects.filter(
                    space=space, current_version__attributes__name=object_name
                ).exclude(pk=folder.pk).first()
                if obj is None:
                    continue
                if not Link.objects.filter(source=obj, target=folder, nature=FOLDER_LINK_NATURE).exists():
                    link_objects(FOLDER_LINK_NATURE, obj, folder, author=user)
                    classifications_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(folders_created)} dossier(s) créé(s), {classifications_created} classement(s) créé(s)."
            )
        )
