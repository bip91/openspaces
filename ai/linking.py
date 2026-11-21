"""Proposition de liens entre une exigence et des tables candidates (lot 4)."""

import json

from ai.model import build_agent
from ai.schemas import LinkingResult

_SYSTEM_PROMPT = (
    "Tu proposes des liens entre une exigence et des tables candidates. Pour "
    "chaque table pertinente, donne son nom exact (parmi les candidates "
    "fournies), la nature du lien (ex. « correspondence ») et ta confiance "
    "entre 0 et 1. N'invente pas de nom de table hors de la liste donnée. Si "
    "aucune table ne correspond, renvoie une liste vide."
)


def propose_links(exigence: dict, candidate_tables: list[dict]) -> LinkingResult:
    agent = build_agent(LinkingResult, _SYSTEM_PROMPT)
    prompt = (
        f"Exigence : {json.dumps(exigence, ensure_ascii=False)}\n"
        f"Tables candidates : {json.dumps(candidate_tables, ensure_ascii=False)}"
    )
    result = agent.run_sync(prompt)
    return result.output
