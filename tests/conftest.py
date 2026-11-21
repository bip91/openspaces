import pytest
from django.contrib.auth.models import User

from engine.models import Layer, ObjectType, Space


@pytest.fixture
def user(db):
    return User.objects.create_user(username="dev")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="fonctionnel")


@pytest.fixture
def space(user):
    return Space.objects.create(name="projet-demo", owner=user)


@pytest.fixture
def layer_dev(space, user):
    return Layer.objects.create(space=space, owner=user, role="developpeur")


@pytest.fixture
def layer_fonctionnel(space, other_user):
    return Layer.objects.create(space=space, owner=other_user, role="fonctionnel")


@pytest.fixture
def table_type(db):
    return ObjectType.objects.create(
        name="Table",
        schema={
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "fields": {"type": "array", "items": {"type": "object"}},
            },
        },
    )
