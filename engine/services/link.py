from django.db import transaction

from engine.models import Event, Link
from engine.services._actor import require_actor
from engine.services.aspects import run_aspects


@transaction.atomic
def link_objects(nature, source, target, *, layer=None, author=None, agent_name=None, proposed_by=None):
    """Crée un lien actif entre deux objets et journalise l'événement sur la source.

    ``proposed_by`` : la Proposal IA dont ce lien est issu, si c'est le cas
    (voir ``engine.services.propose.decide_proposal``).
    """
    _, _ = require_actor(author, agent_name)

    link = Link.objects.create(
        nature=nature,
        source=source,
        target=target,
        layer=layer,
        version=source.current_version,
        status=Link.Status.ACTIVE,
        proposed_by=proposed_by,
    )
    event = Event.objects.create(
        object=source, version=source.current_version, nature="linked", author=author, agent_name=agent_name
    )
    run_aspects(source, event)
    return link
