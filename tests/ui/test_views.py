from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from engine.models import Blob, Object, Proposal


def test_workspace_page_renders(client, demo_context):
    response = client.get(reverse("workspace"))

    assert response.status_code == 200


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


def test_submit_prompt_records_pending_proposal(client, demo_context):
    response = client.post(reverse("submit-prompt"), {"text": "le délai doit être facultatif"})

    assert response.status_code == 200
    proposal = Proposal.objects.get(operation="manual-prompt")
    assert proposal.decision == Proposal.Decision.PENDING
    assert b"manual-prompt" in response.content
