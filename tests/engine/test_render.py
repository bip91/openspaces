import pytest

from engine.services.create import create_object
from engine.services.errors import VersionConflict
from engine.services.link import link_objects
from engine.services.render import apply_view_edit, render_view


def test_render_view_table_returns_fields_as_rows(commande, view_template_table):
    result = render_view(commande, view_template_table)

    assert result["columns"] == ["name", "type", "nullable"]
    assert result["rows"] == commande.current_version.attributes["fields"]


def test_render_view_mermaid_includes_fields(commande, view_template_mermaid):
    result = render_view(commande, view_template_mermaid)

    assert "erDiagram" in result["text"]
    assert "commande" in result["text"]
    assert "integer delai" in result["text"]


def test_render_view_mermaid_uses_exactly_two_tokens_per_attribute(commande, view_template_mermaid):
    """type + nom, rien d'autre : un 3e terme libre casse la syntaxe erDiagram."""
    apply_view_edit(commande.id, 1, {"fields": [
        {"name": "id", "type": "uuid", "nullable": False},
        {"name": "delai", "type": "integer", "nullable": True},
    ]}, author=commande.current_version.author)
    commande.refresh_from_db()

    result = render_view(commande, view_template_mermaid)

    for line in result["text"].splitlines():
        stripped = line.strip()
        if stripped and stripped not in ("erDiagram", "}") and not stripped.endswith("{"):
            if "||--o{" not in stripped:
                assert len(stripped.split()) == 2, stripped

    assert "uuid id" in result["text"]
    assert "integer delai" in result["text"]


def test_render_view_mermaid_includes_outgoing_link(commande, view_template_mermaid, space, table_type, user):
    ligne = create_object(
        space,
        table_type,
        {"name": "ligne_commande", "fields": [{"name": "id", "type": "uuid", "nullable": False}]},
        author=user,
    )
    link_objects("correspondence", commande, ligne, author=user)

    result = render_view(commande, view_template_mermaid)

    assert 'commande ||--o{ ligne_commande : "correspondence"' in result["text"]
    assert "ligne_commande {" in result["text"]


def test_render_view_mermaid_includes_incoming_link(commande, view_template_mermaid, space, table_type, user):
    client_table = create_object(
        space,
        table_type,
        {"name": "client", "fields": [{"name": "id", "type": "uuid", "nullable": False}]},
        author=user,
    )
    link_objects("correspondence", client_table, commande, author=user)

    result = render_view(commande, view_template_mermaid)

    assert 'client ||--o{ commande : "correspondence"' in result["text"]
    assert "client {" in result["text"]


def test_render_view_mermaid_ignores_links_to_non_table_objects(commande, view_template_mermaid, space, user):
    from engine.models import ObjectType

    document_type = ObjectType.objects.create(
        name="Document", schema={"type": "object", "properties": {"name": {"type": "string"}}}
    )
    document = create_object(space, document_type, {"name": "note.txt"}, author=user)
    link_objects("correspondence", commande, document, author=user)

    result = render_view(commande, view_template_mermaid)

    assert "note.txt" not in result["text"]


def test_render_view_markdown_includes_fields(commande, view_template_markdown):
    result = render_view(commande, view_template_markdown)

    assert "# commande" in result["text"]
    assert "delai" in result["text"]
    assert "obligatoire" in result["text"]


def test_apply_view_edit_changes_field_and_bumps_version(commande):
    new_fields = [
        {"name": "id", "type": "uuid", "nullable": False},
        {"name": "delai", "type": "integer", "nullable": True},
    ]

    version = apply_view_edit(commande.id, 1, {"fields": new_fields}, author=commande.current_version.author)

    assert version.number == 2
    assert version.attributes["fields"][1]["nullable"] is True


def test_apply_view_edit_rejects_stale_version(commande):
    apply_view_edit(commande.id, 1, {"name": "commande-v2"}, author=commande.current_version.author)

    with pytest.raises(VersionConflict):
        apply_view_edit(commande.id, 1, {"name": "commande-v3-perdue"}, author=commande.current_version.author)
