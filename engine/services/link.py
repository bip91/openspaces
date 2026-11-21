from django.db import transaction

from engine.models import Event, Link
from engine.services._actor import require_actor


@transaction.atomic
def link_objects(nature, source, target, *, layer=None, author=None, agent_name=None):
    """Crée un lien actif entre deux objets et journalise l'événement sur la source."""
    _, _ = require_actor(author, agent_name)

    link = Link.objects.create(
        nature=nature,
        source=source,
        target=target,
        layer=layer,
        version=source.current_version,
        status=Link.Status.ACTIVE,
    )
    Event.objects.create(
        object=source, version=source.current_version, nature="linked", author=author, agent_name=agent_name
    )
    return link
