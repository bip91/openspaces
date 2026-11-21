"""Noms fixes des données de démonstration (voir `seed_demo`).

Le harnais tourne pour un seul utilisateur, sans page de connexion : on va chercher
cet espace/calque/type par leur nom plutôt que par une session.
"""

from django.contrib.auth.models import User

from engine.models import Layer, ObjectType, Space

DEMO_USERNAME = "demo"
DEMO_SPACE_NAME = "démo"
DEMO_LAYER_ROLE = "développeur"
DEMO_LAYER_ROLE_FONCTIONNEL = "fonctionnel"
DEMO_TYPE_NAME = "Document"
DEMO_SECOND_TYPE_NAME = "Exigence"
DEMO_TABLE_TYPE_NAME = "Table"
DEMO_TABLE_OBJECT_NAME = "commande"


def demo_context():
    """Renvoie (space, layer, document_type, user) ou lève une erreur explicite."""
    try:
        user = User.objects.get(username=DEMO_USERNAME)
        space = Space.objects.get(name=DEMO_SPACE_NAME)
        layer = Layer.objects.get(space=space, role=DEMO_LAYER_ROLE)
        document_type = ObjectType.objects.get(name=DEMO_TYPE_NAME, scope=ObjectType.Scope.BASE)
    except (User.DoesNotExist, Space.DoesNotExist, Layer.DoesNotExist, ObjectType.DoesNotExist) as exc:
        raise RuntimeError(
            "Données de démo manquantes : lancez `python manage.py seed_demo`."
        ) from exc
    return space, layer, document_type, user
