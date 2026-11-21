import markdown as markdown_lib
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from engine.models import Blob, Event, Layer, Object, ObjectType, Proposal, ViewTemplate
from engine.services.blob import store_blob
from engine.services.create import create_object
from engine.services.errors import SchemaValidationError, VersionConflict
from engine.services.link import link_objects as link_objects_service
from engine.services.propose import record_proposal
from engine.services.render import apply_view_edit as apply_view_edit_service
from engine.services.render import render_view as render_view_service
from engine.services.typing import set_typing as set_typing_service
from engine.services.update import update_object as update_object_service
from ui.demo import demo_context


def _lookup(queryset, pk_value):
    """get(pk=...) qui renvoie None plutôt que de planter sur un pk vide/invalide."""
    if not pk_value:
        return None
    try:
        return queryset.get(pk=pk_value)
    except (queryset.model.DoesNotExist, ValidationError, ValueError):
        return None


def _object_list_context(space):
    objects = list(
        Object.objects.filter(space=space)
        .select_related("base_type", "current_version")
        .prefetch_related(
            "current_version__provenances__source_blob",
            "links_from__target__current_version",
            "typings__layer",
            "typings__type",
        )
        .order_by("-created_at")[:50]
    )
    for obj in objects:
        provenances = list(obj.current_version.provenances.all())
        obj.blob = provenances[0].source_blob if provenances else None
    layers = Layer.objects.filter(space=space).order_by("role")
    types = ObjectType.objects.filter(scope=ObjectType.Scope.BASE).order_by("name")
    return {"objects": objects, "layers": layers, "types": types}


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
        provenance = {"source_blob": blob, "operation": "import-fichier"}

        # Un dépôt du même nom dans cet espace est traité comme une nouvelle version
        # de l'objet existant, pas comme un objet distinct.
        existing = (
            Object.objects.filter(
                space=space,
                base_type=document_type,
                current_version__attributes__name=uploaded.name,
            )
            .select_related("current_version")
            .first()
        )
        existing_provenance = existing.current_version.provenances.first() if existing else None
        unchanged = (
            existing_provenance
            and existing_provenance.source_blob_id == blob.sha256
        )

        try:
            if unchanged:
                pass  # même contenu : rien à faire, pas de version inutile
            elif existing:
                update_object_service(
                    existing.id,
                    existing.current_version.number,
                    attributes,
                    author=user,
                    provenance=provenance,
                )
            else:
                create_object(space, document_type, attributes, author=user, provenance=provenance)
        except VersionConflict:
            errors.append(f"{uploaded.name} : modifié entre-temps, réessaie le dépôt.")
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


@require_POST
def link_object_view(request, object_id):
    space, layer, document_type, user = demo_context()
    errors = []
    try:
        source = Object.objects.get(pk=object_id, space=space)
    except Object.DoesNotExist:
        raise Http404

    nature = request.POST.get("nature", "").strip()
    target = _lookup(Object.objects.filter(space=space), request.POST.get("target"))

    if not nature:
        errors.append("indique une nature de lien.")
    elif not target:
        errors.append("choisis un objet cible.")
    else:
        link_objects_service(nature, source, target, layer=layer, author=user)

    context = _object_list_context(space)
    context["errors"] = errors
    return render(request, "ui/_object_list.html", context)


@require_POST
def type_object_view(request, object_id):
    space, layer, document_type, user = demo_context()
    errors = []
    try:
        obj = Object.objects.get(pk=object_id, space=space)
    except Object.DoesNotExist:
        raise Http404

    target_layer = _lookup(Layer.objects.filter(space=space), request.POST.get("layer"))
    object_type = _lookup(ObjectType.objects.filter(scope=ObjectType.Scope.BASE), request.POST.get("type"))

    if not target_layer:
        errors.append("choisis un calque.")
    elif not object_type:
        errors.append("choisis un type.")
    else:
        set_typing_service(obj, target_layer, object_type, author=user)

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


def _object_detail_context(obj, errors=None):
    views = []
    for view_template in ViewTemplate.objects.filter(applies_to=obj.base_type).order_by("name"):
        rendered = render_view_service(obj, view_template)
        if view_template.renderer == "markdown":
            rendered = {"html": markdown_lib.markdown(rendered["text"])}
        views.append({"template": view_template, "rendered": rendered})
    return {"object": obj, "views": views, "errors": errors or []}


@require_GET
def object_detail(request, object_id):
    space, layer, document_type, user = demo_context()
    try:
        obj = Object.objects.select_related("base_type", "current_version").get(pk=object_id, space=space)
    except Object.DoesNotExist:
        raise Http404
    context = _object_detail_context(obj)
    context["space"] = space
    return render(request, "ui/object_detail.html", context)


@require_POST
def apply_view_edit_view(request, object_id):
    space, layer, document_type, user = demo_context()
    try:
        obj = Object.objects.select_related("base_type", "current_version").get(pk=object_id, space=space)
    except Object.DoesNotExist:
        raise Http404

    expected_version = int(request.POST.get("expected_version", "0"))
    names = request.POST.getlist("field_name")
    types = request.POST.getlist("field_type")
    nullables = request.POST.getlist("field_nullable")
    fields = [
        {"name": name, "type": type_, "nullable": nullable == "true"}
        for name, type_, nullable in zip(names, types, nullables)
    ]

    errors = []
    try:
        apply_view_edit_service(object_id, expected_version, {"fields": fields}, author=user)
    except VersionConflict as exc:
        errors.append(f"conflit : version courante = {exc.current_version.number}, recharge et réessaie.")
    except SchemaValidationError as exc:
        errors.append("; ".join(exc.errors))

    obj.refresh_from_db()
    context = _object_detail_context(obj, errors)
    context["space"] = space
    return render(request, "ui/object_detail.html", context)
