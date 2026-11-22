import pytest
from django.contrib.auth.models import User

from engine.models import Layer, ObjectType, Space, ViewTemplate
from engine.services.create import create_object
from ui.demo import (
    DEMO_FOLDER_TYPE_NAME,
    DEMO_LAYER_ROLE,
    DEMO_LAYER_ROLE_FONCTIONNEL,
    DEMO_SECOND_TYPE_NAME,
    DEMO_SPACE_NAME,
    DEMO_TABLE_OBJECT_NAME,
    DEMO_TABLE_TYPE_NAME,
    DEMO_TYPE_NAME,
    DEMO_USERNAME,
)


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
def demo_layer_fonctionnel(demo_space, demo_user):
    return Layer.objects.create(space=demo_space, owner=demo_user, role=DEMO_LAYER_ROLE_FONCTIONNEL)


@pytest.fixture
def demo_second_type(db):
    return ObjectType.objects.create(
        name=DEMO_SECOND_TYPE_NAME,
        scope=ObjectType.Scope.BASE,
        schema={"type": "object", "properties": {"name": {"type": "string"}}},
    )


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
def demo_folder_type(db):
    return ObjectType.objects.create(
        name=DEMO_FOLDER_TYPE_NAME,
        scope=ObjectType.Scope.BASE,
        schema={"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}},
    )


@pytest.fixture
def demo_table_type(db):
    return ObjectType.objects.create(
        name=DEMO_TABLE_TYPE_NAME,
        scope=ObjectType.Scope.BASE,
        schema={
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "fields": {"type": "array", "items": {"type": "object"}},
            },
        },
    )


@pytest.fixture
def demo_view_templates(demo_table_type):
    return [
        ViewTemplate.objects.create(
            name="table-grid",
            applies_to=demo_table_type,
            kind=ViewTemplate.Kind.STRUCTURED,
            renderer="table",
            editable=True,
        ),
        ViewTemplate.objects.create(
            name="table-mermaid",
            applies_to=demo_table_type,
            kind=ViewTemplate.Kind.STRUCTURED,
            renderer="mermaid.erDiagram",
            editable=True,
        ),
        ViewTemplate.objects.create(
            name="table-spec",
            applies_to=demo_table_type,
            kind=ViewTemplate.Kind.NARRATIVE,
            renderer="markdown",
            editable=False,
        ),
    ]


@pytest.fixture
def demo_commande(demo_space, demo_table_type, demo_user, demo_view_templates):
    return create_object(
        demo_space,
        demo_table_type,
        {
            "name": DEMO_TABLE_OBJECT_NAME,
            "fields": [
                {"name": "id", "type": "uuid", "nullable": False},
                {"name": "delai", "type": "integer", "nullable": False},
            ],
        },
        author=demo_user,
    )


@pytest.fixture
def demo_context(demo_space, demo_layer, demo_layer_fonctionnel, demo_type, demo_second_type, demo_folder_type):
    return demo_space, demo_layer, demo_type
