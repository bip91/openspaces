"""Construction de l'agent Pydantic AI (lot 4).

Lazy : l'agent n'est construit qu'à l'appel, pas à l'import du module —
pour que l'import de ``ai`` n'exige pas Ollama en marche (utile aux tests,
qui mockent l'agent plutôt que de l'appeler réellement).
"""

from django.conf import settings
from pydantic_ai import Agent, NativeOutput
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider


def build_agent(output_type, system_prompt: str) -> Agent:
    """``NativeOutput`` : décodage contraint par schéma (Ollama 0.5+, via
    llama.cpp). Sans lui, un petit modèle produit parfois un JSON invalide
    ou hors-schéma — constaté en test avec qwen2.5:0.5b."""
    model = OllamaModel(
        settings.AI_MODEL_NAME,
        provider=OllamaProvider(base_url=settings.OLLAMA_BASE_URL),
    )
    return Agent(model, output_type=NativeOutput(output_type), system_prompt=system_prompt)
