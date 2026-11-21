from engine.models import Event, Link, Proposal
from engine.services.create import create_object
from engine.services.link import link_objects


def test_link_objects_records_proposed_by_when_given(space, table_type, user):
    source = create_object(space, table_type, {"name": "exigence-delai"}, author=user)
    target = create_object(space, table_type, {"name": "table-commande"}, author=user)
    proposal = Proposal.objects.create(operation="proposition-liens", input={})

    link = link_objects("correspondence", source, target, author=user, proposed_by=proposal)

    assert link.proposed_by == proposal


def test_link_objects_creates_active_link(space, table_type, user):
    requirement_type = table_type
    source = create_object(space, requirement_type, {"name": "exigence-delai"}, author=user)
    target = create_object(space, requirement_type, {"name": "table-commande"}, author=user)

    link = link_objects("correspondence", source, target, author=user)

    assert link.status == Link.Status.ACTIVE
    assert link.source == source
    assert link.target == target
    assert link.version == source.current_version


def test_link_objects_writes_linked_event_on_source(space, table_type, user):
    source = create_object(space, table_type, {"name": "exigence-delai"}, author=user)
    target = create_object(space, table_type, {"name": "table-commande"}, author=user)

    link_objects("correspondence", source, target, author=user)

    event = Event.objects.get(object=source, nature="linked")
    assert event.author == user
