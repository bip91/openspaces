"""Journal attribué du noyau du bus (lot 3).

Distinct de ``engine.models.Event`` : ``Event`` journalise des événements
de domaine (création/mise à jour d'un objet). ``CallLog`` journalise des
appels au bus — y compris les lectures et les refus, qui ne produisent
aucun événement côté moteur.
"""

import uuid

from django.db import models


class CallLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verb = models.CharField(max_length=100)
    client_id = models.CharField(max_length=255)
    input = models.JSONField(default=dict)
    allowed = models.BooleanField()
    confirmed = models.BooleanField(default=False)
    output = models.JSONField(null=True, blank=True)
    error = models.CharField(max_length=255, null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.verb}@{self.client_id} ({'autorisé' if self.allowed else 'refusé'})"
