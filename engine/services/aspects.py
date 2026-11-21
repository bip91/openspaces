"""Exécution des aspects (lot 3).

Appelé explicitement en fin de transaction par create_object/update_object/
link_objects (jamais par un signal Django) : la trace de ce qu'un aspect a fait reste
lisible depuis l'objet qu'il modifie — pas d'« action à distance invisible »
(voir CLAUDE.md, anti-modèles / AOP).
"""

from engine.models import Aspect, Divergence, Event, Link, Object


def _linked_objects_of_type(object, type_name):
    """Objets reliés à ``object`` (dans un sens ou l'autre) dont le type de base
    porte ce nom — aucune convention de direction n'est imposée pour une
    correspondance.
    """
    outgoing_ids = Link.objects.filter(source=object, target__base_type__name=type_name).values_list(
        "target_id", flat=True
    )
    incoming_ids = Link.objects.filter(target=object, source__base_type__name=type_name).values_list(
        "source_id", flat=True
    )
    return list(
        Object.objects.filter(pk__in=list(outgoing_ids) + list(incoming_ids)).select_related(
            "base_type", "current_version"
        )
    )


def _pointcut_matches(pointcut, object, event):
    expected_types = pointcut.get("type")
    if expected_types:
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if object.base_type.name not in expected_types:
            return False

    expected_event = pointcut.get("event")
    if expected_event and event.nature != expected_event:
        return False

    linked_from = pointcut.get("linked_from")
    if linked_from and not _linked_objects_of_type(object, linked_from):
        return False

    return True


def _notify(aspect, object, event):
    linked_type = aspect.pointcut.get("linked_from")
    for linked in _linked_objects_of_type(object, linked_type):
        Event.objects.create(
            object=linked,
            version=linked.current_version,
            nature="notified",
            agent_name=f"aspect:{aspect.name}",
        )


def _sync_divergence(exigence, table):
    attributes = exigence.current_version.attributes
    field_name = attributes.get("field")
    rule = attributes.get("rule")
    if not field_name or not rule:
        return  # exigence non structurée : rien à comparer automatiquement

    fields = table.current_version.attributes.get("fields", [])
    field = next((f for f in fields if f.get("name") == field_name), None)
    if field is None:
        return  # le champ visé n'existe pas (plus) sur la table

    expects_required = rule == "obligatoire"
    is_consistent = (not field.get("nullable")) == expects_required

    existing = (
        Divergence.objects.filter(related_objects=exigence, status=Divergence.Status.OPEN)
        .filter(related_objects=table)
        .first()
    )

    if is_consistent:
        if existing:
            existing.status = Divergence.Status.RESOLVED
            existing.save(update_fields=["status"])
        return

    if existing:
        return  # déjà signalée, pas de doublon

    table_name = table.current_version.attributes.get("name", table.id)
    current_state = "facultatif" if field.get("nullable") else "obligatoire"
    divergence = Divergence.objects.create(
        space=table.space,
        description=(
            f"« {attributes.get('name', exigence.id)} » exige {field_name} {rule}, "
            f"mais {table_name}.{field_name} est {current_state}."
        ),
    )
    divergence.related_objects.add(exigence, table)


def _check_constraint(object):
    if object.base_type.name == "Exigence":
        for table in _linked_objects_of_type(object, "Table"):
            _sync_divergence(object, table)
    elif object.base_type.name == "Table":
        for exigence in _linked_objects_of_type(object, "Exigence"):
            _sync_divergence(exigence, object)


def _run_action(aspect, object, event):
    kind = aspect.action.get("kind")
    if kind == "notify":
        _notify(aspect, object, event)
    elif kind == "check_constraint":
        _check_constraint(object)


def run_aspects(object, event):
    for aspect in Aspect.objects.filter(active=True):
        if _pointcut_matches(aspect.pointcut, object, event):
            _run_action(aspect, object, event)
