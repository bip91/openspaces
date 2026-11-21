"""Contrat MCP du moteur : create_object, update_object, link_objects, set_typing (lot 1),
render_view, apply_view_edit (lot 2).

Chaque outil est une fine couche de (dé)sérialisation au-dessus de engine/services ;
aucune règle métier n'est dupliquée ici.
"""

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from mcp.server.mcpserver import MCPServer

from engine.models import Layer, Object, ObjectType, Space, ViewTemplate
from engine.services.create import create_object as engine_create_object
from engine.services.errors import SchemaValidationError, VersionConflict
from engine.services.link import link_objects as engine_link_objects
from engine.services.render import apply_view_edit as engine_apply_view_edit
from engine.services.render import render_view as engine_render_view
from engine.services.typing import set_typing as engine_set_typing
from engine.services.update import update_object as engine_update_object
from mcp_server.serializers import serialize_link, serialize_object, serialize_typing, serialize_version

server = MCPServer(
    "openspaces-engine",
    instructions="Contrat MCP du moteur d'objets collaboratif (lot 1).",
)


def _resolve_actor(author_username, agent_name):
    if author_username:
        return User.objects.get(username=author_username), None
    return None, agent_name


def _not_found(message):
    return {"error": "not_found", "message": message}


def _create_object(
    space_id: str,
    type_id: str,
    attributes: dict,
    author_username: str | None = None,
    agent_name: str | None = None,
) -> dict:
    try:
        space = Space.objects.get(pk=space_id)
        object_type = ObjectType.objects.get(pk=type_id)
        author, agent_name = _resolve_actor(author_username, agent_name)
    except ObjectDoesNotExist as exc:
        return _not_found(str(exc))
    except ValueError as exc:
        return {"error": "actor", "message": str(exc)}

    try:
        obj = engine_create_object(space, object_type, attributes, author=author, agent_name=agent_name)
    except SchemaValidationError as exc:
        return {"error": "schema", "errors": exc.errors}
    except ValueError as exc:
        return {"error": "actor", "message": str(exc)}

    return serialize_object(obj)


@server.tool()
def create_object(
    space_id: str,
    type_id: str,
    attributes: dict,
    author_username: str | None = None,
    agent_name: str | None = None,
) -> dict:
    """Crée un objet et sa version 1 dans l'espace donné."""
    return _create_object(space_id, type_id, attributes, author_username, agent_name)


def _update_object(
    object_id: str,
    expected_version: int,
    attributes: dict,
    author_username: str | None = None,
    agent_name: str | None = None,
) -> dict:
    try:
        author, agent_name = _resolve_actor(author_username, agent_name)
    except ObjectDoesNotExist as exc:
        return _not_found(str(exc))
    except ValueError as exc:
        return {"error": "actor", "message": str(exc)}

    try:
        version = engine_update_object(object_id, expected_version, attributes, author=author, agent_name=agent_name)
    except Object.DoesNotExist as exc:
        return _not_found(str(exc))
    except VersionConflict as exc:
        return {"error": "conflict", "current_version": serialize_version(exc.current_version)}
    except SchemaValidationError as exc:
        return {"error": "schema", "errors": exc.errors}
    except ValueError as exc:
        return {"error": "actor", "message": str(exc)}

    return serialize_version(version)


@server.tool()
def update_object(
    object_id: str,
    expected_version: int,
    attributes: dict,
    author_username: str | None = None,
    agent_name: str | None = None,
) -> dict:
    """Met à jour un objet si ``expected_version`` est bien la version courante."""
    return _update_object(object_id, expected_version, attributes, author_username, agent_name)


def _link_objects(
    nature: str,
    source_id: str,
    target_id: str,
    layer_id: str | None = None,
    author_username: str | None = None,
    agent_name: str | None = None,
) -> dict:
    try:
        source = Object.objects.get(pk=source_id)
        target = Object.objects.get(pk=target_id)
        layer = Layer.objects.get(pk=layer_id) if layer_id else None
        author, agent_name = _resolve_actor(author_username, agent_name)
    except ObjectDoesNotExist as exc:
        return _not_found(str(exc))
    except ValueError as exc:
        return {"error": "actor", "message": str(exc)}

    try:
        link = engine_link_objects(nature, source, target, layer=layer, author=author, agent_name=agent_name)
    except ValueError as exc:
        return {"error": "actor", "message": str(exc)}

    return serialize_link(link)


@server.tool()
def link_objects(
    nature: str,
    source_id: str,
    target_id: str,
    layer_id: str | None = None,
    author_username: str | None = None,
    agent_name: str | None = None,
) -> dict:
    """Crée un lien typé, actif, entre deux objets."""
    return _link_objects(nature, source_id, target_id, layer_id, author_username, agent_name)


def _set_typing(
    object_id: str,
    layer_id: str,
    type_id: str,
    author_username: str | None = None,
    agent_name: str | None = None,
) -> dict:
    try:
        obj = Object.objects.get(pk=object_id)
        layer = Layer.objects.get(pk=layer_id)
        object_type = ObjectType.objects.get(pk=type_id)
        author, agent_name = _resolve_actor(author_username, agent_name)
    except ObjectDoesNotExist as exc:
        return _not_found(str(exc))
    except ValueError as exc:
        return {"error": "actor", "message": str(exc)}

    try:
        typing = engine_set_typing(obj, layer, object_type, author=author, agent_name=agent_name)
    except ValueError as exc:
        return {"error": "actor", "message": str(exc)}

    return serialize_typing(typing)


@server.tool()
def set_typing(
    object_id: str,
    layer_id: str,
    type_id: str,
    author_username: str | None = None,
    agent_name: str | None = None,
) -> dict:
    """Ajoute un typage de l'objet pour le calque donné."""
    return _set_typing(object_id, layer_id, type_id, author_username, agent_name)


def _render_view(object_id: str, view_template_id: str) -> dict:
    try:
        obj = Object.objects.get(pk=object_id)
        view_template = ViewTemplate.objects.get(pk=view_template_id)
    except ObjectDoesNotExist as exc:
        return _not_found(str(exc))

    return engine_render_view(obj, view_template)


@server.tool()
def render_view(object_id: str, view_template_id: str) -> dict:
    """Rend un objet selon un gabarit de vue (lecture, aucune écriture)."""
    return _render_view(object_id, view_template_id)


def _apply_view_edit(
    object_id: str,
    expected_version: int,
    changes: dict,
    author_username: str | None = None,
    agent_name: str | None = None,
) -> dict:
    try:
        author, agent_name = _resolve_actor(author_username, agent_name)
    except ObjectDoesNotExist as exc:
        return _not_found(str(exc))
    except ValueError as exc:
        return {"error": "actor", "message": str(exc)}

    try:
        version = engine_apply_view_edit(
            object_id, expected_version, changes, author=author, agent_name=agent_name
        )
    except Object.DoesNotExist as exc:
        return _not_found(str(exc))
    except VersionConflict as exc:
        return {"error": "conflict", "current_version": serialize_version(exc.current_version)}
    except SchemaValidationError as exc:
        return {"error": "schema", "errors": exc.errors}
    except ValueError as exc:
        return {"error": "actor", "message": str(exc)}

    return serialize_version(version)


@server.tool()
def apply_view_edit(
    object_id: str,
    expected_version: int,
    changes: dict,
    author_username: str | None = None,
    agent_name: str | None = None,
) -> dict:
    """Applique une modification structurée (issue d'une vue) si la version attendue tient."""
    return _apply_view_edit(object_id, expected_version, changes, author_username, agent_name)
