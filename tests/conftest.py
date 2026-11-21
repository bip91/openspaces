import pytest
from django.contrib.auth.models import User

from engine.models import Aspect, Layer, ObjectType, Space, ViewTemplate
from engine.services.create import create_object


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


@pytest.fixture
def view_template_table(table_type):
    return ViewTemplate.objects.create(
        name="table-grid", applies_to=table_type, kind=ViewTemplate.Kind.STRUCTURED, renderer="table", editable=True
    )


@pytest.fixture
def view_template_mermaid(table_type):
    return ViewTemplate.objects.create(
        name="table-mermaid",
        applies_to=table_type,
        kind=ViewTemplate.Kind.STRUCTURED,
        renderer="mermaid.erDiagram",
        editable=True,
    )


@pytest.fixture
def view_template_markdown(table_type):
    return ViewTemplate.objects.create(
        name="table-spec",
        applies_to=table_type,
        kind=ViewTemplate.Kind.NARRATIVE,
        renderer="markdown",
        editable=False,
    )


@pytest.fixture
def exigence_type(db):
    return ObjectType.objects.create(
        name="Exigence",
        schema={
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "field": {"type": "string"},
                "rule": {"type": "string", "enum": ["obligatoire", "facultatif"]},
            },
        },
    )


@pytest.fixture
def notify_aspect(layer_fonctionnel):
    return Aspect.objects.create(
        name="notify-field-change",
        layer=layer_fonctionnel,
        pointcut={"type": "Table", "event": "updated", "linked_from": "Exigence"},
        action={"kind": "notify", "target_layer": "fonctionnel"},
        active=True,
    )


@pytest.fixture
def check_constraint_aspect(layer_fonctionnel):
    return Aspect.objects.create(
        name="exigence-contrainte-divergence",
        layer=layer_fonctionnel,
        pointcut={"type": ["Table", "Exigence"]},
        action={"kind": "check_constraint"},
        active=True,
    )


@pytest.fixture
def commande(space, table_type, user):
    return create_object(
        space,
        table_type,
        {
            "name": "commande",
            "fields": [
                {"name": "id", "type": "uuid", "nullable": False},
                {"name": "delai", "type": "integer", "nullable": False},
            ],
        },
        author=user,
    )
