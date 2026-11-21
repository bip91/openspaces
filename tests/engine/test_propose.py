from engine.models import Proposal
from engine.services.propose import record_proposal


def test_record_proposal_creates_pending_entry(db):
    proposal = record_proposal("manual-prompt", {"text": "le délai doit être facultatif"})

    assert Proposal.objects.filter(pk=proposal.pk).exists()
    assert proposal.decision == Proposal.Decision.PENDING
    assert proposal.output is None
    assert proposal.input == {"text": "le délai doit être facultatif"}
