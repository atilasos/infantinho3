from __future__ import annotations

import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class DemoBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Execução Demo'
        verbose_name_plural = 'Execuções Demo'

    def __str__(self) -> str:  # pragma: no cover
        label = self.description or str(self.id)
        return f'Demo {label} @ {timezone.localtime(self.created_at):%Y-%m-%d %H:%M}'


class DemoRecord(models.Model):
    batch = models.ForeignKey(DemoBatch, related_name='records', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    label = models.CharField(max_length=120, blank=True)

    class Meta:
        unique_together = ('batch', 'content_type', 'object_id')
        ordering = ('-created_at',)
        verbose_name = 'Registo Demo'
        verbose_name_plural = 'Registos Demo'

    def __str__(self) -> str:  # pragma: no cover
        return f'{self.content_type}#{self.object_id} ({self.batch_id})'
