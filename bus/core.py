"""Noyau du bus de coordination (lot 3) : routage, droits, confirmation de
l'irréversible, validation des schémas, journal attribué. Déterministe,
sans IA — voir docs/spec.md, « Bus de coordination ».
"""

import time

import jsonschema
from django.db import transaction

from bus.models import CallLog
from bus.registry import CAPABILITIES, CLIENTS, input_schema


def _refuse(verb, client_id, payload, error, **extra):
    CallLog.objects.create(
        verb=verb, client_id=client_id, input=payload, allowed=False, error=error
    )
    return {"error": error, **extra}


@transaction.atomic
def call(verb: str, client_id: str, payload: dict, *, confirmed: bool = False) -> dict:
    """Point d'entrée unique du noyau. Journalise systématiquement, qu'il
    autorise l'appel ou le refuse."""
    capability = CAPABILITIES.get(verb)
    if capability is None:
        return _refuse(verb, client_id, payload, "unknown_verb")

    allowed_effects = CLIENTS.get(client_id)
    if allowed_effects is None or capability.effect not in allowed_effects:
        return _refuse(verb, client_id, payload, "forbidden")

    if not capability.reversible and not confirmed:
        return _refuse(verb, client_id, payload, "confirmation_required")

    validator = jsonschema.Draft202012Validator(input_schema(verb))
    errors = sorted(validator.iter_errors(payload), key=str)
    if errors:
        return _refuse(verb, client_id, payload, "invalid_input", errors=[e.message for e in errors])

    started = time.perf_counter()
    output = capability.implementation(**payload)
    duration_ms = int((time.perf_counter() - started) * 1000)

    CallLog.objects.create(
        verb=verb,
        client_id=client_id,
        input=payload,
        allowed=True,
        confirmed=confirmed,
        output=output,
        duration_ms=duration_ms,
    )
    return output
