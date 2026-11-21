from pathlib import Path

from engine.models import Blob
from engine.services.blob import store_blob


def test_store_blob_writes_file_and_creates_row(db, settings, tmp_path):
    settings.BLOB_STORAGE_ROOT = str(tmp_path)
    content = b"contenu du fichier"

    blob = store_blob(content, "text/plain")

    assert Blob.objects.filter(pk=blob.sha256).exists()
    assert blob.size == len(content)
    assert blob.mime_type == "text/plain"
    assert Path(blob.path).read_bytes() == content


def test_store_blob_is_deduplicated_by_hash(db, settings, tmp_path):
    settings.BLOB_STORAGE_ROOT = str(tmp_path)

    first = store_blob(b"identique", "text/plain")
    second = store_blob(b"identique", "text/plain")

    assert first.sha256 == second.sha256
    assert Blob.objects.filter(sha256=first.sha256).count() == 1
