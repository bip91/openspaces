import pytest

from engine.models import ObjectType
from engine.services.errors import SchemaValidationError
from engine.services.schema import effective_schema, validate_attributes


@pytest.fixture
def document_type(db):
    return ObjectType.objects.create(
        name="Document",
        schema={"type": "object", "required": ["title"], "properties": {"title": {"type": "string"}}},
    )


@pytest.fixture
def sensitive_trait(db):
    return ObjectType.objects.create(
        name="Sensible",
        schema={"type": "object", "properties": {"confidentiel": {"type": "boolean"}}},
    )


def test_effective_schema_inherits_from_parent(document_type):
    child = ObjectType.objects.create(
        name="Exigence",
        parent=document_type,
        schema={"type": "object", "required": ["description"], "properties": {"description": {"type": "string"}}},
    )

    schema = effective_schema(child)

    assert set(schema["properties"]) == {"title", "description"}
    assert set(schema["required"]) == {"title", "description"}


def test_effective_schema_includes_traits(document_type, sensitive_trait):
    child = ObjectType.objects.create(name="Exigence", parent=document_type)
    child.traits.add(sensitive_trait)

    schema = effective_schema(child)

    assert "confidentiel" in schema["properties"]
    assert "title" in schema["properties"]


def test_validate_attributes_uses_inherited_required(document_type):
    child = ObjectType.objects.create(name="Exigence", parent=document_type)

    with pytest.raises(SchemaValidationError):
        validate_attributes(child, {})

    validate_attributes(child, {"title": "délai de livraison"})
