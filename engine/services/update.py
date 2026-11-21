from django.db import transaction

from engine.models import Event, Object, Provenance, Version
from engine.services._actor import require_actor
from engine.services.aspects import run_aspects
from engine.services.errors import VersionConflict
from engine.services.hashing import sha256_attributes
from engine.services.schema import validate_attributes


@transaction.atomic
def update_object(object_id, expected_version_number, attributes, *, author=None, agent_name=None, provenance=None):
    """Écriture optimiste : refuse sans modifier si la version attendue est dépassée.

    Verrouille la ligne ``Object`` pour la durée de la vérification + écriture, afin
    qu'aucune autre transaction concurrente ne puisse créer la version suivante entre
    la lecture de la version courante et son remplacement.
    """
    nature, _ = require_actor(author, agent_name)
    obj = Object.objects.select_for_update().get(pk=object_id)

    if obj.current_version.number != expected_version_number:
        raise VersionConflict(obj.current_version)

    validate_attributes(obj.base_type, attributes)

    version = Version.objects.create(
        object=obj,
        number=expected_version_number + 1,
        attributes=attributes,
        sha256=sha256_attributes(attributes),
        author=author,
        agent_name=agent_name,
        nature=nature,
        validated=(nature == "human"),
    )
    obj.current_version = version
    obj.save(update_fields=["current_version"])

    if provenance:
        Provenance.objects.create(version=version, **provenance)

    event = Event.objects.create(object=obj, version=version, nature="updated", author=author, agent_name=agent_name)
    run_aspects(obj, event)
    return version
