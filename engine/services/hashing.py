import hashlib
import json


def sha256_attributes(attributes: dict) -> str:
    """Empreinte stable d'un dict d'attributs (JSON canonique, clés triées)."""
    canonical = json.dumps(attributes, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
