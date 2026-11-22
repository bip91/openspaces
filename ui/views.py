import time

import markdown as markdown_lib
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from ai.extraction import extract_requirements
from ai.linking import propose_links as propose_links_ai
from bus.core import call as bus_call
from bus.models import CallLog
from bus.registry import CAPABILITIES, CLIENTS
from engine.models import Blob, Divergence, Event, Layer, Link, Object, ObjectType, Proposal, ViewTemplate
from engine.services.blob import store_blob
from engine.services.create import create_object
from engine.services.errors import SchemaValidationError, VersionConflict
from engine.services.link import link_objects as link_objects_service
from engine.services.propose import decide_proposal as decide_proposal_service
from engine.services.propose import record_ai_proposal
from engine.services.render import apply_view_edit as apply_view_edit_service
from engine.services.render import render_view as render_view_service
from engine.services.typing import set_typing as set_typing_service
from engine.services.update import update_object as update_object_service
from ui.demo import DEMO_FOLDER_TYPE_NAME, DEMO_TABLE_TYPE_NAME, FOLDER_LINK_NATURE, demo_context


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
            "divergences",
        )
        .order_by("-created_at")[:50]
    )
    for obj in objects:
        provenances = list(obj.current_version.provenances.all())
        obj.blob = provenances[0].source_blob if provenances else None
        obj.open_divergences = [d for d in obj.divergences.all() if d.status == Divergence.Status.OPEN]
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
    divergences = (
        Divergence.objects.filter(space=space, status=Divergence.Status.OPEN)
        .prefetch_related("related_objects__current_version")
        .order_by("-created_at")
    )
    return {"events": events, "proposals": proposals, "divergences": divergences}


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


@require_GET
def object_browse(request):
    space, layer, document_type, user = demo_context()
    objects = Object.objects.filter(space=space).select_related("base_type", "current_version")

    selected_type = request.GET.get("type", "")
    if selected_type:
        objects = objects.filter(base_type_id=selected_type)

    selected_dossier = request.GET.get("dossier", "")
    if selected_dossier:
        dossier_object = Object.objects.filter(pk=selected_dossier).select_related("current_version").first()
        query = dossier_object.current_version.attributes.get("query") if dossier_object else None
        if query:
            # Dossier dynamique : l'appartenance est calculée (égalité sur des
            # champs de Version), pas posée par un Link — « déplacer » un objet
            # hors de ce dossier revient alors à changer l'attribut concerné
            # (ex. update_object valide une Version, donc validated devient True).
            objects = objects.filter(**{f"current_version__{field}": value for field, value in query.items()})
        else:
            objects = objects.filter(links_from__nature=FOLDER_LINK_NATURE, links_from__target_id=selected_dossier)

    objects = objects.order_by("base_type__name", "-created_at")

    links = (
        Link.objects.filter(source__space=space)
        .select_related("source__current_version", "target__current_version", "layer")
        .order_by("-created_at")
    )

    folder_type = ObjectType.objects.filter(name=DEMO_FOLDER_TYPE_NAME, scope=ObjectType.Scope.BASE).first()
    dossiers = (
        Object.objects.filter(space=space, base_type=folder_type).select_related("current_version")
        if folder_type
        else Object.objects.none()
    )
    types = ObjectType.objects.filter(scope=ObjectType.Scope.BASE).order_by("name")

    return render(
        request,
        "ui/object_browse.html",
        {
            "space": space,
            "objects": objects,
            "links": links,
            "types": types,
            "dossiers": dossiers,
            "selected_type": selected_type,
            "selected_dossier": selected_dossier,
        },
    )


def _bus_log_context():
    return {
        "entries": CallLog.objects.order_by("-created_at")[:20],
        "clients": sorted(CLIENTS),
        "verbs": sorted(CAPABILITIES) + ["verbe-inexistant"],
    }


@require_GET
def bus_page(request):
    space, layer, document_type, user = demo_context()
    context = _bus_log_context()
    context["space"] = space
    return render(request, "ui/bus.html", context)


@require_GET
def bus_log(request):
    return render(request, "ui/_bus_log.html", _bus_log_context())


@require_POST
def trigger_bus_call(request):
    space, layer, document_type, user = demo_context()
    client_id = request.POST.get("client_id", "harnais-web")
    verb = request.POST.get("verb", "create_object")
    name = request.POST.get("name", "").strip() or "objet-demo-bus"

    if verb == "create_object":
        table_type = ObjectType.objects.get(name=DEMO_TABLE_TYPE_NAME, scope=ObjectType.Scope.BASE)
        payload = {
            "space_id": str(space.id),
            "type_id": str(table_type.id),
            "attributes": {"name": name},
            "author_username": user.username,
        }
    else:
        payload = {}

    bus_call(verb, client_id, payload)
    return render(request, "ui/_bus_log.html", _bus_log_context())


@require_POST
def create_folder(request):
    """Crée un objet Dossier (classement multi-valué, pas un sous-espace —
    voir CLAUDE.md). Le classement lui-même se fait avec le lien générique
    existant (``link-object``), aucun code dédié n'est nécessaire pour ça."""
    space, layer, document_type, user = demo_context()
    name = request.POST.get("name", "").strip()
    errors = []
    if name:
        folder_type = ObjectType.objects.get(name=DEMO_FOLDER_TYPE_NAME, scope=ObjectType.Scope.BASE)
        create_object(space, folder_type, {"name": name}, author=user)
    else:
        errors.append("indique un nom de dossier.")

    context = _object_list_context(space)
    context["errors"] = errors
    return render(request, "ui/_object_list.html", context)


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
    """Extraction d'exigences (lot 4) depuis un texte collé (ex. un mail
    fonctionnel). Journalise une Proposal PENDING ; rien n'est créé tant
    qu'elle n'est pas décidée (voir ``decide_proposal_view``)."""
    space, layer, document_type, user = demo_context()
    text = request.POST.get("text", "").strip()
    if text:
        started = time.perf_counter()
        result = extract_requirements(text)
        duration_ms = int((time.perf_counter() - started) * 1000)
        record_ai_proposal(
            "extraction-exigences",
            {"space_id": str(space.id), "layer_id": str(layer.id), "text": text},
            result.model_dump(),
            settings.AI_MODEL_NAME,
            duration_ms,
        )
    return render(request, "ui/_event_log.html", _log_context(space))


@require_POST
def decide_proposal_view(request, proposal_id):
    """Décide d'une Proposal (accepter/rejeter). Si c'est une extraction
    acceptée, enchaîne automatiquement une proposition de liens par
    Exigence créée contre les Table du space — « exigences extraites,
    liens proposés » sans étape manuelle supplémentaire."""
    space, layer, document_type, user = demo_context()
    decision = request.POST.get("decision", "")
    errors = []

    try:
        proposal = Proposal.objects.get(pk=proposal_id)
    except Proposal.DoesNotExist:
        raise Http404

    try:
        result = decide_proposal_service(proposal.id, decision, author=user)
    except ValueError as exc:
        errors.append(str(exc))
        result = {"created": []}

    if proposal.operation == "extraction-exigences" and decision == Proposal.Decision.ACCEPTED:
        table_type = ObjectType.objects.get(name=DEMO_TABLE_TYPE_NAME, scope=ObjectType.Scope.BASE)
        candidate_tables = [
            {
                "name": obj.current_version.attributes.get("name"),
                "fields": obj.current_version.attributes.get("fields", []),
            }
            for obj in Object.objects.filter(space=space, base_type=table_type).select_related("current_version")
        ]
        for exigence in result["created"]:
            started = time.perf_counter()
            linking_result = propose_links_ai(exigence.current_version.attributes, candidate_tables)
            duration_ms = int((time.perf_counter() - started) * 1000)
            record_ai_proposal(
                "proposition-liens",
                {
                    "space_id": str(space.id),
                    "layer_id": str(layer.id),
                    "exigence_id": str(exigence.id),
                    "exigence_attributes": exigence.current_version.attributes,
                },
                linking_result.model_dump(),
                settings.AI_MODEL_NAME,
                duration_ms,
            )

    context = _log_context(space)
    context["errors"] = errors
    return render(request, "ui/_event_log.html", context)


def _object_detail_context(obj, errors=None):
    obj.open_divergences = list(obj.divergences.filter(status=Divergence.Status.OPEN))
    links_out = list(obj.links_from.select_related("target__current_version", "layer").order_by("-created_at"))
    links_in = list(obj.links_to.select_related("source__current_version", "layer").order_by("-created_at"))
    views = []
    for view_template in ViewTemplate.objects.filter(applies_to=obj.base_type).order_by("name"):
        rendered = render_view_service(obj, view_template)
        if view_template.renderer == "markdown":
            rendered = {"html": markdown_lib.markdown(rendered["text"])}
        views.append({"template": view_template, "rendered": rendered})
    return {"object": obj, "views": views, "links_out": links_out, "links_in": links_in, "errors": errors or []}


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
