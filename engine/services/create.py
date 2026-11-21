from django.db import transaction

from engine.models import Event, Object, Provenance, Version
from engine.services._actor import require_actor
from engine.services.hashing import sha256_attributes
from engine.services.schema import validate_attributes


@transaction.atomic
def create_object(space, object_type, attributes, *, author=None, agent_name=None, provenance=None):
    """Crée un objet et sa première version. Écrit un événement ``created``.

    ``provenance`` est un dict optionnel : {"source_object", "source_blob", "anchor", "operation"}.
    """
    nature, _ = require_actor(author, agent_name)
    validate_attributes(object_type, attributes)

    obj = Object.objects.create(space=space, base_type=object_type)
    version = Version.objects.create(
        object=obj,
        number=1,
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

    Event.objects.create(object=obj, version=version, nature="created", author=author, agent_name=agent_name)
    return obj
