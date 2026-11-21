"""Rendu et édition des vues (lot 2).

``render_view`` ne lit jamais qu'``attributes`` sur la version courante — aucune copie
des attributs ailleurs, pour ne pas fermer la porte à un filtrage par objet/attribut
lors d'un futur partage (voir CLAUDE.md, section Sécurité).
"""

from engine.models import Object, ViewTemplate
from engine.services.update import update_object


def effective_view_templates(object_type):
    return ViewTemplate.objects.filter(applies_to=object_type)


def render_view(object, view_template):
    attributes = object.current_version.attributes
    fields = attributes.get("fields", [])

    if view_template.renderer == "table":
        return {
            "columns": ["name", "type", "nullable"],
            "rows": fields,
        }

    if view_template.renderer == "mermaid.erDiagram":
        lines = ["erDiagram", f"    {attributes.get('name', 'TABLE')} {{"]
        for field in fields:
            nullable = "" if field.get("nullable") else "not-null"
            lines.append(f"        {field.get('type', 'string')} {field.get('name', '')} {nullable}".rstrip())
        lines.append("    }")
        return {"text": "\n".join(lines)}

    if view_template.renderer == "markdown":
        lines = [f"# {attributes.get('name', '(sans nom)')}", ""]
        for field in fields:
            nullable = "facultatif" if field.get("nullable") else "obligatoire"
            lines.append(f"- **{field.get('name')}** ({field.get('type')}, {nullable})")
        return {"text": "\n".join(lines)}

    raise ValueError(f"renderer inconnu : {view_template.renderer}")


def apply_view_edit(object_id, expected_version_number, changes: dict, *, author=None, agent_name=None):
    """Fusionne ``changes`` dans les attributs courants et délègue à update_object :

    même refus sur conflit de version, même événement, rien de dupliqué.
    """
    obj = Object.objects.get(pk=object_id)
    attributes = dict(obj.current_version.attributes)
    attributes.update(changes)
    return update_object(object_id, expected_version_number, attributes, author=author, agent_name=agent_name)
