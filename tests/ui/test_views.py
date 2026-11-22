from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ai.schemas import ExtractedRequirement, ExtractionResult, LinkingResult, ProposedLink
from engine.models import Blob, Link, Object, Proposal, Typing
from engine.services.create import create_object


def test_workspace_page_renders(client, demo_context):
    response = client.get(reverse("workspace"))

    assert response.status_code == 200


def test_decide_proposal_accepts_extraction_and_chains_link_proposal(
    client, demo_context, demo_commande, monkeypatch
):
    from engine.services.propose import record_ai_proposal

    space, layer, document_type = demo_context
    proposal = record_ai_proposal(
        "extraction-exigences",
        {"space_id": str(space.id), "layer_id": str(layer.id), "text": "..."},
        {"requirements": [{"name": "délai obligatoire", "field": "delai", "rule": "obligatoire", "quote": "..."}]},
        "qwen2.5:1.5b",
        1000,
    )
    fake_links = LinkingResult(links=[ProposedLink(table_name="commande", nature="correspondence", confidence=0.9)])
    monkeypatch.setattr("ui.views.propose_links_ai", lambda exigence, candidates: fake_links)

    response = client.post(reverse("decide-proposal", args=[proposal.id]), {"decision": "accepted"})

    assert response.status_code == 200
    assert Object.objects.filter(current_version__attributes__name="délai obligatoire").exists()
    link_proposal = Proposal.objects.get(operation="proposition-liens")
    assert link_proposal.output["links"][0]["table_name"] == "commande"
    assert b"commande" in response.content


def test_object_browse_filters_by_type(client, demo_context, demo_commande, demo_table_type):
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("a.md", b"a")})

    response = client.get(reverse("object-browse"), {"type": str(demo_table_type.id)})

    assert b"commande" in response.content
    assert b"a.md" not in response.content


def test_object_browse_filters_by_dossier(client, demo_context, demo_commande, demo_user):
    space, layer, document_type = demo_context
    client.post(reverse("create-folder"), {"name": "mon-dossier"})
    folder = Object.objects.get(current_version__attributes__name="mon-dossier")
    client.post(reverse("link-object", args=[demo_commande.id]), {"target": folder.id, "nature": "classification"})
    create_object(space, demo_commande.base_type, {"name": "hors-dossier"}, author=demo_user)

    response = client.get(reverse("object-browse"), {"dossier": str(folder.id)})

    assert b"commande" in response.content
    assert b"hors-dossier" not in response.content


def test_object_browse_dynamic_dossier_filters_by_query_and_updates_both_ways(
    client, demo_context, demo_commande, demo_user, demo_folder_type
):
    from engine.services.update import update_object

    space, layer, document_type = demo_context
    agent_made = create_object(
        space, demo_commande.base_type, {"name": "exigence-agent"}, agent_name="qwen2.5:1.5b"
    )
    assert agent_made.current_version.validated is False  # créé par l'agent, pas encore relu

    folder = create_object(
        space, demo_folder_type, {"name": "dynamique", "query": {"validated": False}}, author=demo_user
    )

    response = client.get(reverse("object-browse"), {"dossier": str(folder.id)})
    assert b"exigence-agent" in response.content
    assert b"commande" not in response.content

    # Un humain réenregistre l'objet : validated passe à True, il sort du dossier
    # dynamique sans aucun changement de Link.
    update_object(agent_made.id, agent_made.current_version.number, agent_made.current_version.attributes, author=demo_user)

    response = client.get(reverse("object-browse"), {"dossier": str(folder.id)})
    assert b"exigence-agent" not in response.content


def test_object_browse_lists_objects_and_links(client, demo_context):
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("a.md", b"a")})
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("b.md", b"b")})
    source = Object.objects.get(current_version__attributes__name="a.md")
    target = Object.objects.get(current_version__attributes__name="b.md")
    client.post(reverse("link-object", args=[source.id]), {"target": target.id, "nature": "correspondence"})

    response = client.get(reverse("object-browse"))

    assert response.status_code == 200
    assert b"a.md" in response.content
    assert b"b.md" in response.content
    assert b"correspondence" in response.content


def test_object_detail_shows_the_three_views(client, demo_context, demo_commande):
    response = client.get(reverse("object-detail", args=[demo_commande.id]))

    assert response.status_code == 200
    assert b"erDiagram" in response.content
    assert b"<h1>commande</h1>" in response.content
    assert b"obligatoire" in response.content  # aper\xc3\xa7u Markdown


def test_object_detail_shows_outgoing_and_incoming_links(client, demo_context, demo_commande):
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("note.md", b"note")})
    note = Object.objects.get(current_version__attributes__name="note.md")
    client.post(reverse("link-object", args=[demo_commande.id]), {"target": note.id, "nature": "documente"})

    commande_response = client.get(reverse("object-detail", args=[demo_commande.id]))
    note_response = client.get(reverse("object-detail", args=[note.id]))

    assert b"documente" in commande_response.content
    assert b"note.md" in commande_response.content
    assert b"documente" in note_response.content
    assert b"commande" in note_response.content


def test_apply_view_edit_updates_fields_and_all_views(client, demo_context, demo_commande):
    response = client.post(
        reverse("apply-view-edit", args=[demo_commande.id]),
        {
            "expected_version": 1,
            "field_name": ["id", "delai"],
            "field_type": ["uuid", "integer"],
            "field_nullable": ["false", "true"],
        },
    )

    assert response.status_code == 200
    demo_commande.refresh_from_db()
    assert demo_commande.current_version.number == 2
    assert demo_commande.current_version.attributes["fields"][1]["nullable"] is True
    assert b"facultatif" in response.content


def test_apply_view_edit_reports_conflict(client, demo_context, demo_commande):
    client.post(
        reverse("apply-view-edit", args=[demo_commande.id]),
        {
            "expected_version": 1,
            "field_name": ["id", "delai"],
            "field_type": ["uuid", "integer"],
            "field_nullable": ["false", "false"],
        },
    )

    response = client.post(
        reverse("apply-view-edit", args=[demo_commande.id]),
        {
            "expected_version": 1,
            "field_name": ["id", "delai"],
            "field_type": ["uuid", "integer"],
            "field_nullable": ["false", "true"],
        },
    )

    assert response.status_code == 200
    assert b"conflit" in response.content
    demo_commande.refresh_from_db()
    assert demo_commande.current_version.number == 2


def test_import_object_creates_object_and_lists_it(client, demo_context):
    upload = SimpleUploadedFile("spec.md", b"# spec", content_type="text/markdown")

    response = client.post(reverse("import-object"), {"files": upload})

    assert response.status_code == 200
    assert Object.objects.filter(current_version__attributes__name="spec.md").exists()
    assert b"spec.md" in response.content


def test_import_object_stores_content_and_serves_it(client, demo_context, settings, tmp_path):
    settings.BLOB_STORAGE_ROOT = str(tmp_path)
    content = b"# spec de test"
    upload = SimpleUploadedFile("spec.md", content, content_type="text/markdown")

    client.post(reverse("import-object"), {"files": upload})

    blob = Blob.objects.get()
    assert blob.size == len(content)
    response = client.get(reverse("blob-content", args=[blob.sha256]))
    assert response.status_code == 200
    assert b"".join(response.streaming_content) == content


def test_import_object_with_same_name_creates_new_version(client, demo_context, settings, tmp_path):
    settings.BLOB_STORAGE_ROOT = str(tmp_path)
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("spec.md", b"v1")})

    response = client.post(reverse("import-object"), {"files": SimpleUploadedFile("spec.md", b"v2 plus long")})

    assert response.status_code == 200
    assert Object.objects.filter(current_version__attributes__name="spec.md").count() == 1
    obj = Object.objects.get(current_version__attributes__name="spec.md")
    assert obj.current_version.number == 2
    assert obj.current_version.attributes["size"] == len(b"v2 plus long")


def test_import_object_with_same_name_and_same_content_does_not_bump_version(client, demo_context, settings, tmp_path):
    settings.BLOB_STORAGE_ROOT = str(tmp_path)
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("spec.md", b"contenu identique")})

    client.post(reverse("import-object"), {"files": SimpleUploadedFile("spec.md", b"contenu identique")})

    obj = Object.objects.get(current_version__attributes__name="spec.md")
    assert obj.current_version.number == 1


def test_create_folder_creates_a_folder_object(client, demo_context):
    response = client.post(reverse("create-folder"), {"name": "mon-dossier"})

    assert response.status_code == 200
    assert Object.objects.filter(current_version__attributes__name="mon-dossier").exists()
    assert b"mon-dossier" in response.content


def test_create_folder_requires_a_name(client, demo_context):
    response = client.post(reverse("create-folder"), {"name": ""})

    assert response.status_code == 200
    assert not Object.objects.filter(base_type__name="Dossier").exists()
    assert b"dossier" in response.content


def test_classifying_an_object_into_a_folder_shows_in_its_links(client, demo_context, demo_commande):
    client.post(reverse("create-folder"), {"name": "mon-dossier"})
    folder = Object.objects.get(current_version__attributes__name="mon-dossier")

    client.post(reverse("link-object", args=[demo_commande.id]), {"target": folder.id, "nature": "classification"})
    response = client.get(reverse("object-detail", args=[demo_commande.id]))

    assert b"classification" in response.content
    assert b"mon-dossier" in response.content


def test_update_object_renames_it(client, demo_context, settings, tmp_path):
    settings.BLOB_STORAGE_ROOT = str(tmp_path)
    upload = SimpleUploadedFile("spec.md", b"# spec", content_type="text/markdown")
    client.post(reverse("import-object"), {"files": upload})
    obj = Object.objects.get(current_version__attributes__name="spec.md")

    response = client.post(
        reverse("update-object", args=[obj.id]),
        {"expected_version": 1, "name": "spec-renommee.md"},
    )

    assert response.status_code == 200
    obj.refresh_from_db()
    assert obj.current_version.number == 2
    assert obj.current_version.attributes["name"] == "spec-renommee.md"
    assert b"spec-renommee.md" in response.content


def test_update_object_keeps_blob_link_after_rename(client, demo_context, settings, tmp_path):
    settings.BLOB_STORAGE_ROOT = str(tmp_path)
    upload = SimpleUploadedFile("spec.md", b"# spec", content_type="text/markdown")
    client.post(reverse("import-object"), {"files": upload})
    obj = Object.objects.get(current_version__attributes__name="spec.md")
    blob = Blob.objects.get()

    response = client.post(
        reverse("update-object", args=[obj.id]),
        {"expected_version": 1, "name": "spec-renommee.md"},
    )

    assert response.status_code == 200
    assert f'/blobs/{blob.sha256}/'.encode() in response.content
    obj.refresh_from_db()
    assert obj.current_version.provenances.get().source_blob == blob


def test_update_object_reports_conflict_without_mutating(client, demo_context, settings, tmp_path):
    settings.BLOB_STORAGE_ROOT = str(tmp_path)
    upload = SimpleUploadedFile("spec.md", b"# spec", content_type="text/markdown")
    client.post(reverse("import-object"), {"files": upload})
    obj = Object.objects.get(current_version__attributes__name="spec.md")
    client.post(reverse("update-object", args=[obj.id]), {"expected_version": 1, "name": "v2"})

    response = client.post(
        reverse("update-object", args=[obj.id]),
        {"expected_version": 1, "name": "v3-perdue"},
    )

    assert response.status_code == 200
    assert b"conflit" in response.content
    obj.refresh_from_db()
    assert obj.current_version.number == 2
    assert obj.current_version.attributes["name"] == "v2"


def test_link_object_creates_active_link_and_shows_it(client, demo_context):
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("a.md", b"a")})
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("b.md", b"b")})
    source = Object.objects.get(current_version__attributes__name="a.md")
    target = Object.objects.get(current_version__attributes__name="b.md")

    response = client.post(
        reverse("link-object", args=[source.id]),
        {"target": target.id, "nature": "correspondence"},
    )

    assert response.status_code == 200
    link = Link.objects.get(source=source, target=target)
    assert link.nature == "correspondence"
    assert link.status == Link.Status.ACTIVE
    assert b"correspondence" in response.content
    assert b"b.md" in response.content


def test_link_object_requires_nature(client, demo_context):
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("a.md", b"a")})
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("b.md", b"b")})
    source = Object.objects.get(current_version__attributes__name="a.md")
    target = Object.objects.get(current_version__attributes__name="b.md")

    response = client.post(reverse("link-object", args=[source.id]), {"target": target.id, "nature": ""})

    assert response.status_code == 200
    assert not Link.objects.filter(source=source, target=target).exists()
    assert b"nature" in response.content


def test_link_object_requires_target(client, demo_context):
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("a.md", b"a")})
    source = Object.objects.get(current_version__attributes__name="a.md")

    response = client.post(reverse("link-object", args=[source.id]), {"target": "", "nature": "correspondence"})

    assert response.status_code == 200
    assert not Link.objects.filter(source=source).exists()
    assert b"cible" in response.content


def test_type_object_requires_type(client, demo_context, demo_layer_fonctionnel):
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("a.md", b"a")})
    obj = Object.objects.get(current_version__attributes__name="a.md")

    response = client.post(
        reverse("type-object", args=[obj.id]),
        {"layer": demo_layer_fonctionnel.id, "type": ""},
    )

    assert response.status_code == 200
    assert not Typing.objects.filter(object=obj).exists()
    assert b"type" in response.content


def test_type_object_adds_typing_and_shows_it(client, demo_context, demo_layer_fonctionnel, demo_second_type):
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("a.md", b"a")})
    obj = Object.objects.get(current_version__attributes__name="a.md")

    response = client.post(
        reverse("type-object", args=[obj.id]),
        {"layer": demo_layer_fonctionnel.id, "type": demo_second_type.id},
    )

    assert response.status_code == 200
    assert Typing.objects.filter(object=obj, layer=demo_layer_fonctionnel, type=demo_second_type).exists()
    assert b"fonctionnel" in response.content
    assert b"Exigence" in response.content


def test_type_object_requires_layer(client, demo_context, demo_second_type):
    client.post(reverse("import-object"), {"files": SimpleUploadedFile("a.md", b"a")})
    obj = Object.objects.get(current_version__attributes__name="a.md")

    response = client.post(reverse("type-object", args=[obj.id]), {"layer": "", "type": demo_second_type.id})

    assert response.status_code == 200
    assert not Typing.objects.filter(object=obj).exists()
    assert b"calque" in response.content


def test_submit_prompt_extracts_requirements_into_a_pending_proposal(client, demo_context, monkeypatch):
    fake_result = ExtractionResult(
        requirements=[
            ExtractedRequirement(
                name="délai obligatoire", field="delai", rule="obligatoire", quote="le délai doit être facultatif"
            )
        ]
    )
    monkeypatch.setattr("ui.views.extract_requirements", lambda text: fake_result)

    response = client.post(reverse("submit-prompt"), {"text": "le délai doit être facultatif"})

    assert response.status_code == 200
    proposal = Proposal.objects.get(operation="extraction-exigences")
    assert proposal.decision == Proposal.Decision.PENDING
    assert proposal.output["requirements"][0]["name"] == "délai obligatoire"
    assert b"d\xc3\xa9lai obligatoire" in response.content
    assert b"accepter" in response.content
