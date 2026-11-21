from django.db import transaction

from engine.models import Layer, Object, ObjectType, Proposal, Space
from engine.services.create import create_object
from engine.services.link import link_objects as link_objects_service


@transaction.atomic
def record_proposal(operation: str, input_data: dict) -> Proposal:
    """Journalise une proposition en attente, sans sortie IA encore produite
    (ex. texte collé non encore traité)."""
    return Proposal.objects.create(operation=operation, input=input_data)


@transaction.atomic
def record_ai_proposal(operation: str, input_data: dict, output: dict, model: str, duration_ms: int) -> Proposal:
    """Journalise une sortie IA complète : entrée, sortie, modèle, durée (règle 9).

    ``decision`` reste ``PENDING`` : rien n'est appliqué sans décision.
    """
    return Proposal.objects.create(
        operation=operation, input=input_data, output=output, model=model, duration_ms=duration_ms
    )


@transaction.atomic
def decide_proposal(proposal_id, decision, *, author, correction=None) -> dict:
    """Décide d'une proposition IA et applique son effet (règle 9).

    Attribution de la version/du lien qui en résulte : ``ACCEPTED`` (sortie
    IA inchangée) → agent, ``agent_name=proposal.model`` ; ``MODIFIED``
    (retouchée par un humain via ``correction``) → humain, ``author``. Une
    fois qu'un humain y touche, c'est humain (règle 4). ``REJECTED`` ne crée
    ni ne lie rien. Une proposition déjà décidée ne peut pas être redécidée.
    """
    proposal = Proposal.objects.select_for_update().get(pk=proposal_id)
    if proposal.decision != Proposal.Decision.PENDING:
        raise ValueError(f"proposition déjà décidée ({proposal.decision})")

    proposal.decision = decision
    proposal.correction = correction
    proposal.save(update_fields=["decision", "correction"])

    if decision == Proposal.Decision.REJECTED:
        return {"created": [], "linked": [], "skipped": []}

    effective = correction if correction is not None else proposal.output
    actor_kwargs = {"author": author} if decision == Proposal.Decision.MODIFIED else {"agent_name": proposal.model}

    if proposal.operation == "extraction-exigences":
        return _apply_extraction(proposal, effective, actor_kwargs)
    if proposal.operation == "proposition-liens":
        return _apply_linking(proposal, effective, actor_kwargs)
    raise ValueError(f"opération inconnue : {proposal.operation}")


def _apply_extraction(proposal, effective, actor_kwargs) -> dict:
    space = Space.objects.get(pk=proposal.input["space_id"])
    exigence_type = ObjectType.objects.get(name="Exigence", scope=ObjectType.Scope.BASE)

    created = []
    for requirement in effective.get("requirements", []):
        attributes = {"name": requirement["name"]}
        if requirement.get("field"):
            attributes["field"] = requirement["field"]
        if requirement.get("rule"):
            attributes["rule"] = requirement["rule"]
        obj = create_object(
            space,
            exigence_type,
            attributes,
            provenance={"anchor": {"quote": requirement.get("quote")}, "operation": proposal.operation},
            **actor_kwargs,
        )
        created.append(obj)
    return {"created": created, "linked": [], "skipped": []}


def _apply_linking(proposal, effective, actor_kwargs) -> dict:
    layer = Layer.objects.get(pk=proposal.input["layer_id"])
    source = Object.objects.get(pk=proposal.input["exigence_id"])

    linked, skipped = [], []
    for link_data in effective.get("links", []):
        try:
            target = Object.objects.get(
                space=source.space, current_version__attributes__name=link_data["table_name"]
            )
        except Object.DoesNotExist:
            skipped.append(link_data["table_name"])
            continue
        link = link_objects_service(
            link_data["nature"], source, target, layer=layer, proposed_by=proposal, **actor_kwargs
        )
        linked.append(link)
    return {"created": [], "linked": linked, "skipped": skipped}
