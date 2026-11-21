from unittest.mock import MagicMock

from ai.linking import propose_links
from ai.schemas import LinkingResult, ProposedLink


def test_propose_links_returns_the_agent_output(monkeypatch):
    fake_result = MagicMock(
        output=LinkingResult(links=[ProposedLink(table_name="commande", nature="correspondence", confidence=0.8)])
    )
    fake_agent = MagicMock(run_sync=MagicMock(return_value=fake_result))
    monkeypatch.setattr("ai.linking.build_agent", lambda output_type, system_prompt: fake_agent)

    result = propose_links({"name": "délai obligatoire"}, [{"name": "commande", "fields": []}])

    assert result.links[0].table_name == "commande"
    fake_agent.run_sync.assert_called_once()
