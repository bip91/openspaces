"""Extraction d'exigences depuis un texte collé (lot 4)."""

from ai.model import build_agent
from ai.schemas import ExtractionResult

_SYSTEM_PROMPT = (
    "Tu extrais les exigences fonctionnelles d'un texte (mail, note). Pour "
    "chaque exigence : un nom court, le champ technique concerné si "
    "identifiable, la règle (obligatoire/facultatif) si elle est explicite, "
    "et la citation exacte du passage qui la justifie. N'invente rien : si "
    "le texte ne contient aucune exigence claire, renvoie une liste vide."
)


def extract_requirements(text: str) -> ExtractionResult:
    agent = build_agent(ExtractionResult, _SYSTEM_PROMPT)
    result = agent.run_sync(text)
    return result.output
