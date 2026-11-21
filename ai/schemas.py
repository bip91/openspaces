"""Sorties structurées des opérations IA (lot 4)."""

from typing import Literal

from pydantic import BaseModel, Field


class ExtractedRequirement(BaseModel):
    name: str = Field(description="Nom court de l'exigence")
    field: str | None = Field(default=None, description="Champ technique concerné, si identifiable")
    rule: Literal["obligatoire", "facultatif"] | None = Field(default=None)
    quote: str = Field(description="Citation exacte du passage source qui justifie cette exigence")


class ExtractionResult(BaseModel):
    requirements: list[ExtractedRequirement]


class ProposedLink(BaseModel):
    table_name: str = Field(description="Nom exact d'une des tables candidates fournies")
    nature: str = Field(description="Nature du lien, ex. « correspondence »")
    confidence: float = Field(ge=0, le=1)


class LinkingResult(BaseModel):
    links: list[ProposedLink]
