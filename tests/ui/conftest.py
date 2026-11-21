import pytest
from django.contrib.auth.models import User

from engine.models import Layer, ObjectType, Space
from ui.demo import DEMO_LAYER_ROLE, DEMO_SPACE_NAME, DEMO_TYPE_NAME, DEMO_USERNAME


@pytest.fixture
def demo_user(db):
    return User.objects.create_user(username=DEMO_USERNAME)


@pytest.fixture
def demo_space(demo_user):
    return Space.objects.create(name=DEMO_SPACE_NAME, owner=demo_user)


@pytest.fixture
def demo_layer(demo_space, demo_user):
    return Layer.objects.create(space=demo_space, owner=demo_user, role=DEMO_LAYER_ROLE)


@pytest.fixture
def demo_type(db):
    return ObjectType.objects.create(
        name=DEMO_TYPE_NAME,
        scope=ObjectType.Scope.BASE,
        schema={
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "mime_type": {"type": "string"},
                "size": {"type": "integer"},
            },
        },
    )


@pytest.fixture
def demo_context(demo_space, demo_layer, demo_type):
    return demo_space, demo_layer, demo_type
