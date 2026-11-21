import hashlib
from pathlib import Path

from django.conf import settings
from django.db import transaction

from engine.models import Blob


@transaction.atomic
def store_blob(content: bytes, mime_type: str) -> Blob:
    """Écrit un contenu sur disque, adressé par son empreinte. Dédupliqué par SHA-256 :

    un contenu déjà vu n'est ni réécrit ni dupliqué en base.
    """
    sha256 = hashlib.sha256(content).hexdigest()
    path = Path(settings.BLOB_STORAGE_ROOT) / sha256

    blob, created = Blob.objects.get_or_create(
        sha256=sha256,
        defaults={"mime_type": mime_type, "size": len(content), "path": str(path)},
    )
    if created or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return blob
