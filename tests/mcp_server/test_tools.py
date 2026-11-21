from engine.models import Object
from mcp_server.server import apply_view_edit, create_object, link_objects, render_view, set_typing, update_object


def test_create_object_tool_returns_serialized_object(space, table_type, user):
    result = create_object(str(space.id), str(table_type.id), {"name": "commande"}, author_username=user.username)

    assert result["version"]["number"] == 1
    assert Object.objects.filter(pk=result["id"]).exists()


def test_create_object_tool_reports_schema_errors(space, table_type, user):
    result = create_object(str(space.id), str(table_type.id), {}, author_username=user.username)

    assert result["error"] == "schema"


def test_update_object_tool_reports_conflict(space, table_type, user):
    created = create_object(str(space.id), str(table_type.id), {"name": "commande"}, author_username=user.username)
    update_object(created["id"], 1, {"name": "v2"}, author_username=user.username)

    result = update_object(created["id"], 1, {"name": "v3_perdue"}, author_username=user.username)

    assert result["error"] == "conflict"
    assert result["current_version"]["number"] == 2


def test_link_objects_tool(space, table_type, user):
    source = create_object(str(space.id), str(table_type.id), {"name": "exigence"}, author_username=user.username)
    target = create_object(str(space.id), str(table_type.id), {"name": "table"}, author_username=user.username)

    result = link_objects("correspondence", source["id"], target["id"], author_username=user.username)

    assert result["status"] == "active"
    assert result["source_id"] == source["id"]


def test_set_typing_tool(space, table_type, layer_fonctionnel, user):
    created = create_object(str(space.id), str(table_type.id), {"name": "commande"}, author_username=user.username)

    result = set_typing(created["id"], str(layer_fonctionnel.id), str(table_type.id), author_username=user.username)

    assert result["object_id"] == created["id"]
    assert result["layer_id"] == str(layer_fonctionnel.id)


def test_render_view_tool(commande, view_template_mermaid):
    result = render_view(str(commande.id), str(view_template_mermaid.id))

    assert "erDiagram" in result["text"]
    assert "delai" in result["text"]


def test_apply_view_edit_tool_reports_conflict(commande, user):
    apply_view_edit(str(commande.id), 1, {"name": "v2"}, author_username=user.username)

    result = apply_view_edit(str(commande.id), 1, {"name": "v3-perdue"}, author_username=user.username)

    assert result["error"] == "conflict"
    assert result["current_version"]["number"] == 2
