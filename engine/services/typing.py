from django.db import transaction

from engine.models import Event, Typing
from engine.services._actor import require_actor


@transaction.atomic
def set_typing(object, layer, object_type, *, author=None, agent_name=None):
    """Ajoute un typage de ``object`` pour ``layer``. Idempotent sur (object, layer, type)."""
    require_actor(author, agent_name)

    typing, created = Typing.objects.get_or_create(object=object, layer=layer, type=object_type)
    if created:
        Event.objects.create(
            object=object,
            version=object.current_version,
            nature="typed",
            author=author,
            agent_name=agent_name,
        )
    return typing
