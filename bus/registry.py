"""Registre des capacités et des clients du noyau du bus (lot 3).

Le type d'entrée n'est pas redéclaré ici : il est lu dynamiquement depuis
``mcp_server.server.server`` (JSON Schema généré depuis les annotations de
type de chaque outil). Le registre n'ajoute que ce que MCP ne sait pas
exprimer : l'effet et la réversibilité d'un verbe.
"""

import asyncio
from dataclasses import dataclass

from mcp_server import server as mcp_server_module


@dataclass(frozen=True)
class Capability:
    effect: str  # "read" ou "write"
    reversible: bool
    component: str
    implementation: callable


# Tous réversibles aujourd'hui : rien n'est détruit, tout est versionné
# (règles d'architecture du CLAUDE.md). Le jour où un verbe vraiment
# irréversible apparaît dans le contrat, il s'ajoute ici avec
# ``reversible=False`` — le noyau en déduira seul qu'une confirmation est
# requise, sans changer sa logique.
CAPABILITIES: dict[str, Capability] = {
    "create_object": Capability("write", True, "engine", mcp_server_module._create_object),
    "update_object": Capability("write", True, "engine", mcp_server_module._update_object),
    "link_objects": Capability("write", True, "engine", mcp_server_module._link_objects),
    "set_typing": Capability("write", True, "engine", mcp_server_module._set_typing),
    "render_view": Capability("read", True, "engine", mcp_server_module._render_view),
    "apply_view_edit": Capability("write", True, "engine", mcp_server_module._apply_view_edit),
}

# Registre statique et grossier (périmètre maquette : « hors droits fins »).
# Pas de modèle en base — une vraie gestion des droits viendrait avec le
# partage d'espaces, hors périmètre.
CLIENTS: dict[str, set[str]] = {
    "harnais-web": {"read", "write"},
    "agent-mcp": {"read", "write"},
    "lecteur-demo": {"read"},
}


# Schémas d'entrée des outils MCP, calculés une fois (ils sont dérivés des
# annotations de type, statiques pour la durée du process).
_INPUT_SCHEMAS: dict[str, dict] = {
    tool.name: tool.input_schema for tool in asyncio.run(mcp_server_module.server.list_tools())
}


def input_schema(verb: str) -> dict:
    """Schéma d'entrée déclaré par l'outil MCP correspondant, pour la validation du noyau."""
    return _INPUT_SCHEMAS[verb]
