from django.db import transaction

from engine.models import Proposal


@transaction.atomic
def record_proposal(operation: str, input_data: dict) -> Proposal:
    """Journalise une proposition en attente. Aucun traitement IA au lot 1 :

    c'est le lot 4 qui remplira ``output``/``model`` et décidera.
    """
    return Proposal.objects.create(operation=operation, input=input_data)
