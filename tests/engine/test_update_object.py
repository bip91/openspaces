import pytest

from engine.models import Event, Version
from engine.services.create import create_object
from engine.services.errors import SchemaValidationError, VersionConflict
from engine.services.update import update_object


def test_update_object_creates_next_version(space, table_type, user):
    obj = create_object(space, table_type, {"name": "commande"}, author=user)

    version = update_object(obj.pk, 1, {"name": "commande_client"}, author=user)

    obj.refresh_from_db()
    assert version.number == 2
    assert obj.current_version == version
    assert obj.current_version.attributes == {"name": "commande_client"}


def test_update_object_writes_updated_event(space, table_type, user):
    obj = create_object(space, table_type, {"name": "commande"}, author=user)
    update_object(obj.pk, 1, {"name": "commande_client"}, author=user)

    events = list(Event.objects.filter(object=obj).order_by("created_at"))
    assert [e.nature for e in events] == ["created", "updated"]


def test_update_object_rejects_stale_version_without_mutating(space, table_type, user):
    obj = create_object(space, table_type, {"name": "commande"}, author=user)
    update_object(obj.pk, 1, {"name": "commande_v2"}, author=user)

    with pytest.raises(VersionConflict) as exc_info:
        update_object(obj.pk, 1, {"name": "commande_v3_perdue"}, author=user)

    assert exc_info.value.current_version.number == 2
    obj.refresh_from_db()
    assert obj.current_version.number == 2
    assert obj.current_version.attributes == {"name": "commande_v2"}
    assert Version.objects.filter(object=obj).count() == 2


def test_update_object_rejects_invalid_attributes(space, table_type, user):
    obj = create_object(space, table_type, {"name": "commande"}, author=user)

    with pytest.raises(SchemaValidationError):
        update_object(obj.pk, 1, {}, author=user)


def test_update_object_by_agent_is_unvalidated(space, table_type, user):
    obj = create_object(space, table_type, {"name": "commande"}, author=user)

    version = update_object(obj.pk, 1, {"name": "commande_reinterpretee"}, agent_name="reinterpretation-spec")

    assert version.nature == Version.Nature.AGENT
    assert version.validated is False
