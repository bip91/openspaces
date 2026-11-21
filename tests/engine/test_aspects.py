import pytest

from engine.models import Divergence, Event, Version
from engine.services.create import create_object
from engine.services.link import link_objects
from engine.services.render import apply_view_edit


@pytest.fixture
def delai_obligatoire(space, exigence_type, user):
    return create_object(
        space, exigence_type, {"name": "délai obligatoire", "field": "delai", "rule": "obligatoire"}, author=user
    )


@pytest.fixture
def linked_commande(commande, delai_obligatoire, user):
    link_objects("correspondence", delai_obligatoire, commande, author=user)
    return commande


def test_notify_aspect_notifies_linked_exigence_when_table_updates(
    linked_commande, delai_obligatoire, notify_aspect, user
):
    apply_view_edit(
        linked_commande.id,
        1,
        {"fields": [{"name": "id", "type": "uuid", "nullable": False}, {"name": "delai", "type": "integer", "nullable": True}]},
        author=user,
    )

    assert Event.objects.filter(object=delai_obligatoire, nature="notified").exists()


def test_notify_aspect_does_not_fire_on_creation(space, table_type, notify_aspect, user):
    obj = create_object(space, table_type, {"name": "autre_table", "fields": []}, author=user)

    assert not Event.objects.filter(object=obj, nature="notified").exists()


def test_notify_aspect_ignores_unlinked_table(space, table_type, notify_aspect, user):
    obj = create_object(space, table_type, {"name": "isolee", "fields": []}, author=user)

    apply_view_edit(obj.id, 1, {"fields": [{"name": "x", "type": "string", "nullable": True}]}, author=user)

    assert not Event.objects.filter(nature="notified").exists()


def test_check_constraint_creates_divergence_when_field_becomes_inconsistent(
    linked_commande, delai_obligatoire, check_constraint_aspect, user
):
    apply_view_edit(
        linked_commande.id,
        1,
        {"fields": [{"name": "id", "type": "uuid", "nullable": False}, {"name": "delai", "type": "integer", "nullable": True}]},
        author=user,
    )

    divergence = Divergence.objects.get(status=Divergence.Status.OPEN)
    assert delai_obligatoire in divergence.related_objects.all()
    assert linked_commande in divergence.related_objects.all()


def test_check_constraint_does_not_duplicate_open_divergence(
    linked_commande, delai_obligatoire, check_constraint_aspect, user
):
    apply_view_edit(
        linked_commande.id,
        1,
        {"fields": [{"name": "id", "type": "uuid", "nullable": False}, {"name": "delai", "type": "integer", "nullable": True}]},
        author=user,
    )
    apply_view_edit(
        linked_commande.id,
        2,
        {"name": "commande", "fields": [{"name": "id", "type": "uuid", "nullable": False}, {"name": "delai", "type": "integer", "nullable": True}]},
        author=user,
    )

    assert Divergence.objects.filter(status=Divergence.Status.OPEN).count() == 1


def test_check_constraint_resolves_divergence_once_consistent_again(
    linked_commande, delai_obligatoire, check_constraint_aspect, user
):
    apply_view_edit(
        linked_commande.id,
        1,
        {"fields": [{"name": "id", "type": "uuid", "nullable": False}, {"name": "delai", "type": "integer", "nullable": True}]},
        author=user,
    )
    apply_view_edit(
        linked_commande.id,
        2,
        {"fields": [{"name": "id", "type": "uuid", "nullable": False}, {"name": "delai", "type": "integer", "nullable": False}]},
        author=user,
    )

    assert not Divergence.objects.filter(status=Divergence.Status.OPEN).exists()
    assert Divergence.objects.filter(status=Divergence.Status.RESOLVED).exists()


def test_check_constraint_triggers_on_link_creation(commande, delai_obligatoire, check_constraint_aspect, user):
    apply_view_edit(
        commande.id,
        1,
        {"fields": [{"name": "id", "type": "uuid", "nullable": False}, {"name": "delai", "type": "integer", "nullable": True}]},
        author=user,
    )

    assert not Divergence.objects.exists()  # pas encore liés

    link_objects("correspondence", delai_obligatoire, commande, author=user)

    assert Divergence.objects.filter(status=Divergence.Status.OPEN).exists()


def test_version_requires_author_xor_agent_name(commande):
    """Aspect « attribution » : déjà garanti par la contrainte DB du lot 1."""
    from django.db import IntegrityError, transaction

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Version.objects.create(
                object=commande,
                number=99,
                attributes={"name": "x"},
                sha256="0" * 64,
                nature=Version.Nature.HUMAN,
                author=None,
                agent_name=None,
            )
