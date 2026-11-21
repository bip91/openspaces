"""Modèle de données du moteur (lot 1).

Les identifiants suivent le glossaire du CLAUDE.md. Les méta-objets
(``ObjectType``, ``Aspect``) sont des tables simples pour cette maquette,
pas des ``Object``/``Version`` complets : éviter le problème d'amorçage
(un Type aurait besoin d'un Type pour se valider lui-même).
"""

import uuid

from django.conf import settings
from django.db import models
from pgvector.django import VectorField


class Space(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="spaces")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Layer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="layers")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="layers")
    role = models.CharField(max_length=100)
    shared = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.space.name}/{self.role}"


class ObjectType(models.Model):
    class Scope(models.TextChoices):
        BASE = "base", "base"
        SPACE = "space", "space"
        LAYER = "layer", "layer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    traits = models.ManyToManyField("self", blank=True, related_name="used_by", symmetrical=False)
    scope = models.CharField(max_length=10, choices=Scope.choices, default=Scope.BASE)
    space = models.ForeignKey(Space, null=True, blank=True, on_delete=models.CASCADE, related_name="types")
    layer = models.ForeignKey(Layer, null=True, blank=True, on_delete=models.CASCADE, related_name="types")
    schema = models.JSONField(default=dict)
    merge = models.JSONField(default=dict, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "scope", "space", "layer"],
                name="unique_object_type_name_per_scope",
            )
        ]

    def __str__(self):
        return self.name


class ViewTemplate(models.Model):
    """Gabarit de vue (lot 2) : une vue et son rendu, méta-objet comme ObjectType."""

    class Kind(models.TextChoices):
        STRUCTURED = "structured", "structured"
        NARRATIVE = "narrative", "narrative"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    applies_to = models.ForeignKey(ObjectType, on_delete=models.CASCADE, related_name="view_templates")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    renderer = models.CharField(max_length=100)
    editable = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Object(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="engine_objects")
    base_type = models.ForeignKey(ObjectType, on_delete=models.PROTECT, related_name="engine_objects")
    current_version = models.ForeignKey(
        "Version", null=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.base_type.name}:{self.id}"


class Version(models.Model):
    class Nature(models.TextChoices):
        HUMAN = "human", "human"
        AGENT = "agent", "agent"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField()
    attributes = models.JSONField(default=dict)
    sha256 = models.CharField(max_length=64)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="authored_versions"
    )
    agent_name = models.CharField(max_length=255, null=True, blank=True)
    nature = models.CharField(max_length=10, choices=Nature.choices)
    validated = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["object", "number"], name="unique_version_number_per_object"),
            models.CheckConstraint(
                condition=(
                    models.Q(nature="human", author__isnull=False, agent_name__isnull=True)
                    | models.Q(nature="agent", author__isnull=True, agent_name__isnull=False)
                ),
                name="version_author_xor_agent_name",
            ),
        ]
        ordering = ["object", "number"]

    def __str__(self):
        return f"{self.object_id}#{self.number}"


class Typing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name="typings")
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name="typings")
    type = models.ForeignKey(ObjectType, on_delete=models.PROTECT, related_name="typings")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["object", "layer", "type"], name="unique_typing"),
        ]

    def __str__(self):
        return f"{self.object_id}@{self.layer_id}:{self.type.name}"


class Proposal(models.Model):
    class Decision(models.TextChoices):
        PENDING = "pending", "pending"
        ACCEPTED = "accepted", "accepted"
        MODIFIED = "modified", "modified"
        REJECTED = "rejected", "rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation = models.CharField(max_length=100)
    input = models.JSONField(default=dict)
    output = models.JSONField(null=True, blank=True)
    model = models.CharField(max_length=255, null=True, blank=True)
    decision = models.CharField(max_length=10, choices=Decision.choices, default=Decision.PENDING)
    correction = models.JSONField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.operation}:{self.id}"


class Link(models.Model):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "proposed"
        ACTIVE = "active", "active"
        REJECTED = "rejected", "rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nature = models.CharField(max_length=100)
    source = models.ForeignKey(Object, on_delete=models.CASCADE, related_name="links_from")
    target = models.ForeignKey(Object, on_delete=models.CASCADE, related_name="links_to")
    layer = models.ForeignKey(Layer, null=True, blank=True, on_delete=models.CASCADE, related_name="links")
    version = models.ForeignKey(Version, null=True, blank=True, on_delete=models.SET_NULL, related_name="links")
    proposed_by = models.ForeignKey(Proposal, null=True, blank=True, on_delete=models.SET_NULL, related_name="links")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source_id} --{self.nature}--> {self.target_id}"


class Blob(models.Model):
    sha256 = models.CharField(max_length=64, primary_key=True)
    mime_type = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    path = models.CharField(max_length=1024)

    def __str__(self):
        return self.sha256


class Provenance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name="provenances")
    source_object = models.ForeignKey(
        Object, null=True, blank=True, on_delete=models.SET_NULL, related_name="provenances_as_source"
    )
    source_blob = models.ForeignKey(
        Blob, null=True, blank=True, on_delete=models.SET_NULL, related_name="provenances"
    )
    anchor = models.JSONField(null=True, blank=True)
    operation = models.CharField(max_length=100)

    def __str__(self):
        return f"provenance({self.version_id})"


class Aspect(models.Model):
    """Règle greffée. Déclarée au lot 1, exécutée au lot 3."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name="aspects")
    name = models.CharField(max_length=255)
    pointcut = models.JSONField(default=dict)
    action = models.JSONField(default=dict)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    object = models.ForeignKey(Object, on_delete=models.CASCADE, related_name="events")
    version = models.ForeignKey(Version, null=True, blank=True, on_delete=models.SET_NULL, related_name="events")
    nature = models.CharField(max_length=50)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="authored_events"
    )
    agent_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.nature}:{self.object_id}"


class Divergence(models.Model):
    """Écart signalé entre calques. Déclarée au lot 1, détectée au lot 3."""

    class Status(models.TextChoices):
        OPEN = "open", "open"
        RESOLVED = "resolved", "resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="divergences")
    # Nommé ``related_objects`` et non ``objects`` (le mot de la spec) : ce nom de
    # champ entre en collision avec le manager par défaut de Django et le rend
    # totalement inaccessible (``AttributeError: Manager isn't accessible via
    # Divergence instances``).
    related_objects = models.ManyToManyField(Object, related_name="divergences")
    layers = models.ManyToManyField(Layer, related_name="divergences")
    description = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"divergence({self.id}, {self.status})"


class Embedding(models.Model):
    """Recherche par le sens. Déclarée au lot 1, utilisée au lot 4."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(Version, on_delete=models.CASCADE, related_name="embeddings")
    model = models.CharField(max_length=255)
    vector = VectorField(dimensions=1024)

    def __str__(self):
        return f"embedding({self.version_id}, {self.model})"
