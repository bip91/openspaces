from unittest.mock import MagicMock

from ai.extraction import extract_requirements
from ai.schemas import ExtractedRequirement, ExtractionResult


def test_extract_requirements_returns_the_agent_output(monkeypatch):
    fake_result = MagicMock(
        output=ExtractionResult(
            requirements=[
                ExtractedRequirement(
                    name="délai obligatoire", field="delai", rule="obligatoire", quote="le délai est obligatoire"
                )
            ]
        )
    )
    fake_agent = MagicMock(run_sync=MagicMock(return_value=fake_result))
    monkeypatch.setattr("ai.extraction.build_agent", lambda output_type, system_prompt: fake_agent)

    result = extract_requirements("texte quelconque")

    assert result.requirements[0].name == "délai obligatoire"
    fake_agent.run_sync.assert_called_once_with("texte quelconque")
