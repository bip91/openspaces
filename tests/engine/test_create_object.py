import pytest

from engine.models import Event, Object, Version
from engine.services.create import create_object
from engine.services.errors import SchemaValidationError


def test_create_object_writes_object_and_version_one(space, table_type, user):
    obj = create_object(space, table_type, {"name": "commande"}, author=user)

    assert Object.objects.filter(pk=obj.pk).exists()
    assert obj.current_version.number == 1
    assert obj.current_version.attributes == {"name": "commande"}
    assert obj.current_version.nature == Version.Nature.HUMAN
    assert obj.current_version.author == user


def test_create_object_writes_created_event(space, table_type, user):
    obj = create_object(space, table_type, {"name": "commande"}, author=user)

    event = Event.objects.get(object=obj)
    assert event.nature == "created"
    assert event.author == user


def test_create_object_by_agent_is_unvalidated(space, table_type):
    obj = create_object(space, table_type, {"name": "commande"}, agent_name="extraction-exigences")

    assert obj.current_version.nature == Version.Nature.AGENT
    assert obj.current_version.agent_name == "extraction-exigences"
    assert obj.current_version.validated is False


def test_create_object_rejects_invalid_attributes(space, table_type, user):
    with pytest.raises(SchemaValidationError):
        create_object(space, table_type, {}, author=user)


def test_create_object_requires_exactly_one_actor(space, table_type, user):
    with pytest.raises(ValueError):
        create_object(space, table_type, {"name": "commande"}, author=user, agent_name="agent")
    with pytest.raises(ValueError):
        create_object(space, table_type, {"name": "commande"})
