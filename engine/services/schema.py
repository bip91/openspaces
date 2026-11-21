"""Résolution et validation du schéma effectif d'un ObjectType.

Simplification documentée (lot 1) : la fusion est une union simple des
``properties`` (l'enfant l'emporte sur collision) et une union des
``required``. La vraie fonction de ``merge`` par type reste une question
ouverte de la spec (voir docs/spec.md, « Questions ouvertes et suite »).
"""

import jsonschema

from engine.services.errors import SchemaValidationError


def _ancestor_chain(object_type):
    """Du plus ancien ancêtre jusqu'au type lui-même."""
    chain = []
    current = object_type
    while current is not None:
        chain.append(current)
        current = current.parent
    return list(reversed(chain))


def _merge_schema(base, addition):
    merged = {
        "type": addition.get("type", base.get("type", "object")),
        "properties": {**base.get("properties", {}), **addition.get("properties", {})},
        "required": sorted(set(base.get("required", [])) | set(addition.get("required", []))),
    }
    return merged


def effective_schema(object_type) -> dict:
    schema = {"type": "object", "properties": {}, "required": []}
    for ancestor in _ancestor_chain(object_type):
        for trait in ancestor.traits.all():
            schema = _merge_schema(schema, trait.schema)
        schema = _merge_schema(schema, ancestor.schema)
    return schema


def validate_attributes(object_type, attributes: dict) -> None:
    schema = effective_schema(object_type)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(attributes), key=str)
    if errors:
        raise SchemaValidationError([error.message for error in errors])
