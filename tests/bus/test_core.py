from dataclasses import replace

from bus.core import call
from bus.models import CallLog
from bus.registry import CAPABILITIES
from engine.models import Object


def test_registry_lists_the_six_known_verbs():
    assert set(CAPABILITIES) == {
        "create_object",
        "update_object",
        "link_objects",
        "set_typing",
        "render_view",
        "apply_view_edit",
    }
    assert CAPABILITIES["create_object"].effect == "write"
    assert CAPABILITIES["render_view"].effect == "read"
    assert all(capability.reversible for capability in CAPABILITIES.values())


def test_allowed_call_creates_the_object_and_logs_it(space, table_type, user):
    result = call(
        "create_object",
        "harnais-web",
        {
            "space_id": str(space.id),
            "type_id": str(table_type.id),
            "attributes": {"name": "commande"},
            "author_username": user.username,
        },
    )

    assert Object.objects.filter(pk=result["id"]).exists()
    entry = CallLog.objects.get(verb="create_object")
    assert entry.client_id == "harnais-web"
    assert entry.allowed is True
    assert entry.output["id"] == result["id"]


def test_client_without_the_right_effect_is_refused(space, table_type):
    result = call(
        "create_object",
        "lecteur-demo",
        {"space_id": str(space.id), "type_id": str(table_type.id), "attributes": {"name": "commande"}},
    )

    assert result == {"error": "forbidden"}
    assert not Object.objects.filter(current_version__attributes__name="commande").exists()
    entry = CallLog.objects.get(verb="create_object")
    assert entry.allowed is False
    assert entry.error == "forbidden"


def test_unknown_verb_is_refused_and_logged(db):
    result = call("verbe-inexistant", "harnais-web", {})

    assert result == {"error": "unknown_verb"}
    entry = CallLog.objects.get(verb="verbe-inexistant")
    assert entry.allowed is False


def test_irreversible_capability_requires_confirmation(monkeypatch, space, table_type, user):
    irreversible = replace(CAPABILITIES["create_object"], reversible=False)
    monkeypatch.setitem(CAPABILITIES, "create_object", irreversible)
    payload = {
        "space_id": str(space.id),
        "type_id": str(table_type.id),
        "attributes": {"name": "commande"},
        "author_username": user.username,
    }

    refused = call("create_object", "harnais-web", payload)
    assert refused == {"error": "confirmation_required"}
    assert not Object.objects.filter(current_version__attributes__name="commande").exists()

    accepted = call("create_object", "harnais-web", payload, confirmed=True)
    assert Object.objects.filter(pk=accepted["id"]).exists()
    assert CallLog.objects.get(verb="create_object", allowed=True).confirmed is True


def test_invalid_payload_is_refused_with_schema_errors(space, table_type):
    result = call("create_object", "harnais-web", {"space_id": str(space.id), "type_id": str(table_type.id)})

    assert result["error"] == "invalid_input"
    assert result["errors"]
    entry = CallLog.objects.get(verb="create_object")
    assert entry.allowed is False
