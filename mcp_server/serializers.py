def serialize_version(version):
    return {
        "id": str(version.id),
        "object_id": str(version.object_id),
        "number": version.number,
        "attributes": version.attributes,
        "sha256": version.sha256,
        "nature": version.nature,
        "validated": version.validated,
    }


def serialize_object(object):
    return {
        "id": str(object.id),
        "space_id": str(object.space_id),
        "base_type_id": str(object.base_type_id),
        "version": serialize_version(object.current_version),
    }


def serialize_link(link):
    return {
        "id": str(link.id),
        "nature": link.nature,
        "source_id": str(link.source_id),
        "target_id": str(link.target_id),
        "layer_id": str(link.layer_id) if link.layer_id else None,
        "status": link.status,
    }


def serialize_typing(typing):
    return {
        "id": str(typing.id),
        "object_id": str(typing.object_id),
        "layer_id": str(typing.layer_id),
        "type_id": str(typing.type_id),
    }
