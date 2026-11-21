import pytest

from engine.models import Link, Object, Proposal
from engine.services.create import create_object
from engine.services.propose import decide_proposal, record_ai_proposal, record_proposal


def test_record_proposal_creates_pending_entry(db):
    proposal = record_proposal("manual-prompt", {"text": "le délai doit être facultatif"})

    assert Proposal.objects.filter(pk=proposal.pk).exists()
    assert proposal.decision == Proposal.Decision.PENDING
    assert proposal.output is None
    assert proposal.input == {"text": "le délai doit être facultatif"}


def test_record_ai_proposal_fills_all_fields(db):
    proposal = record_ai_proposal(
        "extraction-exigences",
        {"text": "le délai est obligatoire"},
        {"requirements": [{"name": "délai obligatoire", "field": "delai", "rule": "obligatoire", "quote": "..."}]},
        "qwen2.5:1.5b",
        1234,
    )

    assert proposal.decision == Proposal.Decision.PENDING
    assert proposal.model == "qwen2.5:1.5b"
    assert proposal.duration_ms == 1234
    assert proposal.output["requirements"][0]["name"] == "délai obligatoire"


def test_decide_proposal_accepted_creates_exigence_attributed_to_agent(space, layer_fonctionnel, exigence_type, user):
    proposal = record_ai_proposal(
        "extraction-exigences",
        {"space_id": str(space.id), "layer_id": str(layer_fonctionnel.id), "text": "..."},
        {
            "requirements": [
                {"name": "délai obligatoire", "field": "delai", "rule": "obligatoire", "quote": "le délai..."}
            ]
        },
        "qwen2.5:1.5b",
        1000,
    )

    result = decide_proposal(proposal.id, Proposal.Decision.ACCEPTED, author=user)

    assert len(result["created"]) == 1
    obj = result["created"][0]
    assert obj.current_version.attributes == {"name": "délai obligatoire", "field": "delai", "rule": "obligatoire"}
    assert obj.current_version.nature == "agent"
    assert obj.current_version.agent_name == "qwen2.5:1.5b"
    proposal.refresh_from_db()
    assert proposal.decision == Proposal.Decision.ACCEPTED


def test_decide_proposal_modified_attributes_to_human_with_correction(space, layer_fonctionnel, exigence_type, user):
    proposal = record_ai_proposal(
        "extraction-exigences",
        {"space_id": str(space.id), "layer_id": str(layer_fonctionnel.id), "text": "..."},
        {"requirements": [{"name": "brouillon", "field": None, "rule": None, "quote": "..."}]},
        "qwen2.5:1.5b",
        1000,
    )
    correction = {
        "requirements": [
            {"name": "délai obligatoire", "field": "delai", "rule": "obligatoire", "quote": "le délai..."}
        ]
    }

    result = decide_proposal(proposal.id, Proposal.Decision.MODIFIED, author=user, correction=correction)

    obj = result["created"][0]
    assert obj.current_version.attributes["name"] == "délai obligatoire"
    assert obj.current_version.nature == "human"
    assert obj.current_version.author == user


def test_decide_proposal_rejected_creates_nothing(space, layer_fonctionnel, user):
    proposal = record_ai_proposal(
        "extraction-exigences",
        {"space_id": str(space.id), "layer_id": str(layer_fonctionnel.id), "text": "..."},
        {"requirements": [{"name": "x", "field": None, "rule": None, "quote": "..."}]},
        "qwen2.5:1.5b",
        1000,
    )

    result = decide_proposal(proposal.id, Proposal.Decision.REJECTED, author=user)

    assert result == {"created": [], "linked": [], "skipped": []}
    assert not Object.objects.filter(current_version__attributes__name="x").exists()


def test_deciding_an_already_decided_proposal_is_refused(space, layer_fonctionnel, exigence_type, user):
    proposal = record_ai_proposal(
        "extraction-exigences",
        {"space_id": str(space.id), "layer_id": str(layer_fonctionnel.id), "text": "..."},
        {"requirements": []},
        "qwen2.5:1.5b",
        1000,
    )
    decide_proposal(proposal.id, Proposal.Decision.ACCEPTED, author=user)

    with pytest.raises(ValueError):
        decide_proposal(proposal.id, Proposal.Decision.REJECTED, author=user)


def test_decide_proposal_accepted_creates_link_with_proposed_by(space, table_type, layer_fonctionnel, user):
    exigence = create_object(space, table_type, {"name": "exigence-delai"}, author=user)
    target = create_object(space, table_type, {"name": "commande"}, author=user)
    proposal = record_ai_proposal(
        "proposition-liens",
        {
            "space_id": str(space.id),
            "layer_id": str(layer_fonctionnel.id),
            "exigence_id": str(exigence.id),
            "exigence_attributes": {"name": "exigence-delai"},
        },
        {"links": [{"table_name": "commande", "nature": "correspondence", "confidence": 0.9}]},
        "qwen2.5:1.5b",
        1000,
    )

    result = decide_proposal(proposal.id, Proposal.Decision.ACCEPTED, author=user)

    link = result["linked"][0]
    assert link.proposed_by == proposal
    assert link.status == Link.Status.ACTIVE
    assert link.target == target


def test_decide_proposal_skips_a_link_to_an_unknown_table_name(space, table_type, layer_fonctionnel, user):
    exigence = create_object(space, table_type, {"name": "exigence-delai"}, author=user)
    proposal = record_ai_proposal(
        "proposition-liens",
        {
            "space_id": str(space.id),
            "layer_id": str(layer_fonctionnel.id),
            "exigence_id": str(exigence.id),
            "exigence_attributes": {"name": "exigence-delai"},
        },
        {"links": [{"table_name": "n-existe-pas", "nature": "correspondence", "confidence": 0.5}]},
        "qwen2.5:1.5b",
        1000,
    )

    result = decide_proposal(proposal.id, Proposal.Decision.ACCEPTED, author=user)

    assert result["linked"] == []
    assert result["skipped"] == ["n-existe-pas"]
