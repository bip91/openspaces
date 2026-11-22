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

# Dossiers dynamiques : appartenance calculée (query), pas posée par un Link.
# `filter`/`exclude` — convention reprise de Django, chemins ORM classiques en
# clé (voir ui/views.py::object_browse).
DYNAMIC_FOLDERS = {
    "En attente de validation": {
        # Créé par un agent, jamais relu par un humain (engine/services/create.py :
        # nature="agent" => validated=False). Se vide tout seul dès qu'un humain
        # réenregistre l'objet (update_object positionne alors validated=True).
        "filter": {"current_version__validated": False},
    },
    "Tables non classées": {
        # Objets de type Table sans aucun Link de classification vers un Dossier.
        "filter": {"base_type__name": "Table"},
        "exclude": {"links_from__nature": FOLDER_LINK_NATURE},
    },
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

        dynamic_folders_created = []
        for folder_name, query in DYNAMIC_FOLDERS.items():
            if not Object.objects.filter(
                space=space, base_type=folder_type, current_version__attributes__name=folder_name
            ).exists():
                create_object(space, folder_type, {"name": folder_name, "query": query}, author=user)
                dynamic_folders_created.append(folder_name)

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(folders_created)} dossier(s) créé(s), {classifications_created} classement(s) créé(s), "
                f"dossiers dynamiques créés : {dynamic_folders_created or 'aucun'}."
            )
        )
