"""Reusable DRF serializer helpers."""
from rest_framework import serializers


class TimestampedSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True
