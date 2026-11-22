"""Rendu et édition des vues (lot 2).

``render_view`` ne lit jamais qu'``attributes`` sur la version courante — aucune copie
des attributs ailleurs, pour ne pas fermer la porte à un filtrage par objet/attribut
lors d'un futur partage (voir CLAUDE.md, section Sécurité).
"""

import re

from engine.models import Link, Object, ViewTemplate
from engine.services.update import update_object

# Verbes de relation acceptés par le requirementDiagram de Mermaid (vérifié dans
# ui/static/ui/vendor/mermaid.min.js) : une nature de Link qui n'en fait pas partie
# (ex. "correspondence") retombe sur "satisfies", plutôt que de produire une syntaxe
# invalide.
_MERMAID_REQUIREMENT_VERBS = {
    "contains", "copies", "derives", "docref", "refines", "satisfies", "traces", "verifies",
}


def effective_view_templates(object_type):
    return ViewTemplate.objects.filter(applies_to=object_type)


def _mermaid_id(value):
    """Identifiant Mermaid sûr : un nom avec espace ou apostrophe casse la syntaxe
    (même précaution que pour erDiagram, voir plus bas)."""
    return re.sub(r"[^A-Za-z0-9_]", "_", value or "")


def _mermaid_entity_block(name, fields):
    """Deux termes par attribut (type, nom), rien d'autre : un 3e terme libre
    (``not-null``) et un ``?`` suffixé au nom cassent tous les deux la syntaxe
    erDiagram. Le nullable reste visible dans la grille et le Markdown ; pas la
    peine de retenter une 3e variante sans pouvoir la vérifier dans un vrai rendu.
    """
    lines = [f"    {name} {{"]
    for field in fields:
        lines.append(f"        {field.get('type', 'string')} {field.get('name', '')}")
    lines.append("    }")
    return lines


def _mermaid_relationships(object, name):
    """Les correspondances (Link) vers d'autres objets Table, dans les deux sens."""
    lines = []
    seen_entities = set()

    outgoing = Link.objects.filter(source=object, target__base_type__name="Table").select_related(
        "target__current_version"
    )
    for link in outgoing:
        target_attributes = link.target.current_version.attributes
        target_name = target_attributes.get("name", "TABLE")
        lines.append(f'    {name} ||--o{{ {target_name} : "{link.nature}"')
        if link.target_id not in seen_entities:
            lines += _mermaid_entity_block(target_name, target_attributes.get("fields", []))
            seen_entities.add(link.target_id)

    incoming = Link.objects.filter(target=object, source__base_type__name="Table").select_related(
        "source__current_version"
    )
    for link in incoming:
        source_attributes = link.source.current_version.attributes
        source_name = source_attributes.get("name", "TABLE")
        lines.append(f'    {source_name} ||--o{{ {name} : "{link.nature}"')
        if link.source_id not in seen_entities:
            lines += _mermaid_entity_block(source_name, source_attributes.get("fields", []))
            seen_entities.add(link.source_id)

    return lines


def render_view(object, view_template):
    attributes = object.current_version.attributes
    fields = attributes.get("fields", [])

    if view_template.renderer == "table":
        return {
            "columns": ["name", "type", "nullable"],
            "rows": fields,
        }

    if view_template.renderer == "mermaid.erDiagram":
        name = attributes.get("name", "TABLE")
        lines = ["erDiagram"]
        lines += _mermaid_entity_block(name, fields)
        lines += _mermaid_relationships(object, name)
        return {"text": "\n".join(lines)}

    if view_template.renderer == "requirementDiagram":
        name = attributes.get("name", "exigence")
        req_id = _mermaid_id(name)
        lines = ["requirementDiagram", f"    requirement {req_id} {{", f'        id: "{req_id}"', f'        text: "{name}"', "    }"]
        seen = set()
        for link in Link.objects.filter(source=object).select_related("target__current_version", "target__base_type"):
            target_attributes = link.target.current_version.attributes
            target_name = target_attributes.get("name", "element")
            target_id = _mermaid_id(target_name)
            verb = link.nature if link.nature in _MERMAID_REQUIREMENT_VERBS else "satisfies"
            if link.target_id not in seen:
                lines.append(f"    element {target_id} {{")
                lines.append(f'        type: "{link.target.base_type.name}"')
                lines.append("    }")
                seen.add(link.target_id)
            lines.append(f"    {target_id} - {verb} -> {req_id}")
        return {"text": "\n".join(lines)}

    if view_template.renderer == "mermaid.flowchart":
        steps = attributes.get("steps", [])
        lines = ["flowchart LR"]
        for step in steps:
            from_id, to_id = _mermaid_id(step["from"]), _mermaid_id(step["to"])
            lines.append(f'    {from_id}["{step["from"]}"] -->|{step["message"]}| {to_id}["{step["to"]}"]')
        return {"text": "\n".join(lines)}

    if view_template.renderer == "mermaid.sequenceDiagram":
        steps = attributes.get("steps", [])
        participants = []
        for step in steps:
            for participant in (step.get("from"), step.get("to")):
                if participant and participant not in participants:
                    participants.append(participant)
        lines = ["sequenceDiagram"]
        lines += [f"    participant {participant}" for participant in participants]
        lines += [f"    {step['from']}->>{step['to']}: {step['message']}" for step in steps]
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
