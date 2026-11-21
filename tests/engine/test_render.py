import pytest

from engine.services.errors import VersionConflict
from engine.services.render import apply_view_edit, render_view


def test_render_view_table_returns_fields_as_rows(commande, view_template_table):
    result = render_view(commande, view_template_table)

    assert result["columns"] == ["name", "type", "nullable"]
    assert result["rows"] == commande.current_version.attributes["fields"]


def test_render_view_mermaid_includes_fields(commande, view_template_mermaid):
    result = render_view(commande, view_template_mermaid)

    assert "erDiagram" in result["text"]
    assert "commande" in result["text"]
    assert "delai" in result["text"]
    assert "not-null" in result["text"]


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
