import time
from urllib.parse import urlencode

import markdown as markdown_lib
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
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
from ui.demo import (
    DEMO_FOLDER_TYPE_NAME,
    DEMO_TABLE_TYPE_NAME,
    DOSSIER_PARENT_NATURE,
    FOLDER_LINK_NATURE,
    demo_context,
)


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


def _dossier_tree(space, folder_type):
    """Dossiers en arbre pour l'affichage : racines, chacune avec ses enfants
    directs (nature `sous-dossier-de`) sous `.children` — navigation seulement,
    jamais l'appartenance (même principe que Lightroom Collection Set/
    Collection). Un dossier porte `.is_dynamic` si son appartenance est
    calculée (`query`) plutôt que posée par un Link de classification."""
    dossiers = list(
        Object.objects.filter(space=space, base_type=folder_type).select_related("current_version")
    )
    parent_by_child_id = dict(
        Link.objects.filter(source__in=dossiers, nature=DOSSIER_PARENT_NATURE).values_list(
            "source_id", "target_id"
        )
    )
    children_by_parent_id = {}
    roots = []
    for dossier in dossiers:
        dossier.is_dynamic = bool(dossier.current_version.attributes.get("query"))
        parent_id = parent_by_child_id.get(dossier.id)
        if parent_id:
            children_by_parent_id.setdefault(parent_id, []).append(dossier)
        else:
            roots.append(dossier)

    def _name(obj):
        return obj.current_version.attributes.get("name", "")

    for root in roots:
        root.children = sorted(children_by_parent_id.get(root.id, []), key=_name)
        # Un dossier dynamique cache sous un parent fermé par défaut ne se
        # découvre pas — on déplie d'office un parent qui en contient un.
        root.has_dynamic_child = any(child.is_dynamic for child in root.children)
    return sorted(roots, key=_name)


def _browse_queryset(space, selected_type, selected_dossier):
    """Objets d'un espace filtrés par type et/ou dossier (statique ou
    dynamique) — logique partagée entre la liste et l'aperçu, pour que les
    flèches précédent/suivant circulent dans le même ensemble que la liste."""
    objects = Object.objects.filter(space=space).select_related("base_type", "current_version")

    if selected_type:
        objects = objects.filter(base_type_id=selected_type)

    if selected_dossier:
        dossier_object = Object.objects.filter(pk=selected_dossier).select_related("current_version").first()
        query = dossier_object.current_version.attributes.get("query") if dossier_object else None
        if query:
            # Dossier dynamique : l'appartenance est calculée, pas posée par un Link.
            # Convention reprise de Django, pas inventée : `filter`/`exclude`, chemins
            # ORM classiques en clé (ex. "current_version__validated",
            # "links_from__nature") — couvre aussi bien l'égalité que l'absence
            # (un Table « non classée » = exclude sur un Link de classification).
            # « Déplacer » un objet hors d'un dossier dynamique revient à changer
            # l'attribut/la relation concernée (ex. update_object valide une
            # Version, donc validated devient True).
            objects = objects.filter(**query.get("filter", {})).exclude(**query.get("exclude", {}))
        else:
            objects = objects.filter(links_from__nature=FOLDER_LINK_NATURE, links_from__target_id=selected_dossier)

    return objects.order_by("base_type__name", "-created_at")


def _tree_context(space):
    folder_type = ObjectType.objects.filter(name=DEMO_FOLDER_TYPE_NAME, scope=ObjectType.Scope.BASE).first()
    dossiers = _dossier_tree(space, folder_type) if folder_type else []
    types = ObjectType.objects.filter(scope=ObjectType.Scope.BASE).order_by("name")
    return {"types": types, "dossiers": dossiers}


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _browse_shell_response(request, space, content_template, content_context, content_url):
    """Rend la coquille complète (arbre + panneau) avec ce contenu déjà
    inséré, pour toute visite qui n'est pas un échange htmx — rechargement,
    retour/suivant du navigateur, ouverture dans un nouvel onglet. Sans ça,
    les URL poussées par hx-push-url pour le contenu/l'aperçu (qui ne
    rendent normalement qu'un fragment, pas la page) renvoient un fragment
    nu si on y accède directement : l'arbre disparaît — pas un style
    manquant, une vraie page cassée."""
    context = {"space": space, **_tree_context(space)}
    context["selected_type"] = content_context.get("selected_type", "")
    context["selected_dossier"] = content_context.get("selected_dossier", "")
    context["initial_body"] = render_to_string(content_template, content_context, request=request)
    context["content_url"] = content_url
    return render(request, "ui/object_browse.html", context)


@require_GET
def object_browse(request):
    space, layer, document_type, user = demo_context()
    selected_type = request.GET.get("type", "")
    selected_dossier = request.GET.get("dossier", "")
    return render(
        request,
        "ui/object_browse.html",
        {
            "space": space,
            **_tree_context(space),
            "selected_type": selected_type,
            "selected_dossier": selected_dossier,
            "content_url": f"{reverse('object-content')}?{urlencode({'type': selected_type, 'dossier': selected_dossier})}",
        },
    )


@require_GET
def object_content(request):
    """Panneau de contenu, mode liste — chargé par htmx au démarrage de la
    page et à chaque sélection dans l'arbre (clic sur un dossier, ou filtre
    par type)."""
    space, layer, document_type, user = demo_context()
    selected_type = request.GET.get("type", "")
    selected_dossier = request.GET.get("dossier", "")
    objects = _browse_queryset(space, selected_type, selected_dossier)

    dossier_name = ""
    if selected_dossier:
        dossier_object = Object.objects.filter(pk=selected_dossier).select_related("current_version").first()
        dossier_name = dossier_object.current_version.attributes.get("name", "") if dossier_object else ""

    content_context = {
        "objects": objects,
        "selected_type": selected_type,
        "selected_dossier": selected_dossier,
        "dossier_name": dossier_name,
    }
    if _is_htmx(request):
        return render(request, "ui/_object_content.html", content_context)

    content_url = f"{reverse('object-content')}?{urlencode({'type': selected_type, 'dossier': selected_dossier})}"
    return _browse_shell_response(request, space, "ui/_object_content.html", content_context, content_url)


def _applicable_views(obj, selected_view_id):
    """Vues qui s'appliquent au type de cet objet, rendues — reprend
    `_object_detail_context`. `selected_view_id` choisit celle à afficher
    (la première par défaut, ordre alphabétique comme ailleurs)."""
    views = []
    for view_template in ViewTemplate.objects.filter(applies_to=obj.base_type).order_by("name"):
        rendered = render_view_service(obj, view_template)
        if view_template.renderer == "markdown":
            rendered = {"html": markdown_lib.markdown(rendered["text"])}
        views.append({"template": view_template, "rendered": rendered})
    selected = None
    if selected_view_id:
        selected = next((v for v in views if str(v["template"].id) == selected_view_id), None)
    return views, selected or (views[0] if views else None)


@require_GET
def object_preview(request, object_id):
    """Panneau de contenu, mode aperçu — nom, version par défaut, vue
    sélectionnée, et précédent/suivant dans la même liste que le mode liste
    (même filtre type/dossier, transmis en query string)."""
    space, layer, document_type, user = demo_context()
    try:
        obj = Object.objects.select_related("base_type", "current_version").get(pk=object_id, space=space)
    except Object.DoesNotExist:
        raise Http404

    selected_type = request.GET.get("type", "")
    selected_dossier = request.GET.get("dossier", "")
    ids = list(_browse_queryset(space, selected_type, selected_dossier).values_list("id", flat=True))
    try:
        position = ids.index(obj.id)
    except ValueError:
        position = None
    prev_id = ids[position - 1] if position is not None and position > 0 else None
    next_id = ids[position + 1] if position is not None and position + 1 < len(ids) else None

    views, selected_view = _applicable_views(obj, request.GET.get("view", ""))

    folder_type = ObjectType.objects.filter(name=DEMO_FOLDER_TYPE_NAME, scope=ObjectType.Scope.BASE).first()
    classifiable_dossiers = (
        [d for d in Object.objects.filter(space=space, base_type=folder_type).select_related("current_version")
         if not d.current_version.attributes.get("query")]
        if folder_type
        else []
    )

    links_out = list(obj.links_from.select_related("target__current_version", "layer").order_by("-created_at"))
    links_in = list(obj.links_to.select_related("source__current_version", "layer").order_by("-created_at"))

    preview_context = {
        "object": obj,
        "views": views,
        "selected_view": selected_view,
        "links_out": links_out,
        "links_in": links_in,
        "classifiable_dossiers": classifiable_dossiers,
        "selected_type": selected_type,
        "selected_dossier": selected_dossier,
        "prev_id": prev_id,
        "next_id": next_id,
        "message": request.GET.get("message", ""),
    }
    if _is_htmx(request):
        return render(request, "ui/_object_preview.html", preview_context)

    params = {"type": selected_type, "dossier": selected_dossier}
    if request.GET.get("view"):
        params["view"] = request.GET["view"]
    content_url = f"{reverse('object-preview', args=[obj.id])}?{urlencode(params)}"
    return _browse_shell_response(request, space, "ui/_object_preview.html", preview_context, content_url)


@require_POST
def classify_object_view(request, object_id):
    """Classe l'objet dans un dossier choisi — un Link de classification de
    plus, comme n'importe quel autre lien (`link_objects_service`), rien de
    spécifique. Les dossiers dynamiques n'apparaissent pas dans le choix :
    leur appartenance se calcule, elle ne se pose pas."""
    space, layer, document_type, user = demo_context()
    try:
        obj = Object.objects.select_related("base_type", "current_version").get(pk=object_id, space=space)
    except Object.DoesNotExist:
        raise Http404

    target = _lookup(Object.objects.filter(space=space), request.POST.get("dossier"))
    message = ""
    if target:
        link_objects_service(FOLDER_LINK_NATURE, obj, target, layer=layer, author=user)
        message = f"Classé dans « {target.current_version.attributes.get('name', '')} »."
    else:
        message = "Choisis un dossier."

    selected_type = request.POST.get("type", "")
    selected_dossier = request.POST.get("dossier_filter", "")
    query = urlencode({"type": selected_type, "dossier": selected_dossier, "message": message})
    return HttpResponseRedirect(f"{reverse('object-preview', args=[obj.id])}?{query}")


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
