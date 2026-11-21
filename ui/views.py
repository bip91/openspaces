from django.http import FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from engine.models import Blob, Event, Object, Proposal
from engine.services.blob import store_blob
from engine.services.create import create_object
from engine.services.errors import SchemaValidationError, VersionConflict
from engine.services.propose import record_proposal
from engine.services.update import update_object as update_object_service
from ui.demo import demo_context


def _object_list_context(space):
    objects = list(
        Object.objects.filter(space=space)
        .select_related("base_type", "current_version")
        .prefetch_related("current_version__provenances__source_blob")
        .order_by("-created_at")[:50]
    )
    for obj in objects:
        provenances = list(obj.current_version.provenances.all())
        obj.blob = provenances[0].source_blob if provenances else None
    return {"objects": objects}


def _log_context(space):
    events = (
        Event.objects.filter(object__space=space)
        .select_related("object", "author")
        .order_by("-created_at")[:20]
    )
    proposals = Proposal.objects.order_by("-created_at")[:20]
    return {"events": events, "proposals": proposals}


@require_GET
def workspace(request):
    space, layer, document_type, user = demo_context()
    context = {"space": space}
    context.update(_object_list_context(space))
    context.update(_log_context(space))
    return render(request, "ui/workspace.html", context)


@require_GET
def object_list(request):
    space, layer, document_type, user = demo_context()
    return render(request, "ui/_object_list.html", _object_list_context(space))


@require_POST
def import_object(request):
    space, layer, document_type, user = demo_context()
    errors = []
    for uploaded in request.FILES.getlist("files"):
        content = uploaded.read()
        mime_type = uploaded.content_type or "application/octet-stream"
        blob = store_blob(content, mime_type)
        attributes = {
            "name": uploaded.name,
            "mime_type": mime_type,
            "size": uploaded.size,
        }
        try:
            create_object(
                space,
                document_type,
                attributes,
                author=user,
                provenance={"source_blob": blob, "operation": "import-fichier"},
            )
        except SchemaValidationError as exc:
            errors.append(f"{uploaded.name} : {'; '.join(exc.errors)}")

    context = _object_list_context(space)
    context["errors"] = errors
    return render(request, "ui/_object_list.html", context)


@require_POST
def update_object_view(request, object_id):
    space, layer, document_type, user = demo_context()
    errors = []
    try:
        obj = Object.objects.select_related("current_version").get(pk=object_id, space=space)
    except Object.DoesNotExist:
        raise Http404

    expected_version = int(request.POST.get("expected_version", "0"))
    attributes = dict(obj.current_version.attributes)
    attributes["name"] = request.POST.get("name", "").strip()

    # Cette édition ne change que le nom, pas le contenu : on reporte la provenance
    # (le lien vers le blob) sur la nouvelle version, sinon « voir » disparaît après
    # chaque renommage.
    previous_provenance = obj.current_version.provenances.first()
    provenance = None
    if previous_provenance and previous_provenance.source_blob_id:
        provenance = {"source_blob": previous_provenance.source_blob, "operation": "edition-nom"}

    try:
        update_object_service(object_id, expected_version, attributes, author=user, provenance=provenance)
    except VersionConflict as exc:
        errors.append(
            f"conflit sur « {obj.current_version.attributes.get('name')} » : "
            f"version courante = {exc.current_version.number}, recharge et réessaie."
        )
    except SchemaValidationError as exc:
        errors.append(f"{attributes['name']} : {'; '.join(exc.errors)}")

    context = _object_list_context(space)
    context["errors"] = errors
    return render(request, "ui/_object_list.html", context)


@require_GET
def blob_content(request, sha256):
    try:
        blob = Blob.objects.get(sha256=sha256)
    except Blob.DoesNotExist:
        raise Http404
    return FileResponse(open(blob.path, "rb"), content_type=blob.mime_type)


@require_GET
def event_log(request):
    space, layer, document_type, user = demo_context()
    return render(request, "ui/_event_log.html", _log_context(space))


@require_POST
def submit_prompt(request):
    space, layer, document_type, user = demo_context()
    text = request.POST.get("text", "").strip()
    if text:
        record_proposal("manual-prompt", {"text": text})
    return render(request, "ui/_event_log.html", _log_context(space))
